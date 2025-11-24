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
            assert settings.palworldServerPort == 9999
            assert settings.webUsername == 'testuser'
        finally:
            os.unlink(temp_path)

    def test_read_settings_file_not_found(self):
        """Test handling of missing settings file."""
        settings = Settings()
        original_port = settings.palworldServerPort
        
        # Set required settings in the settings dict to avoid validation error
        settings['palworldServerExePath'] = '/path/to/server.exe'
        settings['palworldServerAdminPassword'] = 'admin123'
        settings['webPassword'] = 'webpass123'
        settings['sessionSecretKey'] = 'test_secret_key_123456789012345678901234567890'
        
        # Should not raise an exception, just log
        settings.readSettings('nonexistent_file.json')
        
        # Settings should remain unchanged
        assert settings.palworldServerPort == original_port

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
        
        # Include required settings in partial update
        test_settings = {
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
            'palworldServerExePath': '/path/to/server.exe',
            'webPassword': 'webpass123'
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

    def test_auto_generate_session_secret_when_missing(self):
        """Test that sessionSecretKey is auto-generated when missing from settings.json."""
        settings = Settings()
        
        # Create a temporary settings file without sessionSecretKey
        test_settings = {
            'palworldServerExePath': '/path/to/server.exe',
            'palworldServerAdminPassword': 'admin123',
            'webPassword': 'webpass123'
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_settings, f)
            temp_path = f.name
        
        try:
            settings.readSettings(temp_path)
            
            # Verify that a session secret key was generated
            assert settings.sessionSecretKey is not None
            assert isinstance(settings.sessionSecretKey, str)
            assert len(settings.sessionSecretKey) == 64  # secrets.token_hex(32) produces 64 hex chars
            # Verify it's a valid hex string
            int(settings.sessionSecretKey, 16)  # Should not raise ValueError
            
            # Verify the key was saved back to the file
            with open(temp_path, 'r') as f:
                saved_settings = json.load(f)
            assert 'sessionSecretKey' in saved_settings
            assert saved_settings['sessionSecretKey'] == settings.sessionSecretKey
            assert len(saved_settings['sessionSecretKey']) == 64
        finally:
            os.unlink(temp_path)

    def test_auto_generate_session_secret_when_none(self):
        """Test that sessionSecretKey is auto-generated when explicitly set to None."""
        settings = Settings()
        
        # Create a temporary settings file with sessionSecretKey set to None
        test_settings = {
            'palworldServerExePath': '/path/to/server.exe',
            'palworldServerAdminPassword': 'admin123',
            'webPassword': 'webpass123',
            'sessionSecretKey': None
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_settings, f)
            temp_path = f.name
        
        try:
            settings.readSettings(temp_path)
            
            # Verify that a session secret key was generated
            assert settings.sessionSecretKey is not None
            assert isinstance(settings.sessionSecretKey, str)
            assert len(settings.sessionSecretKey) == 64
            
            # Verify the key was saved back to the file
            with open(temp_path, 'r') as f:
                saved_settings = json.load(f)
            assert saved_settings['sessionSecretKey'] == settings.sessionSecretKey
        finally:
            os.unlink(temp_path)

    def test_preserve_existing_session_secret(self):
        """Test that an existing sessionSecretKey is preserved."""
        settings = Settings()
        
        existing_secret = 'existing_secret_key_123456789012345678901234567890123456789012345678901234567890'
        test_settings = {
            'palworldServerExePath': '/path/to/server.exe',
            'palworldServerAdminPassword': 'admin123',
            'webPassword': 'webpass123',
            'sessionSecretKey': existing_secret
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_settings, f)
            temp_path = f.name
        
        try:
            settings.readSettings(temp_path)
            
            # Verify that the existing secret key was preserved
            assert settings.sessionSecretKey == existing_secret
            
            # Verify the file still has the original key
            with open(temp_path, 'r') as f:
                saved_settings = json.load(f)
            assert saved_settings['sessionSecretKey'] == existing_secret
        finally:
            os.unlink(temp_path)


