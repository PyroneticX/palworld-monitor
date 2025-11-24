# Palworld Monitor

A Python application for managing PalWorld dedicated servers on Windows and Linux. The server automatically starts when players attempt to connect and shuts down when idle, with a web-based admin interface for monitoring and control.

## Features

- **Cross-platform support**: Windows and Linux compatibility
- **REST API communication**: Recommended protocol for reliable server communication
- **RCON protocol support**: Legacy protocol option for older setups
- **Automatic server management**: 
  - Auto-start when players attempt to connect
  - Auto-stop when server is empty (configurable delay)
- **Web-based admin interface**: 
  - Real-time server monitoring
  - Player tracking and stats
  - Server control capabilities
- **Player management**: 
  - Track online/offline players
  - Detailed player information (name, Steam ID, level)
  - Kick or ban players
- **Configurable settings**: JSON-based configuration system

## Limitations

- **Development stage**: This tool is in active development and may contain bugs
- **Same host requirement**: In order to be able to start/stop the Palworld Server this app must run on the same host as the PalWorld server (your own PC, same AWS EC2 instance, same Docker container, etc).

## How to Use

#### Step 0: Configure your Palworld Server.

<details>
<summary>Click here to see how to configure your Palworld Server.</summary>

**REST API Protocol (Recommended)**

The REST API is the recommended communication method for better reliability and Unicode support. To enable it:

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

Copy `src/settings.json.example` into `src/settings.json` and change settings at will.

Most settings are optional and have sensible defaults. Feel free to change if you need to. See `src/settings.py` for all available options.

### Required Settings

These settings are required and the app won't start without them:

| Setting | Description |
|---------|-------------|
| `os` | Operating system type: `windows` or `linux`. Set to `linux` if running on Linux. |
| `palworldServerExePath` | Full path to PalWorld server executable. Must be accessible and executable. |
| `palworldServerAdminPassword` | Admin password for server API access. Must match your `PalWorldSettings.ini`. |
| `webPassword` | Password for web admin interface. Separate from server admin password. |
| `sessionSecretKey` | Secret key for session encryption. Use whatever unique 32-char string you want. |

### Step 3: Run the app

In the app's directory run:

```bash
# Install dependencies with pip
pip install -r requirements.txt
# Launch the app
python src/main.py
```

That's it. Your monitor should be running at http://localhost:8213.

**Web Admin Interface:**

<img src="images/AdminPageSample.png?raw=true" width="300px">

Access the admin panel using:
- **Username**: `admin` (You can change it in settings)
- **Password**: Your configured web password

## License

MIT

## Attribution

This project is a modified version of the original PalWorld Dedicated Server Auto-Start-Stop script by nomomo.
Special thanks to nomomo for the original implementation. Buy them a coffee at the following link:

<a href="https://www.buymeacoffee.com/nomomo" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-yellow.png" alt="Buy nomomo A Coffee" height="60"></a>
