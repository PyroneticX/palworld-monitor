# PalWorld-Dedicated-Server-Auto-Start-Stop

- This is a Python application for automatically managing PalWorld dedicated servers on Windows and Linux.
- When the PalWorld server is not running, it automatically starts when a user attempts to connect.
- When the PalWorld server is running and there are no online users, it automatically shuts down after a configurable period.
- Provides an Admin Page through the web server to monitor and control the server.
- Supports both RCON and REST API protocols for server communication.

## Features

- **Cross-platform support**: Windows and Linux
- **Multiple communication protocols**: RCON and REST API
- **Automatic server management**: Start on connection, stop when idle
- **Web-based admin interface**: Monitor and control server remotely
- **Player tracking**: Track currently online players
- **Process management**: Robust process lifecycle management
- **Configurable settings**: JSON-based configuration system

## Limitations

- This tool is designed for personal use and is currently in development. It may have bugs.
- Tested primarily on small-scale servers.
- Be cautious as unknown security issues may arise.
- This tool expects to live in the same host as the Palword Server as it cannot control remote 
  processes (as of yet).

## How to Use

### Prerequisites

#### For REST API Protocol (recommended)
To enable the REST API in your PalWorld server:

1. **Edit the PalWorldSettings.ini file**

   Locate your `PalWorldSettings.ini` file, typically found at:
   ```
   {PalServerPath}\PalServer\Pal\Saved\Config\WindowsServer\PalWorldSettings.ini
   ```
   If the file does not exist or is empty, copy the contents from `DefaultPalWorldSettings.ini` in the same directory.

2. **Set the REST API parameters**

   Add or update the following lines in your `PalWorldSettings.ini` file under the `[ServerSettings]` section:
   ```
   RESTEnabled=True
   RESTPort=8212
   AdminPassword=your_admin_password
   ```

   - `RESTEnabled=True` enables the REST API.
   - `RESTPort=8212` sets the port for REST API communication (ensure it matches your configuration).
   - `AdminPassword` is required for authentication.

3. **Restart your PalWorld server**

   After saving the changes, restart your PalWorld server for the settings to take effect.

**Note:**  
- Make sure the REST port is open and not blocked by your firewall.
- Use a strong admin password to protect your server.

#### For RCON Protocol (legacy)
To enable RCON in your PalWorld server:

1. Open your `PalWorldSettings.ini` file, typically located at:
   ```
   {PalServerPath}\PalServer\Pal\Saved\Config\WindowsServer\PalWorldSettings.ini
   ```
   If this file does not exist or is empty, copy the contents from:
   ```
   {PalServerPath}\PalServer\DefaultPalWorldSettings.ini
   ```
   and paste them into `PalWorldSettings.ini`.

2. Under the `[ServerSettings]` section, add or update the following lines:
   ```
   RCONEnabled=True
   RCONPort=25575
   AdminPassword=your_admin_password
   ```
   - `RCONEnabled=True` enables the RCON protocol.
   - `RCONPort=25575` sets the RCON port (ensure it matches your configuration).
   - `AdminPassword` is required for authentication.

3. Save the file and restart your PalWorld server for the changes to take effect.

**Note:**  
- Make sure the RCON port is open and not blocked by your firewall.
- Use a strong admin password to protect your server.

### Download

Download the code from this repository using the "Download ZIP" feature or execute the following command:

```bash
git clone https://github.com/nomomo/PalWorld-Dedicated-Server-Auto-Start-Stop.git
```

### Install Dependencies

This application has been tested with Python 3.10+. To install dependencies, execute the following command:

```bash
pip install -r requirements.txt
```

### Configuration

The application uses a JSON-based configuration system. Create or modify the `src/settings.json` file according to your server settings:

```javascript
{
    // Operating system: "windows" or "linux"
    "os": "windows",
    
    // Path to your PalWorld server executable
    "palworldServerExePath": "C:\\steamapps\\common\\PalServer\\PalServer.exe",
    
    // PalWorld server host address (used for auto-start detection)
    "palworldServerHost": "127.0.0.1",
    
    // PalWorld server port (used for auto-start detection)
    "palworldServerPort": 8211,
    
    // REST API port for server communication
    "palworldRESTPort": 8212,
    
    // RCON port for server communication (legacy)
    "palworldRCONPort": 25575,
    
    // Admin password for server authentication
    "palworldAdminPassword": "your_admin_password",
    
    // Communication protocol: "REST" (recommended) or "RCON"
    "protocol": "REST",
    
    // Enable web-based admin interface
    "useWebServer": true,
    
    // Web server host (use "0.0.0.0" for external access)
    "webServerHost": "0.0.0.0",
    
    // Web server port for admin interface
    "webServerPort": 8213,
    
    // Enable server control through web interface
    "controlServerThroughWeb": true,
    
    // Show server IP address in web interface
    "showServerIPAddress": true,
    
    // Automatically start server when connection is detected
    "autoStart": true,
    
    // Automatically stop server when no players are online
    "autoStop": true,
    
    // Seconds to wait before stopping server when empty
    "autoStopDelay": 600,
    
    // Interval (seconds) to check server status
    "updateInterval": 30,
    
    // Enable player tracking functionality
    "enablePlayerTracking": true
}
```

Most settings are optional. Check default values inside `src/settings.py`.

### Running the Application

#### Option 1: Direct Python Execution
Navigate to the root of the project and execute:

```bash
python src/main.py
```

The application will start and display logs in the console. Logs are also written to the `app.log` file.

If `"useWebServer": true` is set in the configuration, the Admin Page will be accessible at `http://localhost:8213/` (or your configured port).

<img src="https://github.com/nomomo/PalWorld-Dedicated-Server-Auto-Start-Stop/blob/main/images/AdminPageSample.png?raw=true" width="300px">

## Testing

The project includes test scripts to verify functionality:

- `test/test_windows_driver.py`: Test Windows process management
- `test/test_linux_driver.py`: Test Linux process management

Run tests from the project root:

```bash
python test/test_windows_driver.py
```

## Known Issues

- The ShowPlayers command does not work in RCON Commands if the user's nickname contains Unicode characters. This error occurs because the number of characters received that should be read differs from the number of characters actually received.
- Workaround: Open the connection.py file installed with the py-rcon package and modify the contents of the _read function as follows:

```Python
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
