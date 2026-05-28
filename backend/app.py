from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, jsonify, request
from flask_cors import CORS

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
from monitor import MonitorService
from websocket import socketio


monitor_service = MonitorService()
scheduler = BackgroundScheduler(timezone="UTC")


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = settings.database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = settings.secret_key

    CORS(app)
    db.init_app(app)
    socketio.init_app(app)

    register_routes(app)

    with app.app_context():
        db.create_all()
        _seed_default_source()

    _ensure_scheduler_started(app)

    return app


def register_routes(app: Flask) -> None:
    @app.get("/api/health")
    def health() -> Any:
        return jsonify({"status": "ok", "service": settings.app_name})

    @app.post("/api/monitor/run-once")
    def run_monitor_once() -> Any:
        monitor_service.run_cycle_safe()
        return jsonify({"status": "ok"})

    @app.get("/api/probes")
    def list_probes() -> Any:
        probes = Probe.query.order_by(Probe.created_at.desc()).all()
        return jsonify([probe.to_dict() for probe in probes])

    @app.post("/api/probes")
    def create_probe() -> Any:
        payload = request.get_json(silent=True) or {}
        required_fields = ["name", "host"]
        missing = [field for field in required_fields if not payload.get(field)]
        if missing:
            return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

        probe = Probe(
            name=payload["name"].strip(),
            host=payload["host"].strip(),
            group=payload.get("group", "Default").strip(),
            probe_interval=int(payload.get("probe_interval", 5)),
            latency_threshold=float(payload.get("latency_threshold", 80)),
            packet_loss_threshold=float(payload.get("packet_loss_threshold", 5)),
            enabled=bool(payload.get("enabled", True)),
        )
        db.session.add(probe)
        db.session.commit()
        return jsonify(probe.to_dict()), 201

    @app.get("/api/probes/<int:probe_id>")
    def get_probe(probe_id: int) -> Any:
        probe = Probe.query.get_or_404(probe_id)
        return jsonify(probe.to_dict())

    @app.put("/api/probes/<int:probe_id>")
    def update_probe(probe_id: int) -> Any:
        probe = Probe.query.get_or_404(probe_id)
        payload = request.get_json(silent=True) or {}

        for field in [
            "name",
            "host",
            "group",
            "probe_interval",
            "latency_threshold",
            "packet_loss_threshold",
            "enabled",
        ]:
            if field in payload:
                setattr(probe, field, payload[field])

        db.session.commit()
        return jsonify(probe.to_dict())

    @app.delete("/api/probes/<int:probe_id>")
    def delete_probe(probe_id: int) -> Any:
        probe = Probe.query.get_or_404(probe_id)
        db.session.delete(probe)
        db.session.commit()
        return jsonify({"status": "deleted"})

    @app.get("/api/sources")
    def list_sources() -> Any:
        sources = ProbeSource.query.order_by(ProbeSource.created_at.desc()).all()
        return jsonify([source.to_dict() for source in sources])

    @app.post("/api/sources")
    def create_source() -> Any:
        payload = request.get_json(silent=True) or {}
        name = (payload.get("name") or "").strip()
        if not name:
            return jsonify({"error": "name is required"}), 400

        source = ProbeSource(name=name, enabled=bool(payload.get("enabled", True)))
        db.session.add(source)
        db.session.commit()
        return jsonify(source.to_dict()), 201

    @app.post("/api/probes/<int:probe_id>/sources/<int:source_id>")
    def assign_source(probe_id: int, source_id: int) -> Any:
        Probe.query.get_or_404(probe_id)
        ProbeSource.query.get_or_404(source_id)

        exists = ProbeSourceAssignment.query.filter_by(
            probe_id=probe_id, source_id=source_id
        ).first()
        if exists:
            return jsonify({"status": "already_assigned"}), 200

        assignment = ProbeSourceAssignment(probe_id=probe_id, source_id=source_id)
        db.session.add(assignment)
        db.session.commit()
        return jsonify({"status": "assigned"}), 201

    @app.get("/api/results/recent")
    def recent_results() -> Any:
        probe_id = request.args.get("probe_id", type=int)
        source = request.args.get("source", type=str)
        limit = request.args.get("limit", type=int, default=100)

        query = ProbeResult.query.order_by(ProbeResult.checked_at.desc())
        if probe_id:
            query = query.filter(ProbeResult.probe_id == probe_id)
        if source:
            query = query.filter(ProbeResult.source == source)

        results = query.limit(max(1, min(limit, 500))).all()
        return jsonify([item.to_dict() for item in results])

    @app.get("/api/probes/<int:probe_id>/history")
    def probe_history(probe_id: int) -> Any:
        source = request.args.get("source", default="default", type=str)
        minutes = request.args.get("minutes", type=int)
        if minutes is None:
            hours = request.args.get("hours", default=24, type=int)
            minutes = hours * 60
        minutes = max(5, min(minutes, 24 * 60 * 31))
        since = datetime.utcnow() - timedelta(minutes=minutes)

        results = (
            ProbeResult.query.filter(
                ProbeResult.probe_id == probe_id,
                ProbeResult.source == source,
                ProbeResult.checked_at >= since,
            )
            .order_by(ProbeResult.checked_at.asc())
            .all()
        )
        return jsonify([item.to_dict() for item in results])

    @app.get("/api/incidents")
    def list_incidents() -> Any:
        status = request.args.get("status", type=str)
        limit = request.args.get("limit", default=100, type=int)

        query = Incident.query.order_by(Incident.started_at.desc())
        if status:
            query = query.filter(Incident.status == status.upper())

        incidents = query.limit(max(1, min(limit, 500))).all()
        return jsonify([item.to_dict() for item in incidents])

    @app.get("/api/incidents/<int:incident_id>/traces")
    def list_incident_traces(incident_id: int) -> Any:
        Incident.query.get_or_404(incident_id)
        traces = (
            TraceReport.query.filter_by(incident_id=incident_id)
            .order_by(TraceReport.created_at.desc())
            .all()
        )
        return jsonify([trace.to_dict() for trace in traces])

    @app.get("/api/dashboard/kpis")
    def dashboard_kpis() -> Any:
        probes = Probe.query.count()

        latest_results = _latest_results_by_probe_source()
        down = sum(1 for item in latest_results if item["status"] == "DOWN")
        degraded = sum(1 for item in latest_results if item["status"] == "DEGRADED")
        active_incidents = Incident.query.filter_by(status="ACTIVE").count()

        latency_values = [item["latency_avg"] for item in latest_results if item["latency_avg"]]
        packet_loss_values = [item["packet_loss"] for item in latest_results]

        avg_latency = round(sum(latency_values) / len(latency_values), 2) if latency_values else 0
        avg_packet_loss = (
            round(sum(packet_loss_values) / len(packet_loss_values), 2)
            if packet_loss_values
            else 0
        )

        return jsonify(
            {
                "total_probes": probes,
                "active_incidents": active_incidents,
                "targets_down": down,
                "targets_degraded": degraded,
                "average_latency": avg_latency,
                "average_packet_loss": avg_packet_loss,
            }
        )

    @app.get("/api/settings/alerts")
    def get_alert_settings() -> Any:
        persist_seconds = _get_setting_int(
            "degraded_alert_persist_seconds",
            settings.degraded_alert_persist_seconds,
            min_value=10,
            max_value=24 * 60 * 60,
        )
        return jsonify({"degraded_alert_persist_seconds": persist_seconds})

    @app.put("/api/settings/alerts")
    def update_alert_settings() -> Any:
        payload = request.get_json(silent=True) or {}
        if "degraded_alert_persist_seconds" not in payload:
            return jsonify({"error": "degraded_alert_persist_seconds is required"}), 400

        try:
            persist_seconds = int(payload["degraded_alert_persist_seconds"])
        except (TypeError, ValueError):
            return jsonify({"error": "degraded_alert_persist_seconds must be an integer"}), 400

        persist_seconds = max(10, min(persist_seconds, 24 * 60 * 60))
        _upsert_setting("degraded_alert_persist_seconds", str(persist_seconds))
        return jsonify({"degraded_alert_persist_seconds": persist_seconds})


