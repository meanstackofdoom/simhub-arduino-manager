# Changelog

All notable changes to this project will be documented in this file.

This project follows a pragmatic, real-world approach to versioning.
Features may evolve rapidly as SimHub integrations are explored.

---

## [0.2.1] – Session Stats & Custom Serial Integration
**2025-12-24**

### ✨ Added
- **Session Statistics Modal** – Track your session in real-time:
  - App uptime (how long the manager has been running)
  - Identify clicks, Test clicks, Installs counters
  - Session start time and last scan time
  - Profiles loaded/saved counts
- **Custom Serial Device Info** – Reads `CustomSerialPlugin.GeneralSettings2.json`:
  - Shows all Custom Serial devices (e.g., boost gauges)
  - Displays port, baud rate, DTR/RTS status, auto-reconnect, logging
  - Connection status (Connected/Disconnected/Disabled)
  - Last error message with timestamp if any
- **Enhanced Visual Indicators**:
  - ✓ Connected badge with checkmark prefix
  - Cleaner status badges with improved styling
- New **📊 Stats** button in footer to open session statistics

### 🛠️ Internal
- Added `load_custom_serial_devices()` function to parse SimHub's CustomSerialPlugin config
- Added session tracking (`SESSION_START`, `SESSION_STATS`) in `app.py`
- Added `get_session_uptime()` helper for human-readable uptime
- Stats counters track identify, test, install, and profile actions
- Auto-refresh now pauses when Stats modal is open

---

## [0.2.0] – SimHub Config Integration & UI Redesign
**2025-12-24**

### ✨ Added
- **SimHub Config Reader**: Directly reads `SerialDashPlugin.json` from SimHub's PluginsData folder
- **Device Linking**: Link local Arduino devices to SimHub devices via their Unique ID
- **SimHub Metadata Display**: Linked devices now show:
  - SimHub device name
  - RGB LED count
  - Display module count
  - Motor count
  - Button read status
  - Enabled/Disabled status
- New **SimHub Link** dropdown in the Edit modal to associate devices
- Visual indicator on cards showing linked SimHub devices with a green "SIMHUB LINKED" badge
- Warning indicator when a SimHub UID is set but the device isn't found in SimHub config
- **COM Port Status**: Shows if port is whitelisted/blacklisted in SimHub

### 🎨 UI Redesign
- Complete visual overhaul with professional dark theme
- New color palette with better contrast (#22c55e accent, deeper blacks)
- Status pills in header (Online count, SimHub, Plugin)
- Tag-based card metadata (COM port, ID, Role as colored pills)
- Hardware info displayed in clean 2-column grid
- Cleaner SimHub Linked boxes with SVG link icon
- Improved footer with grouped buttons
- Better search box with magnifying glass icon

### 🛠️ Internal
- Added `load_simhub_devices()` function to parse SimHub's MultipleArduinoSettings
- Added `load_simhub_port_lists()` to read whitelist/blacklist from SimHub
- Added `load_simhub_profiles()` to read active LED profiles from SimHub
- Added `get_port_status()` helper for port status indicators
- Added `get_simhub_devices()` helper for UI dropdowns
- SimHub device cache refreshed on each port scan
- New `simhub_uid` field in device configuration for persistent linking
- Flask template auto-reload enabled for development

---

## [0.1.0] – Initial Public Release
**2025-12-24**

### ✨ Added
- Initial release of **SimHub Arduino Manager**
- Web-based dashboard for managing SimHub Arduino devices
- Automatic detection of connected Arduino serial ports
- Persistent device registry stored in `ports.json`
- Per-device **Identify ID** assignment system
- Visual **Identify / Blink** and **Test** actions to map and verify devices
- Channel-aware identify and test modes driven by a custom SimHub plugin
- Bulk install function to auto-assign IDs to all devices
- Editable device metadata:
  - Name
  - Role (LED / Gauge / Buttons / Other)
  - Tags
  - Channel (zone)
  - Group (Desk / Wheel / Rig / etc.)
- Connection duration indicator and basic USB hardware details per device
- Profiles system for saving and loading multiple `ports.json` snapshots
- Clean dark / light themed UI designed for sim racing environments
- Flask-based backend with a lightweight single-page frontend

### 💄 UI Polish
- Refined profile toolbar (select + load + save) for a more professional header layout
- Tooltips for Identify/Test/Bulk Install actions and keyboard shortcut helper in the footer
 - Device Settings modal now explains each field inline

### 🧪 Experimental
- Keyboard-triggered SimHub Identify integration
- Early SimHub API probing for future telemetry & health features
- Dynamic device key handling based on USB identifiers

### 🛠️ Internal
- Modularized device logic into `port_manager.py`
- Flask routing split cleanly between actions and rendering
- Basic error handling for missing devices and malformed data
- Safe handling of empty or invalid update requests
- Basic environment guardrails in the header (SimHub running / plugin presence)
- Install button hidden once a device is already marked as installed
- More robust device keys for CH340-style Arduinos with no serial (fallback to COM-based key)
- Gauge-role devices are marked as SimHub-driven and no longer expose Identify/Test controls

### ⚠️ Known Limitations
- SimHub API access is experimental and may vary by version
- Device heartbeat / RX-TX health indicators not yet implemented
- USB identifiers may differ across systems and reconnects
- Not yet tested with large multi-rig setups

---

## Planned (Upcoming)

### 🚧 0.2.x – Device Health & Metadata (Mostly Complete ✅)
- ✅ SimHub config file integration (LED count, modules, motors)
- ✅ Device linking via SimHub Unique ID
- ✅ Custom Serial device info (boost gauges, etc.)
- ✅ Session statistics tracking
- Live device health / heartbeat indicators
- RX / TX counters (requires SimHub live API)
- Firmware name & MCU type display (if exposed by SimHub)

### 🚧 0.3.x – Power User Features
- Improved multi-profile management (per-rig presets, cloning, etc.)
- Export / import configurations beyond simple JSON snapshots
- Multi-rig support
- Improved SimHub API integration (if available)
- Optional background polling service

---

## Notes

This project is:
- **Independent** of SimHub
- **Community-driven**
- **Experimental by design**

Feedback, issues, and pull requests are welcome.


