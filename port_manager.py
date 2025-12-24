import pyautogui
import serial.tools.list_ports
import json
import re
from pathlib import Path
from datetime import datetime

# =========================
# Config
# =========================

CONFIG_FILE = Path(r"C:\Users\endfm\Desktop\ports\ports.json")

# =========================
# Load / Save
# =========================

def load_config():
    if not CONFIG_FILE.exists():
        return {}

    try:
        text = CONFIG_FILE.read_text().strip()
        if not text:
            return {}
        return json.loads(text)
    except Exception as e:
        print("[WARN] ports.json invalid, resetting:", e)
        return {}

saved = load_config()


def save_config():
    CONFIG_FILE.write_text(json.dumps(saved, indent=2))

# =========================
# Identify (Keyboard → SimHub)
# =========================

def identify_device(key, mode="identify"):
    """
    Trigger an identify or test pattern in SimHub via keyboard hotkeys.

    Configure in SimHub:
      - NumPad 9 → "Trigger Identify Blink"  (normal identify)
      - NumPad 0 → "Trigger Test Pattern"   (richer test pattern)
    """
    device_id = saved.get(key, {}).get("identify_id")

    if not isinstance(device_id, int):
        print("[IDENTIFY] Missing numeric identify_id")
        return

    if mode == "test":
        print(f"[AUTOMATION] TEST device ID {device_id}")
        # SimHub action for test pattern is bound to NumPad 0
        pyautogui.press("num0")
    else:
        print(f"[AUTOMATION] Identifying device ID {device_id}")
        # SimHub action for normal identify is bound to NumPad 9
        pyautogui.press("num9")
    
    
    import requests
from datetime import datetime

SIMHUB_ARDUINO_URL = "http://127.0.0.1:8888/api/arduino"

def fetch_simhub_devices():
    """
    Placeholder for future SimHub HTTP integration.
    Your current SimHub setup has no HTTP API enabled,
    so we simply return an empty list and avoid any errors.
    """
    return []

# =========================
# Install / Assign ID
# =========================

def install_device(key):
    if key not in saved:
        saved[key] = {
            "name": "New Device",
            "role": "Unassigned",
            "tags": [],
            "channel": 0,
            "group": "",
        }

    if "identify_id" not in saved[key]:
        used_ids = {
            d.get("identify_id")
            for d in saved.values()
            if isinstance(d.get("identify_id"), int)
        }

        new_id = 1
        while new_id in used_ids:
            new_id += 1

        saved[key]["identify_id"] = new_id
        print(f"[INSTALL] Assigned identify_id {new_id} to {key}")

    saved[key]["installed"] = True
    save_config()
    return True

def bulk_install():
    devices = scan_ports()
    count = 0
    for d in devices:
        if not d.get("installed") or not d.get("identify_id"):
            if install_device(d["key"]):
                count += 1
    return count

# =========================
# Scan USB Ports
# =========================

def _format_duration(delta_seconds: int) -> str:
    """Return a short human-friendly duration like '5s', '2m', '1h 3m', '2d 4h'."""
    if delta_seconds < 0:
        delta_seconds = 0
    if delta_seconds < 60:
        return f"{delta_seconds}s"
    minutes, seconds = divmod(delta_seconds, 60)
    if minutes < 60:
        return f"{minutes}m"
    hours, minutes = divmod(minutes, 60)
    if hours < 24:
        return f"{hours}h {minutes}m"
    days, hours = divmod(hours, 24)
    return f"{days}d {hours}h"


def scan_ports():
    results = []
    ports = list(serial.tools.list_ports.comports())
    now = datetime.utcnow()
    touched = False

    # SimHub integration is currently disabled (no HTTP API),
    # so we treat any detected COM port as "connected".
    for p in ports:
        key = make_device_key(p)
        entry = dict(saved.get(key, {}))

        # Ensure we have a stable "connected_since" timestamp per device
        connected_since = entry.get("connected_since")
        if not connected_since:
            connected_since = now.isoformat()
            entry["connected_since"] = connected_since
            saved[key] = entry
            touched = True

        # Derive a human readable "connected_for" duration
        connected_for = ""
        try:
            since_dt = datetime.fromisoformat(connected_since)
            delta = now - since_dt
            connected_for = _format_duration(int(delta.total_seconds()))
        except Exception:
            connected_for = ""

        # Hardware details from pyserial
        description = getattr(p, "description", "") or ""
        manufacturer = getattr(p, "manufacturer", "") or ""
        serial_number = getattr(p, "serial_number", "") or ""
        vid = getattr(p, "vid", None)
        pid = getattr(p, "pid", None)
        vid_hex = f"{vid:04X}" if isinstance(vid, int) else None
        pid_hex = f"{pid:04X}" if isinstance(pid, int) else None

        results.append({
            "key": key,
            "port": p.device,
            "name": entry.get("name", "New Device"),
            "role": entry.get("role", "Unassigned"),
            "channel": entry.get("channel", 0),
            "group": entry.get("group", ""),
            "identify_id": entry.get("identify_id"),
            "installed": entry.get("installed", False),
            "status": "connected",
            "description": description,
            "manufacturer": manufacturer,
            "serial_number": serial_number,
            "vid": vid_hex,
            "pid": pid_hex,
            "connected_for": connected_for,
            "simhub": None,
        })

    if touched:
        save_config()

    return results
    # =========================
# Key Function
# =========================
    import re

def make_device_key(port):
    """
    Generate a stable, canonical USB key.
    """
    vid = pid = sn = "UNKNOWN"

    if port.hwid:
        m = re.search(r"VID:PID=([0-9A-Fa-f]{4}):([0-9A-Fa-f]{4})", port.hwid)
        if m:
            vid, pid = m.groups()

        sn_match = re.search(r"SER=([^ ]+)", port.hwid)
        if sn_match:
            sn = sn_match.group(1)

    # Many CH340 clones ship without a real serial number; they all look identical.
    # In that case we suffix the COM port so each physical device gets its own key.
    if sn == "UNKNOWN":
        try:
            sn = f"NO-SN-{port.device}"
        except Exception:
            pass

    return f"USB:VID={vid}:PID={pid}:SN={sn}"

