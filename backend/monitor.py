from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from flask import current_app
from ping3 import ping

from config import settings
from database import db
from models import (
    AppSetting,
    Incident,
    Probe,
    ProbeResult,
    ProbeSource,
    ProbeSourceAssignment,
    TraceReport,
)
from telegram import TelegramNotifier
from traceroute import TraceRunner
from websocket import emit_incident_event, emit_probe_result


@dataclass
class ThresholdState:
    latency_breaches: int = 0
    packet_loss_breaches: int = 0
    down_breaches: int = 0
    latency_ema: Optional[float] = None


class MonitorService:
    _TRACE_MAX_LINES = 14
    _TRACE_MAX_CHARS = 3000
    _LATENCY_EMA_ALPHA = 0.25

    def __init__(self) -> None:
        self._state: Dict[Tuple[int, str], ThresholdState] = {}
        self._notifier = TelegramNotifier()
        self._tracer = TraceRunner()

    def run_cycle(self) -> None:
        probes = Probe.query.filter_by(enabled=True).all()
        for probe in probes:
            sources = self._sources_for_probe(probe.id)
            if not sources:
                sources = ["default"]

            for source_name in sources:
                self._run_probe_for_source(probe, source_name)

    def _sources_for_probe(self, probe_id: int) -> List[str]:
        assignments = (
            db.session.query(ProbeSourceAssignment, ProbeSource)
            .join(ProbeSource, ProbeSource.id == ProbeSourceAssignment.source_id)
            .filter(
                ProbeSourceAssignment.probe_id == probe_id,
                ProbeSource.enabled.is_(True),
            )
            .all()
        )
        return [source.name for _, source in assignments]

    def _run_probe_for_source(self, probe: Probe, source: str) -> None:
        latencies = self._ping_batch(probe.host, settings.ping_count)
        metrics = self._calculate_metrics(latencies)
        status = self._determine_status(
            latency_reference=metrics["latency_median"],
            packet_loss=metrics["packet_loss"],
            latency_threshold=probe.latency_threshold,
            packet_loss_threshold=probe.packet_loss_threshold,
        )

        result = ProbeResult(
            probe_id=probe.id,
            source=source,
            latency_min=metrics["latency_min"],
            latency_avg=metrics["latency_avg"],
            latency_max=metrics["latency_max"],
            jitter=metrics["jitter"],
            packet_loss=metrics["packet_loss"],
            status=status,
            raw_latencies=",".join(str(value) for value in latencies if value is not None),
        )
        db.session.add(result)
        db.session.commit()

        emit_probe_result(
            {
                "probe_id": probe.id,
                "probe_name": probe.name,
                "host": probe.host,
                "source": source,
                "status": status,
                "latency_avg": result.latency_avg,
                "latency_max": result.latency_max,
                "packet_loss": result.packet_loss,
                "jitter": result.jitter,
                "checked_at": result.checked_at.isoformat(),
            }
        )
        self._evaluate_incident(probe, source, result)

    def _ping_batch(self, host: str, count: int) -> List[Optional[float]]:
        latencies_ms: List[Optional[float]] = []
        for _ in range(count):
            response_time = ping(host, timeout=settings.ping_timeout_seconds, unit="ms")
            latencies_ms.append(response_time if response_time is not None else None)
        return latencies_ms

    @staticmethod
    def _calculate_metrics(latencies: List[Optional[float]]) -> dict:
        numeric_latencies = [value for value in latencies if value is not None]
        sent = len(latencies)
        received = len(numeric_latencies)
        packet_loss = 100.0 if sent == 0 else round(((sent - received) / sent) * 100, 2)

        if not numeric_latencies:
            return {
                "latency_min": None,
                "latency_avg": None,
                "latency_max": None,
                "jitter": None,
                "packet_loss": packet_loss,
            }

        jitter = 0.0
        if len(numeric_latencies) > 1:
            jitter = statistics.pstdev(numeric_latencies)

        sorted_latencies = sorted(numeric_latencies)
        latency_median = statistics.median(sorted_latencies)
        filtered_latencies = MonitorService._remove_latency_outliers(sorted_latencies)
        latency_avg = sum(filtered_latencies) / len(filtered_latencies)

        return {
            "latency_min": round(min(numeric_latencies), 2),
            "latency_avg": round(latency_avg, 2),
            "latency_max": round(max(numeric_latencies), 2),
            "latency_median": round(latency_median, 2),
            "jitter": round(jitter, 2),
            "packet_loss": packet_loss,
        }

    @staticmethod
    def _remove_latency_outliers(sorted_latencies: List[float]) -> List[float]:
        if len(sorted_latencies) < 5:
            return sorted_latencies

        midpoint = len(sorted_latencies) // 2
        lower_half = sorted_latencies[:midpoint]
        upper_half = sorted_latencies[midpoint + (0 if len(sorted_latencies) % 2 == 0 else 1) :]
        if not lower_half or not upper_half:
            return sorted_latencies

        q1 = statistics.median(lower_half)
        q3 = statistics.median(upper_half)
        iqr = max(0.0, q3 - q1)
        upper_fence = q3 + (1.5 * iqr)
        lower_fence = max(0.0, q1 - (1.5 * iqr))

        filtered = [
            value
            for value in sorted_latencies
            if lower_fence <= value <= upper_fence
        ]
        return filtered or sorted_latencies

    @staticmethod
    def _determine_status(
        latency_reference: Optional[float],
        packet_loss: float,
        latency_threshold: float,
        packet_loss_threshold: float,
    ) -> str:
        if packet_loss >= 100:
            return "DOWN"
        if packet_loss > packet_loss_threshold:
            return "DEGRADED"
        if latency_reference is not None and latency_reference > latency_threshold:
            return "DEGRADED"
        return "UP"

    def _evaluate_incident(self, probe: Probe, source: str, result: ProbeResult) -> None:
        issue_type = self._determine_issue_type(probe, source, result)
        incident = (
            Incident.query.filter_by(probe_id=probe.id, source=source, status="ACTIVE")
            .order_by(Incident.started_at.desc())
            .first()
        )

        if issue_type is None:
            if incident:
                self._resolve_incident(incident, probe, source)
            return

        if incident and incident.issue_type == issue_type:
            self._send_incident_reminder_if_due(incident, probe, source, result)
            return

        if incident and incident.issue_type != issue_type:
            self._resolve_incident(incident, probe, source)

        new_incident = Incident(
            probe_id=probe.id,
            source=source,
            issue_type=issue_type,
            status="ACTIVE",
            details=(
                f"latency_avg={result.latency_avg}, latency_max={result.latency_max}, "
                f"packet_loss={result.packet_loss}, jitter={result.jitter}"
            ),
        )
        db.session.add(new_incident)
        db.session.commit()

        trace = self._tracer.run_incident_trace(probe.host)
        db.session.add(
            TraceReport(
                incident_id=new_incident.id,
                probe_id=probe.id,
                source=source,
                target=probe.host,
                summary=trace.summary,
                raw_output=trace.output,
            )
        )
        db.session.commit()

        self._notify_with_cooldown(new_incident, probe, source, result, is_recovery=False)
        self._send_trace_report_message(new_incident, probe, source, trace.summary, trace.output)
        emit_incident_event({"event": "CREATED", "incident": new_incident.to_dict()})

    def _determine_issue_type(
        self, probe: Probe, source: str, result: ProbeResult
    ) -> Optional[str]:
        key = (probe.id, source)
        state = self._state.setdefault(key, ThresholdState())
        consecutive_needed = self._required_consecutive_breaches(probe.probe_interval)

        if result.packet_loss >= 100:
            state.down_breaches += 1
            state.latency_breaches = 0
            state.packet_loss_breaches = 0
            if state.down_breaches >= 1:
                return "DOWN"
            return None

        state.down_breaches = 0

        latency_reference = self._extract_latency_reference(result)
        smoothed_latency = self._smooth_latency_reference(state, latency_reference)
        if smoothed_latency is not None and smoothed_latency > probe.latency_threshold:
            state.latency_breaches += 1
        else:
            state.latency_breaches = 0

        if result.packet_loss > probe.packet_loss_threshold:
            state.packet_loss_breaches += 1
        else:
            state.packet_loss_breaches = 0

        if state.latency_breaches >= consecutive_needed:
            return "HIGH_LATENCY"
        if state.packet_loss_breaches >= consecutive_needed:
            return "PACKET_LOSS"
        return None

    @staticmethod
    def _required_consecutive_breaches(probe_interval_seconds: int) -> int:
        safe_interval = max(1, int(probe_interval_seconds))
        persist_seconds = MonitorService._get_degraded_persist_seconds()
        return max(1, math.ceil(persist_seconds / safe_interval))

    @staticmethod
    def _get_degraded_persist_seconds() -> int:
        setting = AppSetting.query.filter_by(key="degraded_alert_persist_seconds").first()
        if not setting:
            return settings.degraded_alert_persist_seconds
        try:
            parsed = int(setting.value)
            return max(10, min(parsed, 24 * 60 * 60))
        except (TypeError, ValueError):
            return settings.degraded_alert_persist_seconds

    def _smooth_latency_reference(
        self, state: ThresholdState, latency_reference: Optional[float]
    ) -> Optional[float]:
        if latency_reference is None:
            return state.latency_ema

        if state.latency_ema is None:
            state.latency_ema = latency_reference
            return state.latency_ema

        alpha = self._LATENCY_EMA_ALPHA
        state.latency_ema = (alpha * latency_reference) + ((1 - alpha) * state.latency_ema)
        return state.latency_ema

    @staticmethod
    def _get_incident_reminder_minutes() -> int:
        setting = AppSetting.query.filter_by(key="incident_reminder_minutes").first()
        if not setting:
            return settings.incident_reminder_minutes

        try:
            parsed = int(setting.value)
            return max(0, min(parsed, 24 * 60))
        except (TypeError, ValueError):
            return settings.incident_reminder_minutes

    @staticmethod
    def _extract_latency_reference(result: ProbeResult) -> Optional[float]:
        # Use median of raw ping samples for incident decisions to reduce
        # sensitivity to single-sample spikes.
        if not result.raw_latencies:
            return result.latency_avg
        try:
            values = [
                float(value)
                for value in result.raw_latencies.split(",")
                if value is not None and value != ""
            ]
            if not values:
                return result.latency_avg
            return statistics.median(values)
        except (TypeError, ValueError):
            return result.latency_avg

    def _resolve_incident(self, incident: Incident, probe: Probe, source: str) -> None:
        incident.status = "RESOLVED"
        incident.resolved_at = datetime.utcnow()
        db.session.commit()

        recovery_message = (
            "✅ INCIDENT RECOVERED\n\n"
            f"Target: {probe.name}\n"
            f"Host: {probe.host}\n"
            f"Source: {source}\n"
            f"Recovered at: {incident.resolved_at.isoformat()} UTC"
        )
        self._notifier.send_message(
            recovery_message, message_type="RECOVERY", incident_id=incident.id
        )
        emit_incident_event({"event": "RESOLVED", "incident": incident.to_dict()})

    def _notify_with_cooldown(
        self,
        incident: Incident,
        probe: Probe,
        source: str,
        result: ProbeResult,
        is_recovery: bool,
    ) -> None:
        if is_recovery:
            return

        now = datetime.utcnow()
        if incident.last_notification_at and now - incident.last_notification_at < timedelta(
            seconds=settings.incident_alert_cooldown_seconds
        ):
            return

        message = (
            "🚨 INCIDENT DETECTED\n\n"
            f"Target: {probe.name}\n"
            f"IP/Host: {probe.host}\n"
            f"Group: {probe.group}\n"
            f"Source: {source}\n\n"
            f"Status: {incident.issue_type}\n"
            f"Average latency: {result.latency_avg} ms\n"
            f"Maximum latency: {result.latency_max} ms\n"
            f"Packet loss: {result.packet_loss}%\n"
            f"Jitter: {result.jitter} ms"
        )
        self._notifier.send_message(message, message_type="INCIDENT", incident_id=incident.id)
        incident.last_notification_at = now
        db.session.commit()

    def _send_trace_report_message(
        self,
        incident: Incident,
        probe: Probe,
        source: str,
        trace_summary: str,
        trace_output: str,
    ) -> None:
        lines = [line.strip() for line in trace_output.splitlines() if line.strip()]
        if not lines:
            lines = ["No trace output captured."]

        # Keep the Telegram message compact and readable on phones.
        snippet_lines = lines[: self._TRACE_MAX_LINES]
        snippet = "\n".join(snippet_lines)
        if len(lines) > self._TRACE_MAX_LINES:
            snippet += "\n... (truncated)"
        snippet = snippet[: self._TRACE_MAX_CHARS]

        message = (
            "📡 TRACE REPORT\n\n"
            f"Target: {probe.name} ({probe.host})\n"
            f"Source: {source}\n"
            f"Incident: {incident.issue_type}\n"
            f"Summary: {trace_summary}\n\n"
            f"{snippet}"
        )
        self._notifier.send_message(
            message, message_type="TRACE_REPORT", incident_id=incident.id
        )

    def _send_incident_reminder_if_due(
        self,
        incident: Incident,
        probe: Probe,
        source: str,
        result: ProbeResult,
    ) -> None:
        reminder_minutes = self._get_incident_reminder_minutes()
        if reminder_minutes <= 0:
            return

        now = datetime.utcnow()
        if incident.last_notification_at and now - incident.last_notification_at < timedelta(
            minutes=reminder_minutes
        ):
            return

        reminder_message = (
            "🔔 INCIDENT REMINDER\n\n"
            f"Target: {probe.name}\n"
            f"IP/Host: {probe.host}\n"
            f"Group: {probe.group}\n"
            f"Source: {source}\n\n"
            f"Status: {incident.issue_type}\n"
            f"Still ongoing since: {incident.started_at.isoformat()} UTC\n"
            f"Current average latency: {result.latency_avg} ms\n"
            f"Current maximum latency: {result.latency_max} ms\n"
            f"Current packet loss: {result.packet_loss}%\n"
            f"Current jitter: {result.jitter} ms"
        )
        self._notifier.send_message(
            reminder_message, message_type="INCIDENT_REMINDER", incident_id=incident.id
        )
        incident.last_notification_at = now
        db.session.commit()

    def run_cycle_safe(self) -> None:
        try:
            self.run_cycle()
        except Exception:
            current_app.logger.exception("Monitor cycle failed.")
