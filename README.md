# HL7 Relay — Flask App

A lightweight Flask web app that runs an HL7 MLLP listener for one or more
lab machines and relays each message into ERPNext as a `Lab Machine
Message` record.

Each lab machine is configured as a **device** with its own dedicated MLLP
port, so multiple machines can connect at once — add, edit, activate, or
remove a device from the dashboard and its listener binds/unbinds live,
no restart needed.

## Requirements

- Python 3.9+
- Network access from the lab machines to this host (same LAN or VPN)
- ERPNext instance with API Key/Secret and the `Lab Machine Message` doctype

## Quick Start (one click)

- **Linux:** double-click `setup_linux.sh` (or run `./setup_linux.sh`)
- **Windows:** double-click `setup_windows.bat`

The script auto-creates the virtual environment, installs dependencies,
starts the app, and opens http://localhost:5050 in your browser. No manual
venv or pip commands needed. Equivalent manual command:

```bash
python3 run.py    # Windows: python run.py
```

Optionally copy `.env.example` to `.env` to override defaults before first
run. To serve the dashboard on a different port, set the
`HL7_DASHBOARD_PORT` environment variable before launching.

## Setup Checklist

1. **Settings** → Enter your ERPNext URL, API Key, and API Secret → Save → Test Connection
2. **Devices** → Add each lab machine (name + a unique MLLP port) → point that machine's HL7 interface at this host on that port
3. **Settings** → Install & Run in Background

## How it Works

```
Lab machine (HL7 interface)
    │  MLLP over TCP
    ▼
One listener per device (asyncio, port from Devices config)
    │
    ├── extracts machine_make / machine_model / lab_test_name from MSH/OBR
    ├── POSTs the raw message to ERPNext (/api/resource/Lab Machine Message)
    ├── sends the HL7 ACK back to the machine
    └── records a message log entry (in-memory + logs/error.log on failure)
```

### No database needed

All configuration (ERPNext credentials, devices/ports) lives in a plain
`config.json` next to the app — readable, editable, and easy to back up.
Message history is in-memory and resets on restart; failures are also
appended to `logs/error.log`.

> `config.json` contains your API credentials — keep it out of git
> (it is listed in `.gitignore`).
>
> **Upgrading from the old `hl7_listener.py` script:** on first start
> the app automatically migrates ERPNext credentials from the legacy
> `local_config.py` into `config.json` (creating one "Default" device on
> the old hardcoded port 5600), and keeps the old file as
> `local_config.py.bak`.

## Project Structure

```
hl7/
├── app/
│   ├── __init__.py               Flask app factory
│   ├── store.py                  config.json persistence + in-memory message log
│   ├── routes/
│   │   ├── dashboard.py          Main dashboard
│   │   ├── devices.py            Device (lab machine) CRUD
│   │   ├── settings.py           ERPNext settings
│   │   └── api.py                JSON API (status, service management)
│   ├── services/
│   │   ├── hl7_listener.py       Multi-device MLLP listener manager (asyncio)
│   │   └── erpnext_service.py    ERPNext REST API client
│   └── templates/                Jinja2 HTML templates
├── config.py
├── run.py                        Auto-bootstrap launcher (venv + deps + start)
├── server.py                     Flask server entry point
├── service_manager.py            OS service install (systemd / Task Scheduler)
├── setup_linux.sh                One-click setup (Linux)
├── setup_windows.bat             One-click setup (Windows)
└── requirements.txt
```

## Running in Production (background service)

The app installs itself as an OS-level background service directly from the UI:

1. Launch the app with the setup script (see Quick Start).
2. Open **Settings** → **Background Service** → click **Install & Run in Background**.
3. The foreground window hands off to the background service within a few seconds.
   You can now close the terminal — the app keeps running and auto-starts on boot.

Under the hood:

- **Linux:** a systemd *user* service (`~/.config/systemd/user/hl7-erpnext-sync.service`,
  no sudo required) with `Restart=on-failure` and `loginctl enable-linger` so it also
  runs while you're logged out. Output is appended to `hl7_relay.log`.
- **Windows:** a Task Scheduler task (`ERPNextHL7SyncService`) that starts at logon
  using `pythonw.exe` (no console window).

To disable auto-start, use **Settings → Background Service → Remove from Auto-Start**.

### Useful commands (Linux)

```bash
# Service status
systemctl --user status hl7-erpnext-sync

# Watch live logs
tail -f hl7_relay.log

# Restart / stop the service manually
systemctl --user restart hl7-erpnext-sync
systemctl --user stop hl7-erpnext-sync
```

## Known limitation

This relay only creates the raw `Lab Machine Message` record in ERPNext —
it does not parse OBX result segments into `Lab Test` records itself
(that previously happened in this repo's now-removed Frappe doctype
controller). Confirm that logic still exists server-side (e.g. in the
`hms_tz` app) on the ERPNext instance this relay points at, otherwise lab
results will stop flowing into `Lab Test` records.
