import serial.tools.list_ports
import json
import time
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter

# =========================
# Config
# =========================

# Use the directory where this script is located for config files
_SCRIPT_DIR = Path(__file__).parent.resolve()
CONFIG_FILE = _SCRIPT_DIR / "ports.json"
HISTORY_FILE = _SCRIPT_DIR / "device_history.json"
PORT_STATS_FILE = _SCRIPT_DIR / "port_stats.json"
CONNECTION_EVENTS_FILE = _SCRIPT_DIR / "connection_events.json"

# Cached data
_device_history: list = []
_connection_events: list = []
_port_stats: dict = {}
_last_seen_ports: set = set()
_session_start = datetime.now()

MAX_HISTORY_ENTRIES = 200
MAX_EVENTS_ENTRIES = 500

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
        "type": event_type,  # "connected", "disconnected", "port_change"
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
# Port Analytics & Statistics
# =========================

def load_port_stats() -> dict:
    """Load port usage statistics."""
    global _port_stats
    if not PORT_STATS_FILE.exists():
        return {}
    try:
        text = PORT_STATS_FILE.read_text().strip()
        if not text:
            return {}
        _port_stats = json.loads(text)
        return _port_stats
    except Exception as e:
        print(f"[STATS] Failed to load port stats: {e}")
        return {}


def save_port_stats():
    """Save port statistics to file."""
    global _port_stats
    PORT_STATS_FILE.parent.mkdir(parents=True, exist_ok=True)
    PORT_STATS_FILE.write_text(json.dumps(_port_stats, indent=2))


def update_port_stats(port: str, event_type: str, device_key: str = None):
    """Update port statistics for analytics."""
    global _port_stats
    
    if port not in _port_stats:
        _port_stats[port] = {
            "first_seen": datetime.now().isoformat(),
            "last_seen": datetime.now().isoformat(),
            "connection_count": 0,
            "disconnection_count": 0,
            "total_connection_time": 0,
            "devices": set(),
            "most_recent_device": None
        }
    
    stats = _port_stats[port]
    stats["last_seen"] = datetime.now().isoformat()
    
    if event_type == "connect":
        stats["connection_count"] += 1
        if device_key:
            stats["devices"].add(device_key)
            stats["most_recent_device"] = device_key
    elif event_type == "disconnect":
        stats["disconnection_count"] += 1
    
    # Convert set to list for JSON serialization
    stats["devices"] = list(stats["devices"])
    save_port_stats()


def get_port_analytics() -> dict:
    """Get comprehensive port analytics."""
    global _port_stats
    
    if not _port_stats:
        load_port_stats()
    
    # Calculate analytics
    total_ports = len(_port_stats)
    active_ports = len([p for p in _port_stats.values() if "most_recent_device" in p and p["most_recent_device"]])
    
    # Most used ports
    port_usage = [(port, data["connection_count"]) for port, data in _port_stats.items()]
    most_used = sorted(port_usage, key=lambda x: x[1], reverse=True)[:5]
    
    # Devices per port
    devices_per_port = [(port, len(data["devices"])) for port, data in _port_stats.items()]
    port_diversity = sorted(devices_per_port, key=lambda x: x[1], reverse=True)[:5]
    
    return {
        "total_ports": total_ports,
        "active_ports": active_ports,
        "most_used_ports": most_used,
        "port_diversity": port_diversity,
        "session_duration": str(datetime.now() - _session_start).split('.')[0],
        "last_updated": datetime.now().isoformat()
    }


def get_connection_timeline(limit: int = 100) -> list:
    """Get connection events as a timeline."""
    global _device_history
    events = []
    
    for event in _device_history[-limit:]:
        events.append({
            "time": event["time"],
            "type": event["type"],
            "port": event["port"],
            "device_name": event["name"],
            "device_key": event["key"]
        })
    
    return sorted(events, key=lambda x: x["time"], reverse=True)


# =========================
# Config (ports.json)
# =========================

def load_config() -> dict:
    if not CONFIG_FILE.exists():
        return {}
    try:
        text = CONFIG_FILE.read_text().strip()
        if not text:
            return {}
        return json.loads(text)
    except Exception as e:
        print(f"[CONFIG] Failed to load config: {e}")
        return {}


def save_config():
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(saved, indent=2))


# =========================
# Device Management
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

    if "device_id" not in saved[key]:
        used_ids = {
            d.get("device_id")
            for d in saved.values()
            if isinstance(d.get("device_id"), int)
        }

        new_id = 1
        while new_id in used_ids:
            new_id += 1

        saved[key]["device_id"] = new_id
        print(f"[INSTALL] Assigned device_id {new_id} to {key}")

    saved[key]["installed"] = True
    save_config()
    return True


def bulk_install():
    devices = scan_ports()
    count = 0
    for d in devices:
        if not d.get("installed") or not d.get("device_id"):
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


def make_device_key(port_info) -> str:
    """Create a stable device key from USB VID/PID/serial."""
    vid = getattr(port_info, "vid", None)
    pid = getattr(port_info, "pid", None)
    serial = getattr(port_info, "serial_number", "") or ""
    
    if vid and pid:
        return f"{vid:04X}:{pid:04X}:{serial}"
    return f"PORT:{port_info.device}"


def scan_ports():
    global _last_seen_ports
    
    results = []
    ports = list(serial.tools.list_ports.comports())
    now = datetime.utcnow()
    touched = False

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
                update_port_stats(p.device, "connect", key)

        # Track last known port
        if entry.get("last_port") != p.device:
            old_port = entry.get("last_port")
            if old_port and old_port != p.device:
                # Port change detected
                add_history_event(
                    "port_change",
                    p.device,
                    entry.get("name", "Device"),
                    key,
                    {"old_port": old_port, "new_port": p.device}
                )
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

        results.append({
            "key": key,
            "port": p.device,
            "name": entry.get("name", description or "Unknown Device"),
            "description": description,
            "manufacturer": manufacturer,
            "serial_number": serial_number,
            "vid": vid,
            "pid": pid,
            "vid_hex": vid_hex,
            "pid_hex": pid_hex,
            "status": "connected",
            "connected_since": connected_since,
            "connected_for": connected_for,
            "role": entry.get("role", "Unassigned"),
            "tags": entry.get("tags", []),
            "channel": entry.get("channel", 0),
            "group": entry.get("group", ""),
            "installed": entry.get("installed", False),
            "device_id": entry.get("device_id"),
            "notes": entry.get("notes", ""),
        })

    # Check for disconnected devices
    for key in _last_seen_ports - current_ports:
        device_entry = saved.get(key, {})
        add_history_event(
            "disconnected",
            device_entry.get("last_port", "Unknown"),
            device_entry.get("name", "Unknown Device"),
            key
        )
        update_port_stats(device_entry.get("last_port", "Unknown"), "disconnect", key)

    _last_seen_ports = current_ports

    if touched:
        save_config()

    return results


# Initialize
saved = load_config()
load_device_history()
load_port_stats()
