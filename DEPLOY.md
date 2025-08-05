# Deployment Guide

This guide provides step-by-step instructions for deploying the PalWorld Dedicated Server Auto Start/Stop application.

## Prerequisites

- Linux server with systemd support
- Python 3.8 or higher
- Git installed
- Root/sudo access for systemd service creation

## 1. Run Deploy Scripts

Run the deployment script using Python:
```bash
python3 scripts/deploy_app.py
```

The deploy script will:
- Set up Python virtual environment
- Install dependencies
- Create necessary directories

## 2. Upload Save Data

Upload save data using the Python script:
```bash
python3 scripts/save_data.py pull /path/to/local/dir
python3 scripts/save_data.py push /path/to/local/dir --backup
```

This script will:
- Create the data directory structure
- Set up save data locations
- Configure backup paths

## 3. Upload Config Data

Upload config data using the Python script:
```bash
python3 scripts/config_data.py pull /path/to/local/dir
python3 scripts/config_data.py push /path/to/local/dir --backup
```

This script will:
- Set up configuration directories
- Create initial config files
- Configure data paths

## 4. Manually Edit settings.json

Navigate to the application directory and edit `src/settings.json`:

```bash
nano /opt/palworld-control/src/settings.json
```

Configure the following settings:
- `palworld_server_path`: Path to your PalWorld server executable
- `server_port`: PalWorld server port (default: 25575)
- `rest_api_port`: REST API port (default: 8212)
- `rest_api_password`: Your REST API password
- `web_port`: Web interface port (default: 8080)
- `auto_start_threshold`: Minimum players to auto-start server
- `auto_stop_delay`: Minutes to wait before auto-stopping empty server

Example configuration:
```json
{
  "palworld_server_path": "/opt/palworld/PalServer.sh",
  "server_port": 25575,
  "rest_api_port": 8212,
  "rest_api_password": "your_rest_api_password_here",
  "web_port": 8080,
  "auto_start_threshold": 1,
  "auto_stop_delay": 30
}
```

## 5. Create Systemd Service

Create the systemd service using the Python script:
```bash
python3 scripts/create_systemd_service.py
```

This will:
- Copy the service file to `/etc/systemd/system/`
- Enable the service for auto-start
- Start the service

### Manual Service Setup (Alternative)

If the script doesn't work, manually create the service:

```bash
sudo cp scripts/palworld-control.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable palworld-control
sudo systemctl start palworld-control
```

## Verification

Check if the service is running:
```bash
sudo systemctl status palworld-control
```

Access the web interface:
- Open browser to `http://your-server-ip:8213`
- Default admin interface should be available

## Troubleshooting

### Check Service Logs
```bash
sudo journalctl -u palworld-control -f
```

### Common Issues
1. **Permission denied**: Ensure the service user has access to PalWorld directories
2. **Port conflicts**: Verify ports are not in use by other services
3. **REST API connection failed**: Check REST API password and port configuration
4. **Service won't start**: Verify Python path and dependencies are correct

### Service Management Commands
```bash
# Stop the service
sudo systemctl stop palworld-control

# Restart the service
sudo systemctl restart palworld-control

# Disable auto-start
sudo systemctl disable palworld-control

# View real-time logs
sudo journalctl -u palworld-control -f
```

## Security Considerations

- Change default REST/RCON API password
- Configure firewall rules for required ports
- Regularly update the application and dependencies
- Monitor system resources and logs

## Backup and Maintenance

- Regular backups of save data and configuration
- Monitor disk space usage
- Update PalWorld server regularly
- Review logs for any issues or anomalies 