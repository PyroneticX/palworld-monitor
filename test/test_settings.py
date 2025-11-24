"""
Tests for the Settings module.
"""
import pytest
import json
import tempfile
import os
import sys
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.settings import Settings, FIRST_PACKET_PATTERN


class TestSettings:
    """Test suite for Settings class."""

    def test_default_settings(self):
        """Test that default settings enable expected behaviors."""
        settings = Settings()
        
        # Test behavior: settings can be accessed via dictionary interface
        assert settings['os'] == 'windows'
        assert settings['palworldServerPort'] == 8211
        
        # Test behavior: critical defaults enable server functionality
        assert settings.protocol == "REST"  # Determines API client type
        assert settings.useWebServer is True  # Enables web interface
        assert settings.autoStart is True  # Enables auto-start feature
        assert settings.autoStop is True  # Enables auto-stop feature
        
        # Test behavior: security defaults are set
        assert settings.maxLoginAttempts == 5  # Prevents brute force
        assert settings.rateLimitEnabled is True  # Prevents abuse
        
        # Test behavior: first packet pattern is correctly defined
        assert settings.firstPacketPattern == FIRST_PACKET_PATTERN

    def test_getitem(self):
        """Test dictionary-like access to settings."""
        settings = Settings()
        assert settings['os'] == 'windows'
        assert settings['palworldServerPort'] == 8211

    def test_setitem(self):
        """Test setting values via dictionary-like access."""
        settings = Settings()
        settings['test_key'] = 'test_value'
        assert settings['test_key'] == 'test_value'
        assert settings.test_key == 'test_value'

    def test_read_settings_from_file(self):
        """Test reading settings from a JSON file."""
        settings = Settings()
        
        # Create a temporary settings file with required settings
        test_settings = {
            'os': 'linux',
            'palworldServerPort': 9999,
            'webUsername': 'testuser',
            'palworldServerExePath': '/path/to/server.exe',
            'palworldServerAdminPassword': 'admin123',
            'webPassword': 'webpass123',
            'sessionSecretKey': 'test_secret_key_123456789012345678901234567890'
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_settings, f)
            temp_path = f.name
        
        try:
            settings.readSettings(temp_path)
            assert settings.os == 'linux'
            assert settings.palworldServerPort == 9999
            assert settings.webUsername == 'testuser'
        finally:
            os.unlink(temp_path)

    def test_read_settings_file_not_found(self):
        """Test handling of missing settings file."""
        settings = Settings()
        original_os = settings.os
        
        # Set required settings in the settings dict to avoid validation error
        settings['palworldServerExePath'] = '/path/to/server.exe'
        settings['palworldServerAdminPassword'] = 'admin123'
        settings['webPassword'] = 'webpass123'
        settings['sessionSecretKey'] = 'test_secret_key_123456789012345678901234567890'
        
        # Should not raise an exception, just log
        settings.readSettings('nonexistent_file.json')
        
        # Settings should remain unchanged
        assert settings.os == original_os

    def test_read_settings_invalid_json(self):
        """Test handling of invalid JSON in settings file."""
        settings = Settings()
        original_port = settings.palworldServerPort
        
        # Set required settings in the settings dict to avoid validation error
        settings['palworldServerExePath'] = '/path/to/server.exe'
        settings['palworldServerAdminPassword'] = 'admin123'
        settings['webPassword'] = 'webpass123'
        settings['sessionSecretKey'] = 'test_secret_key_123456789012345678901234567890'
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{ invalid json }')
            temp_path = f.name
        
        try:
            settings.readSettings(temp_path)
            # Settings should remain unchanged
            assert settings.palworldServerPort == original_port
        finally:
            os.unlink(temp_path)

    def test_read_settings_partial_update(self):
        """Test that reading settings only updates provided keys."""
        settings = Settings()
        original_port = settings.palworldServerPort
        original_os = settings.os
        
        # Include required settings in partial update
        test_settings = {
            'os': 'linux',
            'palworldServerExePath': '/path/to/server.exe',
            'palworldServerAdminPassword': 'admin123',
            'webPassword': 'webpass123',
            'sessionSecretKey': 'test_secret_key_123456789012345678901234567890'
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_settings, f)
            temp_path = f.name
        
        try:
            settings.readSettings(temp_path)
            assert settings.os == 'linux'
            assert settings.palworldServerPort == original_port  # Should remain unchanged
        finally:
            os.unlink(temp_path)

    def test_get_git_hash_success(self):
        """Test getting git hash when git is available."""
        settings = Settings()
        
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = 'abc123def456\n'
            mock_run.return_value = mock_result
            
            hash_value = settings.get_git_hash()
            assert hash_value == 'abc123def456'
            mock_run.assert_called_once()

    def test_get_git_hash_failure(self):
        """Test getting git hash when git command fails."""
        settings = Settings()
        
        with patch('subprocess.run', side_effect=Exception("Git not found")):
            hash_value = settings.get_git_hash()
            assert hash_value is None

    def test_settings_validation_raises_on_none(self):
        """Test that readSettings raises ValueError when required settings are None."""
        settings = Settings()
        
        # Set a required setting to None
        settings.palworldServerAdminPassword = None
        
        test_settings = {
            'os': 'linux'
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_settings, f)
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError, match="REQUIRED"):
                settings.readSettings(temp_path)
        finally:
            os.unlink(temp_path)

    def test_first_packet_pattern(self):
        """Test that FIRST_PACKET_PATTERN is correctly defined."""
        assert isinstance(FIRST_PACKET_PATTERN, bytes)
        assert FIRST_PACKET_PATTERN == b'\x09\x08\x00'

