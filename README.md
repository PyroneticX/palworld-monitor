# PalWorld-Dedicated-Server-Auto-Start-Stop

A Python application for automatically managing PalWorld dedicated servers on Windows and Linux. The server automatically starts when players attempt to connect and shuts down when idle, providing efficient resource management and a web-based admin interface for monitoring and control.

## Features

- **Cross-platform support**: Windows and Linux compatibility
- **REST API communication**: Recommended protocol for reliable server communication
- **RCON protocol support**: Legacy protocol option for older setups
- **Automatic server management**: 
  - Auto-start when players attempt to connect
  - Auto-stop when server is empty (configurable delay)
- **Web-based admin interface**: 
  - Real-time server monitoring
  - Player tracking and statistics
  - Server control capabilities
- **Player management**: 
  - Track online/offline player status
  - Player history with timestamps
  - Detailed player information (name, Steam ID, level)
- **Process management**: Robust server process lifecycle management
- **Configurable settings**: JSON-based configuration system
- **Deployment automation**: Scripts for remote server deployment and systemd service setup

## Limitations

- **Development stage**: This tool is in active development and may contain bugs
- **Local hosting requirement**: Must run on the same host as the PalWorld server (cannot control remote processes)
- **Network access**: Requires proper firewall configuration for REST/RCON ports
- **Unicode limitations**: RCON protocol has known issues with Unicode characters in player names

## How to Use

### Prerequisites

#### PalWorld Server Configuration

**REST API Protocol (Recommended)**

The REST API is the recommended communication method for better reliability and Unicode support. To enable it:

1. **Locate PalWorldSettings.ini**
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

Only use RCON if REST API is not available:

1. **Configure RCON in PalWorldSettings.ini**
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
- REST API is preferred due to better Unicode character support

### Configuration

Create a `src/settings.json` file to configure the application. Here are the key settings:

```json
{
    "os": "windows",
    "palworldServerExePath": "C:\\steamapps\\common\\PalServer\\PalServer.exe",
    "palworldServerHost": "127.0.0.1",
    "palworldServerPort": 8211,
    "palworldRESTPort": 8212,
    "palworldRCONPort": 25575,
    "palworldAdminPassword": "your_admin_password",
    "protocol": "REST",
    "useWebServer": true,
    "webServerPort": 8213,
    "controlServerThroughWeb": true,
    "showServerIPAddress": false,
    "autoStart": true,
    "autoStop": true,
    "autoStopDelay": 600,
    "updateInterval": 30,
    "enablePlayerTracking": true
}
```

**Key Configuration Options:**
- `protocol`: Set to `"REST"` (recommended) or `"RCON"`
- `palworldServerExePath`: Path to your PalWorld server executable
- `palworldAdminPassword`: Must match your PalWorld server admin password

Most settings are optional and have sensible defaults. See `src/settings.py` for all available options.

### Running the Application

Navigate to the project directory and run:

```bash
python src/main.py
```

The application will:
- Start monitoring for player connections
- Launch the web interface (if enabled) at `http://localhost:8213`
- Log activity to console and `app.log` file

**Web Admin Interface:**

<img src="https://github.com/nomomo/PalWorld-Dedicated-Server-Auto-Start-Stop/blob/main/images/AdminPageSample.png?raw=true" width="300px">

Access the admin panel using:
- **Username**: `admin`
- **Password**: Your configured admin password

## How to Install

### Option 1: Manual Installation

**Requirements:**
- Python 3.10 or higher
- Git (for cloning the repository)

**Steps:**

1. **Clone the repository**
   ```bash
   git clone https://github.com/nomomo/PalWorld-Dedicated-Server-Auto-Start-Stop.git
   cd PalWorld-Dedicated-Server-Auto-Start-Stop
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create configuration file**
   ```bash
   cp src/settings.json.example src/settings.json  # If example exists
   # Or create src/settings.json with your configuration
   ```

4. **Configure your PalWorld server** (see Prerequisites section above)

5. **Run the application**
   ```bash
   python src/main.py
   ```

## Testing

The project includes test scripts to verify functionality:

- `test/test_windows_driver.py`: Test Windows process management
- `test/test_linux_driver.py`: Test Linux process management

Run tests from the project root:

```bash
python test/test_windows_driver.py
```

## Known Issues

### RCON Protocol Issues

**Unicode Character Handling**
- The RCON `ShowPlayers` command fails when player nicknames contain Unicode characters
- **Root cause**: Mismatch between expected and received character counts in the py-rcon library
- **Impact**: Player tracking may not work correctly with international character names
- **Recommended solution**: Use REST API protocol instead of RCON

**Workaround for RCON (if REST is not available):**
```python
# Modify connection.py in the py-rcon package installation
def _read(self, length):
    packet_data = self.sock.recv(length)
    if len(packet_data) < length:
        #raise Exception('Received few bytes!') # disable raise exception
        return packet_data
    return packet_data
```

## License

MIT

## Dependencies

- [py-rcon](https://github.com/ttk1/py-rcon) - RCON protocol support
- [psutil](https://pypi.org/project/psutil/) - Process and system utilities
- [Schedule](https://pypi.org/project/schedule/) - Task scheduling
- [Flask](https://pypi.org/project/Flask/) - Web framework
- [requests](https://pypi.org/project/requests/) - HTTP library for REST API

## Happy??

<a href="https://www.buymeacoffee.com/nomomo" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-yellow.png" alt="Buy Me A Coffee" height="60"></a>
