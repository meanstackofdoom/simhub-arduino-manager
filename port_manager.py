import pyautogui
import serial.tools.list_ports
import json
import re
from pathlib import Path
from datetime import datetime

# =========================
# Config
# =========================

# Use the directory where this script is located for config files
_SCRIPT_DIR = Path(__file__).parent.resolve()
CONFIG_FILE = _SCRIPT_DIR / "ports.json"
CUSTOM_SERIAL_NOTES_FILE = _SCRIPT_DIR / "custom_serial_notes.json"
HISTORY_FILE = _SCRIPT_DIR / "device_history.json"

# SimHub config paths
SIMHUB_CONFIG_PATH = Path(r"C:\Program Files (x86)\SimHub\PluginsData\Common\SerialDashPlugin.json")
SIMHUB_RGB_LEDS_PATH = Path(r"C:\Program Files (x86)\SimHub\PluginsData\Common\ArduinoRGBLedsSettings.json")
SIMHUB_RGB_MATRIX_PATH = Path(r"C:\Program Files (x86)\SimHub\PluginsData\Common\ArduinoRGBMatrixSettings.json")
SIMHUB_CUSTOM_SERIAL_PATH = Path(r"C:\Program Files (x86)\SimHub\PluginsData\Common\CustomSerialPlugin.GeneralSettings2.json")

# Cached data
_simhub_port_lists: dict = {"whitelist": [], "blacklist": []}
_simhub_active_profiles: dict = {}
_custom_serial_notes: dict = {}
_device_history: list = []
_last_seen_ports: set = set()

MAX_HISTORY_ENTRIES = 100

# =========================
# Device History
# =========================

def load_device_history() -> list:
    """Load device connection/disconnection history."""
    global _device_history
    if not HISTORY_FILE.exists():
        return []
    try:
        text = HISTORY_FILE.read_text().strip()
        if not text:
            return []
        _device_history = json.loads(text)
        return _device_history
    except Exception as e:
        print(f"[HISTORY] Failed to load history: {e}")
        return []


def save_device_history():
    """Save device history to file."""
    global _device_history
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    # Keep only last N entries
    _device_history = _device_history[-MAX_HISTORY_ENTRIES:]
    HISTORY_FILE.write_text(json.dumps(_device_history, indent=2))


def add_history_event(event_type: str, port: str, name: str, key: str, details: dict = None):
    """Add a device event to history."""
    global _device_history
    event = {
        "time": datetime.now().isoformat(),
        "type": event_type,  # "connected", "disconnected"
        "port": port,
        "name": name,
        "key": key,
    }
    if details:
        event["details"] = details
    _device_history.append(event)
    save_device_history()
    print(f"[HISTORY] {event_type.upper()}: {name} on {port}")


def get_device_history(limit: int = 50) -> list:
    """Get recent device history, newest first."""
    global _device_history
    return list(reversed(_device_history[-limit:]))


def get_device_port_history(key: str) -> list:
    """Get port history for a specific device."""
    global _device_history
    events = [e for e in _device_history if e.get("key") == key]
    return list(reversed(events[-20:]))


# =========================
# Custom Serial Notes (local annotations)
# =========================

def load_custom_serial_notes() -> dict:
    """Load local notes/annotations for Custom Serial devices."""
    global _custom_serial_notes
    if not CUSTOM_SERIAL_NOTES_FILE.exists():
        return {}
    try:
        text = CUSTOM_SERIAL_NOTES_FILE.read_text().strip()
        if not text:
            return {}
        _custom_serial_notes = json.loads(text)
        return _custom_serial_notes
    except Exception as e:
        print(f"[NOTES] Failed to load custom serial notes: {e}")
        return {}


def save_custom_serial_notes():
    """Save local notes/annotations for Custom Serial devices."""
    global _custom_serial_notes
    CUSTOM_SERIAL_NOTES_FILE.parent.mkdir(parents=True, exist_ok=True)
    CUSTOM_SERIAL_NOTES_FILE.write_text(json.dumps(_custom_serial_notes, indent=2))


