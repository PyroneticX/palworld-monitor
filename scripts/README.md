# Scripts Directory

This directory contains deployment and management scripts for the PalWorld Dedicated Server Auto Start/Stop application.

## Configuration

All scripts now use a unified configuration system. Instead of editing multiple files, you only need to modify `config.json`:

### config.json
This is the single source of truth for all configuration settings:

```json
{
  "ec2": {
    "host": "your-ec2-instance-ip-or-domain",
    "user": "ubuntu",
    "key_path": "~/path/to/your-key.pem"
  },
  "palworld": {
    "dir": "/opt/games/palword-server",
    "steamcmd_dir": "/opt/steamcmd",
    "remote_dir": "/opt/palword-control",
    "app_id": "2394010"
  }
}
```

### Configuration Files
- `config.json` - Single configuration file for all settings
- `config.py` - Multiplatform Python module for loading and validating config

## Scripts

### Deployment & Management Scripts
- `deploy_app.py` - Deploy the application to EC2
- `create_systemd_service.py` - Create systemd service
- `update_palworld.py` - Update PalWorld server
- `save_data.py` - Backup server save data and update GameUserSettings.ini
- `config_data.py` - Backup server configuration files

## Usage

1. Edit `config.json` with your EC2 instance details
2. Run the desired script using Python:
   - `python3 scripts/deploy_app.py`
   - `python3 scripts/save_data.py pull /path/to/saves`
   - `python3 scripts/save_data.py push /path/to/saves --backup`
   - `python3 scripts/config_data.py pull /path/to/configs`
   - `python3 scripts/config_data.py push /path/to/configs --backup`
   - `python3 scripts/update_palworld.py`
   - `python3 scripts/create_systemd_service.py`

### Data Management Examples

**Save Data:**
```bash
# Download saves to directory
python3 scripts/save_data.py pull /path/to/saves

# Upload saves from directory (automatically updates GameUserSettings.ini)
python3 scripts/save_data.py push /path/to/saves --backup
```

**Config Files:**
```bash
# Download config to directory
python3 scripts/config_data.py pull /path/to/configs

# Upload config from directory
python3 scripts/config_data.py push /path/to/configs --backup
```

### GameUserSettings.ini Auto-Update

The `save_data.py` script automatically updates the `DedicatedServerName` setting in `GameUserSettings.ini` when pushing save data. This ensures that:

1. The server configuration matches the uploaded save folder name
2. Players can connect to the correct save data
3. No manual editing of configuration files is required

The script will:
- Find the first save folder in the uploaded data
- Create a backup of the existing `GameUserSettings.ini`
- Update the `DedicatedServerName` setting to match the save folder name
- Verify the change was applied correctly

## Requirements

- Python 3.8 or higher
- SSH access to EC2 instance
- Valid EC2 key file 