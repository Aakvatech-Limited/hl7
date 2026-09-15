from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import store

settings_bp = Blueprint("settings", __name__)


@settings_bp.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        store.save_settings(
            erpnext_url=request.form.get("erpnext_url", "").rstrip("/"),
            api_key=request.form.get("api_key", ""),
            api_secret=request.form.get("api_secret", ""),
            logs_directory=request.form.get("logs_directory", "logs"),
        )
        flash("Settings saved.", "success")
        return redirect(url_for("settings.index"))
    return render_template("settings.html", settings=store.get_settings())


@settings_bp.route("/test-connection", methods=["POST"])
def test_connection():
    settings = store.get_settings()
    from app.services.erpnext_service import ERPNextClient
    client = ERPNextClient(settings.erpnext_url, settings.api_key, settings.api_secret)
    result = client.test_connection()
    if result["success"]:
        flash(f"Connected successfully as: {result['user']}", "success")
    else:
        flash(f"Connection failed: {result['error']}", "danger")
    return redirect(url_for("settings.index"))
