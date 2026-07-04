# Copyright (c) 2024 Nomomo
# Copyright (c) 2026 Kevin Perez - Modified work
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

"""
Authentication module for Palworld server control web interface.
Handles user authentication, session management, and login attempt tracking.
"""

from flask_login import UserMixin
from datetime import datetime, timedelta
from typing import Dict, Optional
import logging


class User(UserMixin):
    """User class for Flask-Login authentication."""

    def __init__(self, username: str):
        """Initialize a user instance.

        Args:
            username: The username for this user
        """
        self.id = username
        self.username = username

    def get_id(self):
        """Return the user ID for Flask-Login."""
        return self.id


class LoginAttemptTracker:
    """Track failed login attempts and implement account lockout.
    Stores attempts in memory (resets on application restart).
    """

    def __init__(self, max_attempts: int = 5, lockout_duration: int = 300):
        """Initialize the login attempt tracker.

        Args:
            max_attempts: Maximum failed attempts before lockout
            lockout_duration: Lockout duration in seconds
        """
        self.max_attempts = max_attempts
        self.lockout_duration = lockout_duration
        self.attempts: Dict[str, list] = {}  # IP -> list of attempt timestamps
        self.lockouts: Dict[str, datetime] = {}  # IP -> lockout expiry time

    def is_locked_out(self, ip_address: str) -> bool:
        """Check if an IP address is currently locked out."""
        if ip_address in self.lockouts:
            if datetime.now() < self.lockouts[ip_address]:
                return True
            else:
                del self.lockouts[ip_address]
                self.attempts.pop(ip_address, None)
        return False

    def record_failed_attempt(self, ip_address: str) -> None:
        """Record a failed login attempt."""
        now = datetime.now()
        self.attempts.setdefault(ip_address, []).append(now)
        self.attempts[ip_address] = [
            a for a in self.attempts[ip_address] if a > now - timedelta(seconds=self.lockout_duration)
        ]

        if len(self.attempts[ip_address]) >= self.max_attempts:
            self.lockouts[ip_address] = now + timedelta(seconds=self.lockout_duration)
            logging.warning(
                f"IP {ip_address} locked out after {self.max_attempts} failed login attempts"
            )

    def record_successful_login(self, ip_address: str) -> None:
        """Record a successful login and clear failed attempts."""
        self.attempts.pop(ip_address, None)
        self.lockouts.pop(ip_address, None)

    def get_remaining_attempts(self, ip_address: str) -> int:
        """Get the number of remaining login attempts before lockout."""
        if self.is_locked_out(ip_address):
            return 0
        return max(0, self.max_attempts - len(self.attempts.get(ip_address, [])))

    def get_lockout_time_remaining(self, ip_address: str) -> Optional[int]:
        """Get the remaining lockout time in seconds.

        Args:
            ip_address: The IP address to check

        Returns:
            Remaining seconds if locked out, None otherwise
        """
        if ip_address in self.lockouts:
            remaining = (self.lockouts[ip_address] - datetime.now()).total_seconds()
            if remaining > 0:
                return int(remaining)
        return None


def verify_password(
    username: str, password: str, expected_username: str, expected_password: str
) -> bool:
    """Verify username and password against expected credentials.

    Args:
        username: Provided username
        password: Provided password
        expected_username: Expected username from src.settings
        expected_password: Expected password from src.settings

    Returns:
        True if credentials match, False otherwise
    """
    return username == expected_username and password == expected_password