def update_custom_serial_note(port: str, description: str = None, notes: str = None):
    """Update notes for a Custom Serial device by port name."""
    global _custom_serial_notes
    if port not in _custom_serial_notes:
        _custom_serial_notes[port] = {}
    
    if description is not None:
        _custom_serial_notes[port]["description"] = description
    if notes is not None:
        _custom_serial_notes[port]["notes"] = notes
    
    save_custom_serial_notes()
    print(f"[NOTES] Updated notes for {port}: {_custom_serial_notes[port]}")


def get_custom_serial_note(port: str) -> dict:
    """Get notes for a Custom Serial device."""
    global _custom_serial_notes
    return _custom_serial_notes.get(port, {})

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


def load_custom_serial_devices() -> list:
    """Load Custom Serial devices from SimHub's CustomSerialPlugin config."""
    if not SIMHUB_CUSTOM_SERIAL_PATH.exists():
        return []
    
    try:
        data = json.loads(SIMHUB_CUSTOM_SERIAL_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[SIMHUB] Failed to load Custom Serial config: {e}")
        return []
    
    devices = []
    for dev in data.get("Devices", []):
        last_error_date = dev.get("LastErrorDate")
        error_time_str = ""
        if last_error_date:
            try:
                error_dt = datetime.fromisoformat(last_error_date.replace("+10:00", "+10:00").split(".")[0])
                error_time_str = error_dt.strftime("%Y-%m-%d %H:%M")
            except:
                error_time_str = last_error_date[:16] if len(last_error_date) > 16 else last_error_date
        
        update_messages = dev.get("UpdateMessages", [])
        update_freq = 0
        has_expression = False
        expression_type = ""
        
        for msg in update_messages:
            if msg.get("IsEnabled", False):
                update_freq = msg.get("MaximumFrequency", 0)
                message_config = msg.get("Message", {})
                expression = message_config.get("Expression", "")
                if expression:
                    has_expression = True
                    if "TurboBoost" in expression or "Turbo" in expression:
                        expression_type = "Boost Gauge"
                    elif "RPM" in expression:
                        expression_type = "RPM Display"
                    elif "Speed" in expression:
                        expression_type = "Speedometer"
                    elif "Gear" in expression:
                        expression_type = "Gear Indicator"
                    else:
                        expression_type = "Custom Expression"
        
        on_connect = dev.get("OnConnectMessage", {}).get("Expression", "")
        on_disconnect = dev.get("OnDisconnectMessage", {}).get("Expression", "")
        
        port_name = dev.get("SerialPortName") or None
        device_name = dev.get("Name", "Custom Serial Device")
        notes_key = port_name if port_name else f"name:{device_name}"
        local_notes = get_custom_serial_note(notes_key)
        
        devices.append({
            "name": device_name,
            "description": dev.get("Description", ""),
            "port": port_name,
            "notes_key": notes_key,
            "baud_rate": dev.get("BaudRate", 0),
            "is_enabled": dev.get("IsEnabled", False),
            "is_connected": dev.get("IsConnected", False),
            "is_connecting": dev.get("IsConnecting", False),
            "is_frozen": dev.get("IsFreezed", False),
            "dtr_enable": dev.get("DtrEnable", False),
            "rts_enable": dev.get("RtsEnable", False),
            "auto_reconnect": dev.get("AutomaticReconnect", False),
            "startup_delay": dev.get("StartupDelayMs", 0),
            "last_error": dev.get("LastErrorMessage"),
            "last_error_date": error_time_str,
            "log_incoming": dev.get("LogIncomingData", False),
            "update_frequency": update_freq,
            "has_expression": has_expression,
            "expression_type": expression_type,
            "has_on_connect": bool(on_connect),
            "has_on_disconnect": bool(on_disconnect),
            "custom_description": local_notes.get("description", ""),
            "notes": local_notes.get("notes", ""),
        })
    
    print(f"[SIMHUB] Loaded {len(devices)} Custom Serial devices")
    return devices


def load_simhub_devices() -> dict:
    """Read SimHub's SerialDashPlugin.json and return a dict keyed by deviceUniqueId."""
    if not SIMHUB_CONFIG_PATH.exists():
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
    
    whitelist = data.get("WhiteList", [])
    blacklist = data.get("BlackList", [])
    print(f"[SIMHUB] Loaded {len(result)} devices from config")
    return result


_simhub_devices_cache: dict = {}


def get_simhub_devices() -> list:
    """Return a list of all SimHub devices for UI dropdowns."""
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
load_custom_serial_notes()
load_device_history()


def save_config():
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(saved, indent=2))

