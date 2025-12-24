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

# SimHub config paths
SIMHUB_CONFIG_PATH = Path(r"C:\Program Files (x86)\SimHub\PluginsData\Common\SerialDashPlugin.json")
SIMHUB_RGB_LEDS_PATH = Path(r"C:\Program Files (x86)\SimHub\PluginsData\Common\ArduinoRGBLedsSettings.json")
SIMHUB_RGB_MATRIX_PATH = Path(r"C:\Program Files (x86)\SimHub\PluginsData\Common\ArduinoRGBMatrixSettings.json")

# Cached data
_simhub_port_lists: dict = {"whitelist": [], "blacklist": []}
_simhub_active_profiles: dict = {}

# =========================
# SimHub Config Reader
# =========================

def load_simhub_port_lists() -> dict:
    """Load COM port whitelist and blacklist from SimHub config."""
    global _simhub_port_lists
    if not SIMHUB_CONFIG_PATH.exists():
        return {"whitelist": [], "blacklist": []}
    
    try:
        data = json.loads(SIMHUB_CONFIG_PATH.read_text(encoding="utf-8"))
        _simhub_port_lists = {
            "whitelist": data.get("WhiteList", []),
            "blacklist": data.get("BlackList", []),
        }
        return _simhub_port_lists
    except Exception as e:
        print(f"[SIMHUB] Failed to load port lists: {e}")
        return {"whitelist": [], "blacklist": []}


def load_simhub_profiles() -> dict:
    """Load active LED profiles from SimHub config files."""
    global _simhub_active_profiles
    profiles = {}
    
    # RGB LEDs profile
    if SIMHUB_RGB_LEDS_PATH.exists():
        try:
            data = json.loads(SIMHUB_RGB_LEDS_PATH.read_text(encoding="utf-8"))
            active_id = data.get("activeProfileId", "")
            for p in data.get("Profiles", []):
                if p.get("ProfileId") == active_id:
                    profiles["rgb_leds"] = {
                        "name": p.get("Name", "Unknown"),
                        "id": active_id,
                        "brightness": p.get("GlobalBrightness", 100),
                    }
                    break
        except Exception as e:
            print(f"[SIMHUB] Failed to load RGB LEDs profiles: {e}")
    
    # RGB Matrix profile
    if SIMHUB_RGB_MATRIX_PATH.exists():
        try:
            data = json.loads(SIMHUB_RGB_MATRIX_PATH.read_text(encoding="utf-8"))
            active_id = data.get("activeProfileId", "")
            for p in data.get("Profiles", []):
                if p.get("ProfileId") == active_id:
                    profiles["rgb_matrix"] = {
                        "name": p.get("Name", "Unknown"),
                        "id": active_id,
                        "brightness": data.get("GlobalBrightness", 100),
                    }
                    break
        except Exception as e:
            print(f"[SIMHUB] Failed to load RGB Matrix profiles: {e}")
    
    _simhub_active_profiles = profiles
    return profiles


def get_port_status(port_name: str) -> str:
    """Return 'whitelisted', 'blacklisted', or 'unlisted' for a COM port."""
    global _simhub_port_lists
    if port_name in _simhub_port_lists.get("blacklist", []):
        return "blacklisted"
    if port_name in _simhub_port_lists.get("whitelist", []):
        return "whitelisted"
    return "unlisted"


def get_active_profiles() -> dict:
    """Return cached active profiles."""
    global _simhub_active_profiles
    return _simhub_active_profiles


def load_simhub_devices() -> dict:
    """
    Read SimHub's SerialDashPlugin.json and return a dict keyed by deviceUniqueId.
    Each entry contains the SimHub metadata (RgbLeds, displayModules, Motors, etc.).
    """
    if not SIMHUB_CONFIG_PATH.exists():
        print(f"[SIMHUB] Config not found at {SIMHUB_CONFIG_PATH}")
        return {}

    try:
        data = json.loads(SIMHUB_CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[SIMHUB] Failed to parse config: {e}")
        return {}

    result = {}
    devices = data.get("MultipleArduinoSettings", [])
    
    for dev in devices:
        uid = dev.get("deviceUniqueId")
        if uid:
            result[uid] = {
                "simhub_name": dev.get("deviceName", ""),
                "simhub_uid": uid,
                "rgb_leds": dev.get("RgbLeds", 0),
                "display_modules": dev.get("displayModules", 0),
                "motors": dev.get("Motors", 0),
                "read_buttons": dev.get("readButtons", False),
                "disabled": dev.get("disabled", False),
                "speed_level": dev.get("speedLevel", 0),
                "rotation": dev.get("Rotation", 0),
                "target_rgb_matrix": dev.get("TargetRGBMatrix", 0),
            }
    
    # Also store whitelist/blacklist for reference
    whitelist = data.get("WhiteList", [])
    blacklist = data.get("BlackList", [])
    
    print(f"[SIMHUB] Loaded {len(result)} devices from config (whitelist: {whitelist}, blacklist: {blacklist})")
    return result


# Cached SimHub devices (refreshed on each scan)
_simhub_devices_cache: dict = {}


def get_simhub_devices() -> list:
    """
    Return a list of all SimHub devices for UI dropdowns.
    Each entry has uid, name, rgb_leds, display_modules, etc.
    """
    global _simhub_devices_cache
    if not _simhub_devices_cache:
        _simhub_devices_cache = load_simhub_devices()
    
    return [
        {"uid": uid, **data}
        for uid, data in _simhub_devices_cache.items()
    ]

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
    global _simhub_devices_cache
    
    results = []
    ports = list(serial.tools.list_ports.comports())
    now = datetime.utcnow()
    touched = False

    # Refresh SimHub caches on each scan
    _simhub_devices_cache = load_simhub_devices()
    load_simhub_port_lists()
    load_simhub_profiles()

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

        # Check if this device is linked to a SimHub UID
        linked_uid = entry.get("simhub_uid")
        simhub_info = None
        if linked_uid and linked_uid in _simhub_devices_cache:
            simhub_info = _simhub_devices_cache[linked_uid]

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
            "simhub_uid": linked_uid,
            "simhub": simhub_info,
            "port_status": get_port_status(p.device),
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

