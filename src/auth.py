# Copyright (c) 2024 Nomomo
# Copyright (c) 2024 Kevin Perez - Modified work
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
        """
        Initialize a user instance.

        Args:
            username: The username for this user
        """
        self.id = username
        self.username = username

    def get_id(self):
        """Return the user ID for Flask-Login."""
        return self.id


class LoginAttemptTracker:
    """
    Track failed login attempts and implement account lockout.
    Stores attempts in memory (resets on application restart).
    """

    def __init__(self, max_attempts: int = 5, lockout_duration: int = 300):
        """
        Initialize the login attempt tracker.

        Args:
            max_attempts: Maximum failed attempts before lockout
            lockout_duration: Lockout duration in seconds
        """
        self.max_attempts = max_attempts
        self.lockout_duration = lockout_duration
        self.attempts: Dict[str, list] = {}  # IP -> list of attempt timestamps
        self.lockouts: Dict[str, datetime] = {}  # IP -> lockout expiry time

    def is_locked_out(self, ip_address: str) -> bool:
        """
        Check if an IP address is currently locked out.

        Args:
            ip_address: The IP address to check

        Returns:
            True if locked out, False otherwise
        """
        if ip_address in self.lockouts:
            if datetime.now() < self.lockouts[ip_address]:
                return True
            else:
                # Lockout expired, clean up
                del self.lockouts[ip_address]
                if ip_address in self.attempts:
                    del self.attempts[ip_address]
        return False

    def record_failed_attempt(self, ip_address: str) -> None:
        """
        Record a failed login attempt.

        Args:
            ip_address: The IP address of the failed attempt
        """
        now = datetime.now()

        # Initialize attempts list if needed
        if ip_address not in self.attempts:
            self.attempts[ip_address] = []

        # Add this attempt
        self.attempts[ip_address].append(now)

        # Clean up old attempts (older than lockout duration)
        cutoff = now - timedelta(seconds=self.lockout_duration)
        self.attempts[ip_address] = [
            attempt for attempt in self.attempts[ip_address] if attempt > cutoff
        ]

        # Check if we should lock out
        if len(self.attempts[ip_address]) >= self.max_attempts:
            self.lockouts[ip_address] = now + timedelta(seconds=self.lockout_duration)
            logging.warning(
                f"IP {ip_address} locked out after {self.max_attempts} failed login attempts"
            )

    def record_successful_login(self, ip_address: str) -> None:
        """
        Record a successful login and clear failed attempts.

        Args:
            ip_address: The IP address of the successful login
        """
        if ip_address in self.attempts:
            del self.attempts[ip_address]
        if ip_address in self.lockouts:
            del self.lockouts[ip_address]

    def get_remaining_attempts(self, ip_address: str) -> int:
        """
        Get the number of remaining login attempts before lockout.

        Args:
            ip_address: The IP address to check

        Returns:
            Number of remaining attempts
        """
        if self.is_locked_out(ip_address):
            return 0

        if ip_address not in self.attempts:
            return self.max_attempts

        # Clean up old attempts
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.lockout_duration)
        self.attempts[ip_address] = [
            attempt for attempt in self.attempts[ip_address] if attempt > cutoff
        ]

        return max(0, self.max_attempts - len(self.attempts[ip_address]))

    def get_lockout_time_remaining(self, ip_address: str) -> Optional[int]:
        """
        Get the remaining lockout time in seconds.

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
    """
    Verify username and password against expected credentials.

    Args:
        username: Provided username
        password: Provided password
        expected_username: Expected username from settings
        expected_password: Expected password from settings

    Returns:
        True if credentials match, False otherwise
    """
    return username == expected_username and password == expected_password
