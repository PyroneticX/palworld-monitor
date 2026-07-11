# Copyright (c) 2024 Nomomo
# Copyright (c) 2026 Kevin Perez - Modified work

"""Authentication for the web admin interface."""

import logging
import time

from flask_login import UserMixin


class User(UserMixin):
    """Minimal user for Flask-Login."""

    def __init__(self, username):
        self.id = username
        self.username = username


class LoginAttemptTracker:
    """Track failed login attempts per IP with lockout."""

    def __init__(self, max_attempts=5, lockout_duration=300):
        self.max_attempts = max_attempts
        self.lockout_duration = lockout_duration
        self._failures = {}  # ip -> (count, first_failure_time)

    def is_locked_out(self, ip):
        entry = self._failures.get(ip)
        if entry is None:
            return False
        count, first = entry
        if time.time() - first > self.lockout_duration:
            del self._failures[ip]
            return False
        return count >= self.max_attempts

    def record_failed_attempt(self, ip):
        now = time.time()
        entry = self._failures.get(ip)
        if entry is None or now - entry[1] > self.lockout_duration:
            self._failures[ip] = (1, now)
        else:
            self._failures[ip] = (entry[0] + 1, entry[1])

        count, _first = self._failures[ip]
        if count >= self.max_attempts:
            logging.warning(
                f"IP {ip} locked out after {self.max_attempts} failed login attempts"
            )

    def record_successful_login(self, ip):
        self._failures.pop(ip, None)

    def get_remaining_attempts(self, ip):
        if self.is_locked_out(ip):
            return 0
        entry = self._failures.get(ip)
        if entry is None:
            return self.max_attempts
        return max(0, self.max_attempts - entry[0])

    def get_lockout_time_remaining(self, ip):
        entry = self._failures.get(ip)
        if entry is None:
            return None
        count, first = entry
        if count < self.max_attempts:
            return None
        remaining = self.lockout_duration - (time.time() - first)
        return int(remaining) if remaining > 0 else 0