# =========================
# Identify (Keyboard → SimHub)
# =========================

def identify_device(key, mode="identify"):
    """Trigger an identify or test pattern in SimHub via keyboard hotkeys."""
    device_id = saved.get(key, {}).get("identify_id")

    if not isinstance(device_id, int):
        print("[IDENTIFY] Missing numeric identify_id")
        return

    if mode == "test":
        print(f"[AUTOMATION] TEST device ID {device_id}")
        pyautogui.press("num0")
    else:
        print(f"[AUTOMATION] Identifying device ID {device_id}")
        pyautogui.press("num9")

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
    global _simhub_devices_cache, _last_seen_ports
    
    results = []
    ports = list(serial.tools.list_ports.comports())
    now = datetime.utcnow()
    touched = False

    # Refresh SimHub caches on each scan
    _simhub_devices_cache = load_simhub_devices()
    load_simhub_port_lists()
    load_simhub_profiles()
    load_custom_serial_notes()

    # Track current ports for connect/disconnect detection
    current_ports = set()

    for p in ports:
        key = make_device_key(p)
        current_ports.add(key)
        entry = dict(saved.get(key, {}))

        # Check if this is a new connection
        was_connected = key in _last_seen_ports
        
        # Ensure we have a stable "connected_since" timestamp per device
        connected_since = entry.get("connected_since")
        if not connected_since or not was_connected:
            connected_since = now.isoformat()
            entry["connected_since"] = connected_since
            saved[key] = entry
            touched = True
            
            # Log connection event
            if _last_seen_ports:  # Only log after first scan
                add_history_event(
                    "connected",
                    p.device,
                    entry.get("name", "New Device"),
                    key,
                    {"vid": getattr(p, "vid", None), "pid": getattr(p, "pid", None)}
                )

        # Track last known port
        if entry.get("last_port") != p.device:
            entry["last_port"] = p.device
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
            "notes": entry.get("notes", ""),
        })

    # Detect disconnections
    if _last_seen_ports:
        disconnected = _last_seen_ports - current_ports
        for key in disconnected:
            entry = saved.get(key, {})
            add_history_event(
                "disconnected",
                entry.get("last_port", "Unknown"),
                entry.get("name", "Unknown Device"),
                key
            )
            # Clear connected_since so next connection is fresh
            if key in saved:
                saved[key].pop("connected_since", None)
                touched = True

    _last_seen_ports = current_ports

    if touched:
        save_config()

    return results


def get_known_devices() -> list:
    """Get all known devices from config, including disconnected ones."""
    results = []
    for key, entry in saved.items():
        if not key.startswith("USB:"):
            continue
        results.append({
            "key": key,
            "name": entry.get("name", "Unknown"),
            "last_port": entry.get("last_port", "N/A"),
            "role": entry.get("role", "Unassigned"),
            "group": entry.get("group", ""),
            "identify_id": entry.get("identify_id"),
            "installed": entry.get("installed", False),
        })
    return results


# =========================
# Key Function
# =========================

def make_device_key(port):
    """Generate a stable, canonical USB key."""
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
