"""
Helper functions for setting up PalWorldController in tests.
"""
import platform
from unittest.mock import patch


def get_controller_patches(process_manager=None, player_manager=None, banlist_manager=None):
    """Get common patches for PalWorldController initialization.
    
    Args:
        process_manager: Mock process manager (default: None, will use default mock)
        player_manager: Mock player manager (default: None, will use default mock)
        banlist_manager: Mock banlist manager (default: None, will use default mock)
    
    Returns:
        list: List of patch context managers ready to use in 'with' statement
    """
    # Patch the correct process manager based on platform
    detected_os = platform.system()
    if detected_os.lower() == 'linux':
        process_manager_patch = patch('process_manager.LinuxProcessManager', return_value=process_manager)
    else:
        process_manager_patch = patch('process_manager.WindowsProcessManager', return_value=process_manager)
    
    patches = [
        patch('src.palworld_control.PlayerManager', return_value=player_manager),
        patch('src.palworld_control.BanlistManager', return_value=banlist_manager),
        process_manager_patch,
        patch('os.path.exists', return_value=False),
    ]
    return patches

