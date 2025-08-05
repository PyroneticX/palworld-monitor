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
- `config.sh` - Linux/macOS script that reads from config.json
- `config.bat` - Windows script that reads from config.json

## Scripts

### Deployment Scripts
- `deploy_app.sh` / `deploy_app.bat` - Deploy the application to EC2
- `create_systemd_service.sh` / `create_systemd_service.bat` - Create systemd service
- `update_palworld.sh` / `update_palworld.bat` - Update PalWorld server

### Data Management Scripts
- `save_data.sh` / `save_data.bat` - Backup server save data and update GameUserSettings.ini
- `config_data.sh` / `config_data.bat` - Backup server configuration files

## Usage

1. Edit `config.json` with your EC2 instance details
2. Run the appropriate script for your platform:
   - Linux/macOS: `./script_name.sh`
   - Windows: `script_name.bat`

### Data Management Examples

**Save Data:**
```bash
# Download saves to directory
./scripts/save_data.sh pull /path/to/saves

# Upload saves from directory (automatically updates GameUserSettings.ini)
./scripts/save_data.sh push /path/to/saves --backup
```

**Config Files:**
```bash
# Download config to directory
./scripts/config_data.sh pull /path/to/configs

# Upload config from directory
./scripts/config_data.sh push /path/to/configs --backup
```

### GameUserSettings.ini Auto-Update

The `save_data.sh` and `save_data.bat` scripts now automatically update the `DedicatedServerName` setting in `GameUserSettings.ini` when pushing save data. This ensures that:

1. The server configuration matches the uploaded save folder name
2. Players can connect to the correct save data
3. No manual editing of configuration files is required

The script will:
- Find the first save folder in the uploaded data
- Create a backup of the existing `GameUserSettings.ini`
- Update the `DedicatedServerName` setting to match the save folder name
- Verify the change was applied correctly

## Requirements

- Linux/macOS: `jq` (optional, falls back to grep/sed)
- Windows: PowerShell (built-in)
- SSH access to EC2 instance
- Valid EC2 key file 