import json
import logging
import traceback
import os
import winreg

class Settings:
    def __init__(self):
        self.firstPacketPattern = b'\x09\x08\x00'   # 09 08 00 04 98 5D F6 7E
        # Settings will be populated from settings.json
        pass

def auto_detect_palworld_exe():
    """
    Auto-detect Palworld server executable path by checking common Steam installation locations.
    Returns the path if found, None otherwise.
    """
    try:
        # Common Steam installation paths to check
        steam_paths = []
        
        # Try to get Steam installation path from registry
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam") as key:
                steam_install_path = winreg.QueryValueEx(key, "InstallPath")[0]
                steam_paths.append(steam_install_path)
        except (FileNotFoundError, OSError):
            pass
        
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam") as key:
                steam_install_path = winreg.QueryValueEx(key, "InstallPath")[0]
                steam_paths.append(steam_install_path)
        except (FileNotFoundError, OSError):
            pass
        
        # Add common default Steam paths
        common_paths = [
            r"C:\Program Files (x86)\Steam",
            r"C:\Program Files\Steam",
            r"D:\Steam",
            r"E:\Steam",
            r"F:\Steam"
        ]
        steam_paths.extend(common_paths)
        
        # Check for Palworld server executable in each Steam path
        for steam_path in steam_paths:
            if not steam_path or not os.path.exists(steam_path):
                continue
                
            # Check steamapps/common/PalServer directory
            palserver_path = os.path.join(steam_path, "steamapps", "common", "PalServer")
            
            # Possible executable locations within PalServer directory
            exe_candidates = [
                os.path.join(palserver_path, "Pal", "Binaries", "Win64", "PalServer-Win64-Shipping.exe"),
                os.path.join(palserver_path, "PalServer.exe"),
                os.path.join(palserver_path, "Pal", "Binaries", "Win64", "PalServer-Win64-Test-Cmd.exe")
            ]
            
            for exe_path in exe_candidates:
                if os.path.exists(exe_path):
                    logging.info(f"Auto-detected Palworld executable at: {exe_path}")
                    return exe_path
        
        # Also check SteamLibrary folders in other drives
        for drive in ['C:', 'D:', 'E:', 'F:', 'G:']:
            steamlibrary_path = os.path.join(drive, os.sep, "SteamLibrary", "steamapps", "common", "PalServer")
            exe_candidates = [
                os.path.join(steamlibrary_path, "Pal", "Binaries", "Win64", "PalServer-Win64-Shipping.exe"),
                os.path.join(steamlibrary_path, "PalServer.exe"),
                os.path.join(steamlibrary_path, "Pal", "Binaries", "Win64", "PalServer-Win64-Test-Cmd.exe")
            ]
            
            for exe_path in exe_candidates:
                if os.path.exists(exe_path):
                    logging.info(f"Auto-detected Palworld executable at: {exe_path}")
                    return exe_path
        
        logging.warning("Could not auto-detect Palworld executable path")
        return None
        
    except Exception as e:
        logging.error(f"Error during Palworld executable auto-detection: {e}")
        logging.error(traceback.format_exc())
        return None


Settings = Settings()


def readSettings(file_path):
    try:
        global Settings
        with open(file_path, 'r') as file:
            json_data = json.load(file)
            
            # Update settings in the instance if keys exist in the JSON file
            for key, value in json_data.items():
                if hasattr(Settings, key):
                    setattr(Settings, key, value)
                else:
                    setattr(Settings, key, value)
            
            # Auto-detect Palworld executable if not specified or file doesn't exist
            if not hasattr(Settings, 'palworldExePath') or not Settings.palworldExePath or not os.path.exists(Settings.palworldExePath):
                logging.info("Palworld executable path not specified or file not found, attempting auto-detection...")
                auto_detected_path = auto_detect_palworld_exe()
                if auto_detected_path:
                    Settings.palworldExePath = auto_detected_path
                    logging.info(f"Using auto-detected Palworld executable: {auto_detected_path}")
                else:
                    error_msg = ("CRITICAL ERROR: Could not locate Palworld server executable!\n"
                               "Please install Palworld Dedicated Server through Steam or specify the correct path.\n"
                               "Add 'palworldExePath' to your settings.json file with the full path to PalServer-Win64-Shipping.exe\n"
                               "Example: \"palworldExePath\": \"C:\\\\SteamLibrary\\\\steamapps\\\\common\\\\PalServer\\\\Pal\\\\Binaries\\\\Win64\\\\PalServer-Win64-Shipping.exe\"")
                    logging.error(error_msg)
                    raise FileNotFoundError(error_msg)
            
            print("Settings loaded successfully.")
    except FileNotFoundError:
        logging.info(f"Error: File {file_path} not found.")
    except json.JSONDecodeError:
        logging.warn(f"Error: Invalid JSON format in {file_path}.")
    except Exception as e:
        logging.error(f"Error from readSettings: {e}")
        logging.error(traceback.format_exc())


def updateSettings(options):
    try:
        global Settings
        # Update settings in the instance if keys exist in the options dictionary
        for key, value in options.items():
            if hasattr(Settings, key):
                setattr(Settings, key, value)
        logging.info("Settings updated successfully.")
    except Exception as e:
        logging.error(f"Error from updateSettings: {e}")
        logging.error(traceback.format_exc())