def _latest_results_by_probe_source() -> List[Dict[str, Any]]:
    rows = (
        db.session.query(ProbeResult)
        .order_by(ProbeResult.probe_id, ProbeResult.source, ProbeResult.checked_at.desc())
        .all()
    )
    latest_by_key: Dict[str, ProbeResult] = {}
    for row in rows:
        key = f"{row.probe_id}:{row.source}"
        if key not in latest_by_key:
            latest_by_key[key] = row

    return [item.to_dict() for item in latest_by_key.values()]


def _seed_default_source() -> None:
    existing = ProbeSource.query.filter_by(name="default").first()
    if not existing:
        db.session.add(ProbeSource(name="default", enabled=True))
        db.session.commit()


def _get_setting_int(key: str, default: int, min_value: int, max_value: int) -> int:
    setting = AppSetting.query.filter_by(key=key).first()
    if not setting:
        return default
    try:
        parsed = int(setting.value)
        return max(min_value, min(parsed, max_value))
    except (TypeError, ValueError):
        return default


def _upsert_setting(key: str, value: str) -> None:
    setting = AppSetting.query.filter_by(key=key).first()
    if setting:
        setting.value = value
    else:
        db.session.add(AppSetting(key=key, value=value))
    db.session.commit()


def _ensure_scheduler_started(app: Flask) -> None:
    if scheduler.running:
        return

    scheduler.add_job(
        func=lambda: _run_monitor_job(app),
        trigger="interval",
        seconds=max(2, settings.monitor_tick_seconds),
        id="monitor-cycle",
        replace_existing=True,
        max_instances=1,
    )
    scheduler.start()


def _run_monitor_job(app: Flask) -> None:
    with app.app_context():
        monitor_service.run_cycle_safe()


app = create_app()


if __name__ == "__main__":
    socketio.run(
        app,
        host="0.0.0.0",
        port=settings.app_port,
        debug=False,
        allow_unsafe_werkzeug=True,
    )
