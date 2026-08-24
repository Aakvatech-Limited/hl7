from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from app import store
from app.services.hl7_listener import get_listener_status, reload_device, stop_device

devices_bp = Blueprint("devices", __name__)


def _get_device_or_404(device_id: int):
    device = store.get_device(device_id)
    if device is None:
        abort(404)
    return device


@devices_bp.route("/")
def index():
    return render_template("devices.html", devices=store.get_devices(), status=get_listener_status())


@devices_bp.route("/new", methods=["GET", "POST"])
def new():
    if request.method == "POST":
        try:
            device = store.add_device(
                name=request.form["name"],
                port=int(request.form.get("port", 5600)),
                is_active=bool(request.form.get("is_active")),
            )
        except ValueError as exc:
            flash(str(exc), "danger")
            return render_template("device_form.html", device=None)
        reload_device(device.id)
        flash(f'Device "{device.name}" added.', "success")
        return redirect(url_for("devices.index"))
    return render_template("device_form.html", device=None)


@devices_bp.route("/<int:device_id>/edit", methods=["GET", "POST"])
def edit(device_id):
    device = _get_device_or_404(device_id)
    if request.method == "POST":
        try:
            device = store.update_device(
                device_id,
                name=request.form["name"],
                port=int(request.form.get("port", 5600)),
                is_active=bool(request.form.get("is_active")),
            )
        except ValueError as exc:
            flash(str(exc), "danger")
            return render_template("device_form.html", device=_get_device_or_404(device_id))
        reload_device(device.id)
        flash(f'Device "{device.name}" updated.', "success")
        return redirect(url_for("devices.index"))
    return render_template("device_form.html", device=device)


@devices_bp.route("/<int:device_id>/delete", methods=["POST"])
def delete(device_id):
    device = _get_device_or_404(device_id)
    stop_device(device_id)
    store.delete_device(device_id)
    flash(f'Device "{device.name}" deleted.', "info")
    return redirect(url_for("devices.index"))


@devices_bp.route("/<int:device_id>/toggle", methods=["POST"])
def toggle(device_id):
    device = _get_device_or_404(device_id)
    device = store.update_device(device_id, is_active=not device.is_active)
    if device.is_active:
        reload_device(device_id)
        flash(f'Device "{device.name}" activated.', "success")
    else:
        stop_device(device_id)
        flash(f'Device "{device.name}" deactivated.', "info")
    return redirect(url_for("devices.index"))


@devices_bp.route("/<int:device_id>/logs")
def logs(device_id):
    device = _get_device_or_404(device_id)
    device_logs = store.get_logs(device_id=device_id, limit=50)
    return render_template("device_logs.html", device=device, logs=device_logs)
