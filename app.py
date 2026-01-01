from flask import Flask, render_template, request, redirect, jsonify
from datetime import datetime
from pathlib import Path
import json
import port_manager

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.auto_reload = True

# =========================
# Session Stats Tracking
# =========================
SESSION_START = datetime.now()
SESSION_STATS = {
    "devices_installed": 0,
    "profiles_loaded": 0,
    "profiles_saved": 0,
}


def get_session_uptime() -> str:
    """Return human-readable session uptime."""
    delta = datetime.now() - SESSION_START
    total_seconds = int(delta.total_seconds())
    
    if total_seconds < 60:
        return f"{total_seconds}s"
    minutes, seconds = divmod(total_seconds, 60)
    if minutes < 60:
        return f"{minutes}m {seconds}s"
    hours, minutes = divmod(minutes, 60)
    if hours < 24:
        return f"{hours}h {minutes}m"
    days, hours = divmod(hours, 24)
    return f"{days}d {hours}h"


@app.route("/")
def index():
    devices = port_manager.scan_ports()
    # Sort by group then name for better organization
    devices = sorted(devices, key=lambda d: (d.get("group", "") or "", d.get("name", "") or ""))

    # Profile list (files in ./profiles/*.json)
    profile_dir = Path("profiles")
    profiles = []
    if profile_dir.exists():
        profiles = [p.stem for p in profile_dir.glob("*.json")]

    # Get port analytics
    analytics = port_manager.get_port_analytics()
    
    # Get connection timeline
    timeline = port_manager.get_connection_timeline(20)

    stats = {
        "connected": sum(d["status"] == "connected" for d in devices),
        "total": len(devices),
        "last_scan": datetime.now().strftime("%H:%M:%S"),
        # Session stats
        "uptime": get_session_uptime(),
        "session_start": SESSION_START.strftime("%H:%M:%S"),
        "devices_installed": SESSION_STATS["devices_installed"],
        "profiles_loaded": SESSION_STATS["profiles_loaded"],
        "profiles_saved": SESSION_STATS["profiles_saved"],
        # Analytics
        "total_ports": analytics["total_ports"],
        "active_ports": analytics["active_ports"],
        "session_duration": analytics["session_duration"],
    }

    return render_template(
        "index.html",
        devices=devices,
        stats=stats,
        profiles=profiles,
        analytics=analytics,
        timeline=timeline,
    )


@app.route("/install/<path:key>", methods=["POST"])
def install(key):
    result = port_manager.install_device(key)
    if result:
        SESSION_STATS["devices_installed"] += 1
    return ("OK", 200) if result else ("Error", 400)


@app.route("/bulk_install", methods=["POST"])
def bulk_install():
    count = port_manager.bulk_install()
    return jsonify({"message": f"Installed {count} devices", "count": count})


@app.route("/update", methods=["POST"])
def update():
    key = request.form.get("key")

    if not key:
        print("[WARN] Update called with empty key – ignoring")
        return redirect("/")

    # Start from existing entry (if any) so we don't lose other fields
    current = dict(port_manager.saved.get(key, {}))

    # Name
    new_name = (request.form.get("name") or "").strip()
    if new_name:
        current["name"] = new_name

    # Tags (stored as list)
    raw_tags = request.form.get("tags", "")
    current["tags"] = [t.strip() for t in raw_tags.split(",") if t.strip()]

    # Role (always overwrite; default to "Unassigned" if empty)
    new_role = (request.form.get("role") or "").strip() or "Unassigned"
    current["role"] = new_role

    # Channel (optional, stored as int; default 0 = all)
    channel_val = (request.form.get("channel") or "").strip()
    if channel_val:
        try:
            current["channel"] = int(channel_val)
        except ValueError:
            pass

    # Group (optional free text)
    group_val = (request.form.get("group") or "").strip()
    if group_val:
        current["group"] = group_val

    # Notes (freeform text for wiring info, etc.)
    notes_val = (request.form.get("notes") or "").strip()
    current["notes"] = notes_val

    port_manager.saved[key] = current

    print(f"[UPDATE] Saved settings for {key}: {current}")
    port_manager.save_config()
    return redirect("/")


@app.route("/profile/save", methods=["POST"])
def save_profile():
    name = (request.form.get("name") or "").strip()
    if not name:
        return redirect("/")

    profile_dir = Path("profiles")
    profile_dir.mkdir(exist_ok=True)
    dest = profile_dir / f"{name}.json"

    # Dump current ports config as profile snapshot
    dest.write_text(json.dumps(port_manager.saved, indent=2))
    SESSION_STATS["profiles_saved"] += 1
    print(f"[PROFILE] Saved profile '{name}' to {dest}")
    return redirect("/")


@app.route("/profile/load", methods=["POST"])
def load_profile():
    name = (request.form.get("name") or "").strip()
    if not name:
        return redirect("/")

    profile_dir = Path("profiles")
    src = profile_dir / f"{name}.json"
    if not src.exists():
        print(f"[PROFILE] Missing profile '{name}'")
        return redirect("/")

    try:
        data = json.loads(src.read_text())
    except Exception as e:
        print(f"[PROFILE] Failed to load profile '{name}': {e}")
        return redirect("/")

    # Replace in-memory config and write back to ports.json
    port_manager.saved.clear()
    port_manager.saved.update(data)
    port_manager.save_config()
    SESSION_STATS["profiles_loaded"] += 1
    print(f"[PROFILE] Loaded profile '{name}'")
    return redirect("/")


# =========================
# Analytics & History API
# =========================

@app.route("/api/analytics")
def api_analytics():
    """Return port analytics data as JSON."""
    return jsonify(port_manager.get_port_analytics())


@app.route("/api/timeline")
def api_timeline():
    """Return connection timeline as JSON."""
    limit = request.args.get("limit", 100, type=int)
    return jsonify(port_manager.get_connection_timeline(limit))


@app.route("/api/device_history/<path:key>")
def api_device_history(key):
    """Get port history for a specific device."""
    return jsonify(port_manager.get_device_port_history(key))


@app.route("/api/port_stats")
def api_port_stats():
    """Return detailed port statistics."""
    return jsonify(port_manager._port_stats)


@app.route("/api/export_history")
def export_history():
    """Export device history as JSON."""
    history = port_manager.get_device_history(1000)
    return jsonify({
        "exported_at": datetime.now().isoformat(),
        "total_events": len(history),
        "events": history
    })


if __name__ == "__main__":
    app.run(debug=True)
