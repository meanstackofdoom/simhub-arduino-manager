from flask import Flask, render_template, request, redirect, jsonify
from datetime import datetime
from pathlib import Path
import json
import subprocess
import port_manager

app = Flask(__name__)

SIMHUB_EXE_NAMES = ["SimHubWPF.exe", "SimHub.exe"]
SIMHUB_PLUGIN_PATHS = [
    # Common plugin folder locations
    Path(r"C:\Program Files (x86)\SimHub\Plugins\ArduinoIdentifyPlugin.dll"),
    Path(r"C:\Program Files\SimHub\Plugins\ArduinoIdentifyPlugin.dll"),
    # Some setups drop the DLL directly next to SimHub.exe
    Path(r"C:\Program Files (x86)\SimHub\ArduinoIdentifyPlugin.dll"),
    Path(r"C:\Program Files\SimHub\ArduinoIdentifyPlugin.dll"),
]


def is_simhub_running() -> bool:
    """Best-effort check to see if a SimHub process is running (Windows-only)."""
    try:
        out = subprocess.check_output(["tasklist"], encoding="utf-8", errors="ignore")
    except Exception as e:
        print("[WARN] Unable to check SimHub process:", e)
        return False

    out = out.lower()
    return any(name.lower() in out for name in SIMHUB_EXE_NAMES)


def is_plugin_installed() -> bool:
    """Check common SimHub plugin locations for the ArduinoIdentify plugin DLL."""
    for p in SIMHUB_PLUGIN_PATHS:
        try:
            if p.exists():
                return True
        except Exception:
            continue
    return False


@app.route("/")
def index():
    devices = port_manager.scan_ports()
    # Sort by group then name for a bit more structure
    devices = sorted(devices, key=lambda d: (d.get("group", "") or "", d.get("name", "") or ""))

    # Profile list (files in ./profiles/*.json)
    profile_dir = Path("profiles")
    profiles = []
    if profile_dir.exists():
        profiles = [p.stem for p in profile_dir.glob("*.json")]

    stats = {
        "connected": sum(d["status"] == "connected" for d in devices),
        "missing": 0,
        "total": len(devices),
        "last_scan": datetime.now().strftime("%H:%M:%S"),
        # Live guardrails / environment checks
        "simhub_running": is_simhub_running(),
        "plugin_installed": is_plugin_installed(),
    }

    return render_template("index.html", devices=devices, stats=stats, profiles=profiles)

@app.route("/install/<path:key>", methods=["POST"])
def install(key):
    return ("OK", 200) if port_manager.install_device(key) else ("Error", 400)

@app.route("/bulk_install", methods=["POST"])
def bulk_install():
    count = port_manager.bulk_install()
    return jsonify({"message": f"Installed {count} devices", "count": count})

@app.route("/identify/<path:key>", methods=["POST"])
def identify(key):
    # Guardrails: require SimHub + plugin
    if not is_simhub_running():
        return jsonify({"error": "SimHub does not appear to be running. Start SimHub and try again."}), 400
    if not is_plugin_installed():
        return jsonify({"error": "Arduino Identify plugin not found. Check your SimHub Plugins folder."}), 400

    print(f"[IDENTIFY] Requested identify for {key}")
    port_manager.identify_device(key, mode="identify")
    return ("", 204)


@app.route("/test/<path:key>", methods=["POST"])
def test(key):
    # Guardrails: require SimHub + plugin
    if not is_simhub_running():
        return jsonify({"error": "SimHub does not appear to be running. Start SimHub and try again."}), 400
    if not is_plugin_installed():
        return jsonify({"error": "Arduino Identify plugin not found. Check your SimHub Plugins folder."}), 400

    print(f"[TEST] Requested test pattern for {key}")
    port_manager.identify_device(key, mode="test")
    return ("", 204)


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
    print(f"[PROFILE] Loaded profile '{name}'")
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=False)
