from flask_socketio import SocketIO


socketio = SocketIO(cors_allowed_origins="*")


def emit_probe_result(payload: dict) -> None:
    socketio.emit("probe_result", payload, namespace="/monitor")


def emit_incident_event(payload: dict) -> None:
    socketio.emit("incident_event", payload, namespace="/monitor")
