# Arduino Port History Manager

A powerful port tracking and analytics tool for Arduino devices. It provides a stable, human-friendly registry of all your Arduino connections, with comprehensive historical data and usage analytics.

---

## ✨ Features

- **Web dashboard**
  - Clean card view for each detected Arduino / COM port
  - Dark / light theme toggle with local persistence
  - Real-time connection status and duration tracking
- **Port Analytics**
  - Connection/disconnection event tracking
  - Most used ports statistics
  - Device diversity per port
  - Session duration and uptime tracking
- **Historical Timeline**
  - Real-time activity feed showing connect/disconnect events
  - Port change detection and logging
  - Color-coded event types (connected/disconnected/port change)
  - Export full history as JSON
- **Stable identity & config**
  - Stable per-device keys based on USB VID / PID / serial
  - Persistent configuration stored in `ports.json`
  - Per-device metadata:
    - Name
    - Role (LED / Gauge / Buttons / Display / Other)
    - Tags
    - Channel (zone)
    - Group (Desk, Wheel, Rig, etc.)
    - Notes for wiring info and calibration
  - Profiles: save/load multiple `ports.json` snapshots
- **Hardware details**
  - COM port, USB VID:PID, serial, description, manufacturer
  - "Connected for" indicator derived from first-seen timestamp
  - Connection history per device

---

## 🖼 UI Preview

> Dark theme – Port History Manager showing device cards, analytics dashboard, and activity timeline.

**Main dashboard**

![Main dashboard](docs/website.png)

**Analytics panel**

![Analytics panel](docs/analytics.png)

**Activity timeline**

![Activity timeline](docs/timeline.png)

---

## 🧱 Architecture

- `app.py` – Flask app, routes, analytics endpoints, and API handlers
- `port_manager.py` – port scanning, history tracking, analytics calculations
- `templates/index.html` – single-page UI (cards, timeline, analytics, theming)
- `ports.json` – device registry (generated/maintained automatically)
- `device_history.json` – connection/disconnection event log
- `port_stats.json` – port usage statistics and analytics

---

## 🔧 Requirements

- Windows with Python **3.10+**
- Arduino devices (any USB serial devices supported)

Python dependencies (see `requirements.txt`):

- `Flask`
- `pyserial`

---

## 🚀 Getting Started

From the project root:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Then open `http://127.0.0.1:5000` in your browser.

---

## 📊 Analytics & History

### Port Analytics
The system automatically tracks:
- **Total ports** ever detected
- **Active ports** currently connected
- **Most used ports** ranked by connection count
- **Device diversity** - how many different devices per port
- **Session duration** and uptime

### Activity Timeline
Real-time feed of all connection events:
- 🔌 **Connected** - New device detected
- 🔌 **Disconnected** - Device removed
- 🔄 **Port Change** - Device moved to different COM port

Each event includes timestamp, device name, and port information.

### Data Export
Export complete connection history:
- Click **📥 Export History** in the Actions panel
- Downloads JSON file with all events and metadata
- Includes timestamps, device details, and port changes

---

## 💾 Profiles

- Profiles are stored as JSON snapshots in the `profiles/` directory.
- Use the **Profiles** dropdown to:
  - **Save** – write the current `ports.json` state to `profiles/<name>.json`.
  - **Load** – replace `ports.json` with the selected profile.

This is ideal for switching between *Desk*, *Rig*, or different Arduino setups.

---

## 📁 Data Files

The system creates several data files in the project directory:

- `ports.json` – Device registry with metadata and configuration
- `device_history.json` – Connection/disconnection event log
- `port_stats.json` – Port usage statistics and analytics
- `profiles/` – Saved device configuration profiles

All files use JSON format for easy inspection and backup.

---

## ✅ Manual Smoke Test

After installation, verify the setup with this checklist:

1. **Start the application**
   - Run `python app.py` and open `http://127.0.0.1:5000`.
2. **Detect device**
   - Plug in an Arduino device.
   - Confirm a card appears in the UI with correct COM port and USB details.
3. **Install / assign ID**
   - Click **Install** on the card.
   - Verify device metadata is saved and card updates.
4. **Edit metadata**
   - Click **Edit**, change name/role/tags/channel/group, and **Save**.
   - Confirm the card updates immediately and `ports.json` reflects changes.
5. **Add notes**
   - Click **Edit**, add notes (e.g., "Wires: D4, D5, D7, D8") and **Save**.
   - Confirm the card shows the 📝 Notes section.
6. **View analytics**
   - Check the Analytics panel for port statistics.
   - Verify session duration and port counts update.
7. **Check timeline**
   - Confirm connection events appear in the Recent Activity timeline.
   - Unplug/replug device to see disconnect/connect events.
8. **Export history**
   - Click **📥 Export History** and verify JSON download.
9. **Persistence**
   - Restart the Flask app and reload the page.
   - Confirm all device data, analytics, and history are preserved.

If all steps pass, your Port History Manager is working correctly.

---

## 🔍 API Endpoints

The system provides several API endpoints for integration:

- `GET /api/analytics` – Returns current port analytics and statistics
- `GET /api/timeline?limit=100` – Returns connection event timeline
- `GET /api/device_history/<device_key>` – Returns history for specific device
- `GET /api/port_stats` – Returns detailed port statistics
- `GET /api/export_history` – Exports complete history as JSON

---

## 📓 Versioning & Changelog

This project uses simple semantic-style versions starting from **1.0.0**.
See `CHANGELOG.md` for released versions and the planned roadmap.

---

## 🤝 Contributing

This is an experimental project aimed at making Arduino port management and analytics more accessible.
Issues and pull requests are welcome – ideas around advanced analytics, better visualization, and multi-platform support are especially appreciated.

> Built as a comprehensive port tracking solution to help developers understand their Arduino device usage patterns and troubleshoot connection issues.
