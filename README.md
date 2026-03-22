# PalWorld Monitor

![CI](https://github.com/kevinnio/palworld-monitor/actions/workflows/ci.yml/badge.svg)

A Python application for managing PalWorld dedicated servers on Windows and Linux. The server automatically starts when players attempt to connect and shuts down when idle, with a web-based admin interface for monitoring and control.

## Features

- **Cross-platform support**: Windows and Linux compatibility
- **Automatic server management**:
  - Auto-start when players attempt to connect
  - Auto-stop after configured delay when server is empty (default: 10 minutes)
  - Supports both REST and RCON (legacy) APIs when talking to PalServer
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

## How to Use

### Step 1: Configure your Palworld Server.

<details>
<summary>Click here to see how to configure your Palworld Server.</summary>

**REST API Protocol (Recommended)**

The REST API is the recommended way to talk to your PalWorld server. To enable it:

1. **Locate `PalWorldSettings.ini`**
   ```
   {PalServerPath}\PalServer\Pal\Saved\Config\{Windows|Linux}Server\PalWorldSettings.ini
   ```
   If the file doesn't exist, copy from `DefaultPalWorldSettings.ini`.

2. **Enable REST API**
   Add these settings under `[ServerSettings]`:
   ```ini
   RESTEnabled=True
   RESTPort=8212
   AdminPassword=your_strong_admin_password
   ```

3. **Restart your PalWorld server**

**RCON Protocol (Legacy)**

Only use RCON if for some reason the REST API is not available:

1. **Configure RCON in `PalWorldSettings.ini`**.
   Add these settings under `[ServerSettings]`:
   ```ini
   RCONEnabled=True
   RCONPort=25575
   AdminPassword=your_strong_admin_password
   ```

2. **Restart your PalWorld server**

**Important Notes:**
- Use a strong admin password for security
- Ensure the configured ports are open in your firewall

</details>

### Step 2: Configure your monitor

Copy `src/settings.yaml.example` into `src/settings.yaml` and change settings at will.

#### Required Settings

These settings are required and the app won't start without them:

| Domain | Setting | Description |
|--------|---------|-------------|
| `palserver` | `exePath` | Full path to PalWorld server executable. Must be accessible and executable. |
| `palserver` | `adminPassword` | Admin password for server API access. Must match the one in your server's `PalWorldSettings.ini`. |
| `web` | `password` | Password for web admin interface. Ideally different from server admin password. |

See `src/settings.yaml.example` for all available settings.

### Step 3: Run the app

In the app's directory run:

```bash
# Install dependencies with pip
pip install -r requirements.txt
# Launch the app
python src/main.py
```

Or if you prefer using a venv:
```bash
python -m venv venv
# Install dependencies into your venv
venv\Scripts\pip install -r requirements.txt
# Launch the app
venv\Scripts\python src/main.py
```

That's it! Your monitor should be running at http://localhost:8213.

Access the admin panel using:
- **Username**: `admin` (You can change it in settings)
- **Password**: Your configured web password

## License

MIT

## Attribution

This project is a modified version of the original PalWorld Dedicated Server Auto-Start-Stop script by nomomo.
Special thanks to nomomo for the original implementation. Buy them a coffee at the following link:

<a href="https://www.buymeacoffee.com/nomomo" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-yellow.png" alt="Buy nomomo A Coffee" height="60"></a>
