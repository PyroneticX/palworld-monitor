# PalWorld Monitor

![CI](https://github.com/kevinnio/palworld-monitor/actions/workflows/ci.yml/badge.svg)

A Python application for managing PalWorld dedicated servers on Windows and Linux. The server automatically starts when players attempt to connect and shuts down when idle, with a web-based admin interface for monitoring and control.

## Features

- **Cross-platform support**: Windows and Linux compatibility
- **Automatic server management**:
  - Auto-start when players attempt to connect
  - Auto-stop after configured delay when server is empty (default: 10 minutes)
  - Supports REST API communication with PalServer
- **Web-based admin interface**:
  - Real-time server monitoring
  - Server control capabilities
  - Light/dark theme support
- **Player management**:
  - Track online/offline players (session-based)
  - Kick or ban players
  - Player details: name, Steam ID, level
- **Security**:
  - Web interface with authentication (username/password login)
  - CSRF protection and rate limiting
  - Login attempt lockout after failed attempts
- **Configurable settings**: YAML-based configuration file

## Limitations

- **Development stage**: This tool is in active development and may contain bugs
- **Same host requirement**: In order to be able to start/stop the Palworld Server this app must run on the same host as the PalWorld server (your own PC, same AWS EC2 instance, same Docker container, etc).

## Quick Start

1. Download from the latest [GitHub Release](https://github.com/kevinnio/palworld-monitor/releases):
   - **Windows:** `palworld-monitor.exe`
   - **Linux:** `palworld-monitor`
2. Run it. On first launch it auto-detects your PalServer, enables the REST
   API in your `PalWorldSettings.ini`, asks for a couple of passwords, and
   starts.
3. Open http://localhost:8213 in your browser and log in with the password you
   chose.

No config files to edit. The monitor auto-starts and auto-stops your PalServer
as players come and go.

### From source

```bash
uv sync             # install deps
uv run poe start    # same interactive first-run setup
```

Run e2e smoke tests with `uv run poe smoke`. **Do not run smoke tests
while a real PalServer is running** — they kill all PalServer processes
and occupy game ports to isolate the test environment.

## Configuration

After first run, a `settings.yaml` file is saved next to the app.  You can edit
it to change ports, polling rate, auto-stop delay, etc.

| Setting (YAML) | CLI flag | Description |
|-----------------|----------|-------------|
| — | `--settings PATH` | Path to an alternate `settings.yaml` |
| `palserver.exePath` ⚑ | `--exe-path PATH` | Full path to PalServer executable |
| `palserver.adminPassword` ⚑ | `--admin-password PASS` | Admin password from your server's `PalWorldSettings.ini` |
| `palserver.pollingRate` ⚑ | `--polling-rate SEC` | Seconds between status polls (default `5`) |
| `web.password` ⚑ | `--web-password PASS` | Password for the web admin interface |
| `palserver.host` | `--host HOST` | Palworld server host |
| `palserver.port` | `--server-port PORT` | Palworld game server port |
| `palserver.protocol` | `--protocol REST` | Server communication protocol |
| `web.enabled` | `--no-web` | Disable the web admin UI |
| `web.port` | `--web-port PORT` | Web admin UI port |
| `web.username` | `--web-username USER` | Web admin username |
| `features.autoStart` | `--no-auto-start` | Disable auto-start on UDP probe |
| `features.autoStop` | `--no-auto-stop` | Disable auto-stop when server is empty |

⚑ = required on first run.  Passwords are masked in logs.  Every setting can be
overridden via CLI flag (run with `--help`).

## Manual PalServer setup (optional)

The app auto-configures your PalServer on first run.  This section is only
needed if auto-setup fails, or if you want to configure things yourself.

Your PalServer needs the REST API enabled in `PalWorldSettings.ini`:

```ini
RESTAPIEnabled=True
RESTAPIPort=8212
AdminPassword=your_strong_admin_password
```

<details>
<summary>Where to find PalWorldSettings.ini</summary>

Look inside your PalServer folder. The exact path depends on how you installed it:

**Steam (most common):**

```
C:\Program Files (x86)\Steam\steamapps\common\PalServer\Pal\Saved\Config\WindowsServer\PalWorldSettings.ini
```

**SteamCMD (dedicated server tool):**

```
C:\Program Files\PalServer\Pal\Saved\Config\WindowsServer\PalWorldSettings.ini
```

If `PalWorldSettings.ini` doesn't exist, copy `DefaultPalWorldSettings.ini`
from the same folder and rename it.
</details>

## License

MIT

## Attribution

This project is a modified version of the original PalWorld Dedicated Server Auto-Start-Stop script by nomomo.
Special thanks to nomomo for the original implementation. Buy them a coffee at the following link:

<a href="https://www.buymeacoffee.com/nomomo" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-yellow.png" alt="Buy nomomo A Coffee" height="60"></a>
