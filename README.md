# SimHub Arduino Manager

An experimental but powerful device manager for SimHub Arduino setups.
It gives you a stable, human-friendly registry of all your SimHub Arduinos,
and a fast UI to identify, test, and organize them without fighting COM ports.

---

## ✨ Features

- **Web dashboard**
  - Compact card view for each detected Arduino / COM port
  - Dark / light theme toggle with local persistence
  - Per-card footer showing role, group, and connection duration
- **Stable identity & config**
  - Stable per-device keys based on USB VID / PID / serial
  - Persistent configuration stored in `ports.json`
  - Per-device metadata:
    - Name
    - Role (LED / Gauge / Buttons / Other)
    - Tags
    - Channel (zone)
    - Group (Desk, Wheel, Rig, etc.)
  - Profiles: save/load multiple `ports.json` snapshots
- **Identify & Test flows**
  - Per-device **Identify** action to blink hardware via SimHub
  - Per-device **Test** action for richer patterns
  - Channel-aware identify (`IdentifyChannel`) and mode (`IdentifyMode`) support
- **Hardware details**
  - COM port, USB VID:PID, serial, description, manufacturer
  - “Connected for” indicator derived from first-seen timestamp

---

## 🖼 UI Preview

> Dark theme – Arduino Port Manager showing device cards, edit flow, and identify/test state.

**Main dashboard**

![Main dashboard](docs/website.png)

**Edit device modal**

![Edit device modal](docs/edit.png)

**Identify / Blink state**

![Identify / Blink](docs/BLINKING.png)

---

## 🧱 Architecture

- `app.py` – Flask app, routes, profile handling, and update logic.
- `port_manager.py` – port scanning, config load/save, ID assignment, identify/test triggers.
- `templates/index.html` – single-page UI (cards, modals, footer, theming).
- `ports.json` – device registry (generated/maintained automatically).
- `plugin/ArduinoIdentifyPlugin` – SimHub C# plugin that exposes:
  - `IdentifyPulse`
  - `IdentifyTargetId`
  - `IdentifyChannel`
  - `IdentifyMode`
  - Actions: `Trigger Identify Blink`, `Trigger Test Pattern`

---

## 🔧 Requirements

- Windows with Python **3.10+**
- [SimHub](https://www.simhubdash.com/) installed and running
- `ArduinoIdentifyPlugin.dll` copied into SimHub’s plugins folder and enabled
- NumPad bindings in SimHub:
  - NumPad **9** → `Trigger Identify Blink`
  - NumPad **0** → `Trigger Test Pattern`

Python dependencies (see `requirements.txt`):

- `Flask`
- `pyserial`
- `pyautogui`
- `requests`

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

### SimHub setup

1. Copy `ArduinoIdentifyPlugin.dll` into your SimHub plugins folder.
2. Start SimHub and enable the plugin.
3. Bind keys in SimHub:
   - NumPad 9 → `Trigger Identify Blink`
   - NumPad 0 → `Trigger Test Pattern`
4. Connect your Arduino devices and start the Flask app.

When you click **Identify** / **Test** in the web UI, the app sends the hotkey,
SimHub calls the plugin action, and your Arduino firmware reacts based on
`IdentifyTargetId`, `IdentifyChannel`, and `IdentifyMode`.

---

## 💾 Profiles

- Profiles are stored as JSON snapshots in the `profiles/` directory.
- Use the **Profiles** dropdown in the header to:
  - **Save** – write the current `ports.json` state to `profiles/<name>.json`.
  - **Load** – replace `ports.json` with the selected profile.

This is ideal for switching between *Desk*, *Rig*, or different sim setups.

---

## 📓 Versioning & Changelog

This project uses simple semantic-style versions starting from **0.1.0**.
See `CHANGELOG.md` for released versions and the planned roadmap.

---

## 🤝 Contributing

This is an experimental project aimed at making SimHub Arduino workflows nicer.
Issues and pull requests are welcome – ideas around device health, better
SimHub integration, and multi-rig setups are especially appreciated.

