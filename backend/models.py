from __future__ import annotations

from datetime import datetime

from sqlalchemy import Index, UniqueConstraint

from database import db


class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class Probe(db.Model, TimestampMixin):
    __tablename__ = "probes"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    host = db.Column(db.String(255), nullable=False, index=True)
    group = db.Column(db.String(120), nullable=False, default="Default")
    probe_interval = db.Column(db.Integer, nullable=False, default=5)
    latency_threshold = db.Column(db.Float, nullable=False, default=80)
    packet_loss_threshold = db.Column(db.Float, nullable=False, default=5)
    enabled = db.Column(db.Boolean, nullable=False, default=True)

    results = db.relationship("ProbeResult", backref="probe", lazy=True)
    incidents = db.relationship("Incident", backref="probe", lazy=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "host": self.host,
            "group": self.group,
            "probe_interval": self.probe_interval,
            "latency_threshold": self.latency_threshold,
            "packet_loss_threshold": self.packet_loss_threshold,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class ProbeSource(db.Model, TimestampMixin):
    __tablename__ = "probe_sources"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    enabled = db.Column(db.Boolean, nullable=False, default=True)

    assignments = db.relationship("ProbeSourceAssignment", backref="source", lazy=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class ProbeSourceAssignment(db.Model):
    __tablename__ = "probe_source_assignments"
    __table_args__ = (
        UniqueConstraint("probe_id", "source_id", name="uq_probe_source_assignment"),
    )

    id = db.Column(db.Integer, primary_key=True)
    probe_id = db.Column(db.Integer, db.ForeignKey("probes.id"), nullable=False)
    source_id = db.Column(db.Integer, db.ForeignKey("probe_sources.id"), nullable=False)

    probe = db.relationship("Probe", backref="source_assignments")


class ProbeResult(db.Model):
    __tablename__ = "probe_results"
    __table_args__ = (
        Index("idx_probe_results_probe_source_checked", "probe_id", "source", "checked_at"),
    )

    id = db.Column(db.Integer, primary_key=True)
    probe_id = db.Column(db.Integer, db.ForeignKey("probes.id"), nullable=False, index=True)
    source = db.Column(db.String(120), nullable=False, default="default")
    latency_min = db.Column(db.Float, nullable=True)
    latency_avg = db.Column(db.Float, nullable=True)
    latency_max = db.Column(db.Float, nullable=True)
    jitter = db.Column(db.Float, nullable=True)
    packet_loss = db.Column(db.Float, nullable=False, default=0)
    status = db.Column(db.String(30), nullable=False, index=True)
    raw_latencies = db.Column(db.Text, nullable=True)
    checked_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "probe_id": self.probe_id,
            "source": self.source,
            "latency_min": self.latency_min,
            "latency_avg": self.latency_avg,
            "latency_max": self.latency_max,
            "jitter": self.jitter,
            "packet_loss": self.packet_loss,
            "status": self.status,
            "checked_at": self.checked_at.isoformat(),
        }


class Incident(db.Model):
    __tablename__ = "incidents"
    __table_args__ = (Index("idx_incidents_probe_source_status", "probe_id", "source", "status"),)

    id = db.Column(db.Integer, primary_key=True)
    probe_id = db.Column(db.Integer, db.ForeignKey("probes.id"), nullable=False, index=True)
    source = db.Column(db.String(120), nullable=False, default="default")
    issue_type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="ACTIVE", index=True)
    details = db.Column(db.Text, nullable=True)
    started_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    resolved_at = db.Column(db.DateTime, nullable=True)
    last_notification_at = db.Column(db.DateTime, nullable=True)

    traces = db.relationship("TraceReport", backref="incident", lazy=True)
    telegram_logs = db.relationship("TelegramDeliveryLog", backref="incident", lazy=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "probe_id": self.probe_id,
            "source": self.source,
            "issue_type": self.issue_type,
            "status": self.status,
            "details": self.details,
            "started_at": self.started_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }


class TraceReport(db.Model):
    __tablename__ = "trace_reports"

    id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.Integer, db.ForeignKey("incidents.id"), nullable=False)
    probe_id = db.Column(db.Integer, db.ForeignKey("probes.id"), nullable=False)
    source = db.Column(db.String(120), nullable=False, default="default")
    target = db.Column(db.String(255), nullable=False)
    summary = db.Column(db.String(255), nullable=True)
    raw_output = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    probe = db.relationship("Probe")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "incident_id": self.incident_id,
            "probe_id": self.probe_id,
            "source": self.source,
            "target": self.target,
            "summary": self.summary,
            "created_at": self.created_at.isoformat(),
        }


class TelegramDeliveryLog(db.Model):
    __tablename__ = "telegram_delivery_logs"

    id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.Integer, db.ForeignKey("incidents.id"), nullable=True)
    message_type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    response = db.Column(db.Text, nullable=True)
    error = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class AppSetting(db.Model, TimestampMixin):
    __tablename__ = "app_settings"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(120), nullable=False, unique=True, index=True)
    value = db.Column(db.String(255), nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "key": self.key,
            "value": self.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
