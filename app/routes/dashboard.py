from flask import Blueprint, render_template
from app import store
from app.services.hl7_listener import get_listener_status

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
def index():
    devices = store.get_devices()
    recent_logs = store.get_logs(limit=20)
    counts = store.log_counts()
    status = get_listener_status()

    stats = {
        "total_devices": len(devices),
        "active_devices": sum(1 for d in devices if d.is_active),
        "listening_devices": sum(1 for s in status.values() if s["running"]),
        "total_messages": counts["total"],
        "failed_messages": counts["failed"],
    }

    return render_template(
        "dashboard.html",
        devices=devices,
        status=status,
        recent_logs=recent_logs,
        settings=store.get_settings(),
        stats=stats,
    )
