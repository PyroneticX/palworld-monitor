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

import socket
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import timedelta
from settings import settings
from palworld_control import PalWorldController
from auth import User, LoginAttemptTracker, verify_password
import logging
import threading


class WebServer:
    def __init__(self, palworld_controller: PalWorldController):
        """
        Initialize the web server with a PalWorld controller instance.

        Args:
            palworld_controller: Instance of PalWorldController to handle server operations
        """
        self.palworld_controller = palworld_controller
        self.app = Flask(__name__, static_folder="static")
        self.ip = "Unknown"

        # Configure session
        self.app.secret_key = settings.sessionSecretKey
        self.app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(
            seconds=settings.sessionTimeout
        )

        # Initialize CSRF protection
        self.csrf = CSRFProtect(self.app)

        # Initialize rate limiter
        if settings.rateLimitEnabled:
            self.limiter = Limiter(
                app=self.app,
                key_func=get_remote_address,
                default_limits=[
                    f"{settings.rateLimitRequests} per {settings.rateLimitWindow} seconds"
                ],
            )

        # Initialize Flask-Login
        self.login_manager = LoginManager()
        self.login_manager.init_app(self.app)
        self.login_manager.login_view = "login"
        self.login_manager.login_message = "Please log in to access this page."

        # Initialize login attempt tracker
        self.login_tracker = LoginAttemptTracker(
            max_attempts=settings.maxLoginAttempts,
            lockout_duration=settings.lockoutDuration,
        )

        # Register user loader
        @self.login_manager.user_loader
        def load_user(user_id):
            if user_id == settings.webUsername:
                return User(user_id)
            return None

        # Register custom filters
        self._register_filters()

        # Register routes
        self._register_routes()

    def _register_routes(self):
        """Register Flask routes with the application."""

        @self.app.route("/login", methods=["GET", "POST"])
        def login():
            return self._handle_login()

        @self.app.route("/logout", methods=["POST"])
        @login_required
        def logout():
            logout_user()
            return redirect(url_for("login"))

        @self.app.route("/")
        @login_required
        def index():
            return self._handle_index()

        @self.app.route("/action", methods=["POST"])
        @login_required
        def web_server_action():
            return self._handle_action()

        @self.app.route("/kick", methods=["POST"])
        @login_required
        def kick_player():
            return self._handle_kick()

        @self.app.route("/ban", methods=["POST"])
        @login_required
        def ban_player():
            return self._handle_ban()

        @self.app.route("/unban", methods=["POST"])
        @login_required
        def unban_player():
            return self._handle_unban()

        @self.app.route("/banned", methods=["GET"])
        @login_required
        def get_banned_players():
            return self._handle_get_banned()

    def _register_filters(self):
        """Register custom Jinja2 filters."""

        @self.app.template_filter("datetime")
        def format_datetime(timestamp):
            """Format timestamp to readable datetime string."""
            try:
                if isinstance(timestamp, (int, float)):
                    from datetime import datetime

                    return datetime.fromtimestamp(timestamp).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                else:
                    return str(timestamp)
            except Exception:
                return str(timestamp)

    def _handle_login(self):
        """Handle login page and authentication."""
        ip_address = request.remote_addr

        # Check if locked out
        if self.login_tracker.is_locked_out(ip_address):
            remaining = self.login_tracker.get_lockout_time_remaining(ip_address)
            return render_template(
                "login.html",
                error=f"Too many failed attempts. Try again in {remaining} seconds.",
                locked_out=True,
            )

        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")
            remember = request.form.get("remember") == "yes"

            if verify_password(
                username, password, settings.webUsername, settings.webPassword
            ):
                user = User(username)
                login_user(
                    user,
                    remember=remember,
                    duration=timedelta(days=7 if remember else 0),
                )
                self.login_tracker.record_successful_login(ip_address)

                logging.info(f"Successful login from {ip_address} for user {username}")

                # Redirect to original page or home
                next_page = request.args.get("redirect", "/")
                return redirect(next_page)
            else:
                self.login_tracker.record_failed_attempt(ip_address)
                remaining = self.login_tracker.get_remaining_attempts(ip_address)

                logging.warning(
                    f"Failed login attempt from {ip_address} for user {username}"
                )

                error_msg = "Invalid credentials."
                warning_msg = None

                if remaining == 0:
                    error_msg = "Too many failed attempts. Account locked."
                elif remaining <= 2:
                    warning_msg = f"{remaining} attempts remaining before lockout"

                return render_template(
                    "login.html", error=error_msg, warning=warning_msg
                )

        return render_template("login.html")

    def _get_server_ip(self):
        """Get the server IP address."""
        try:
            ip = socket.gethostbyname(socket.gethostname())
            ip = ip + ":" + str(settings.palworldServerPort)
            return ip
        except Exception as e:
            logging.error(f"Error while getting server IP, {e}")
            return "unknown"

    def _get_player_data(self):
        """Get player data from the player manager."""
        player_manager = self.palworld_controller.get_player_manager()
        return {
            "players": player_manager.get_all_players(),
            "total_player_count": player_manager.get_total_player_count(),
        }

    def _handle_index(self):
        """Handle the main page route."""
        current_server_info = self.palworld_controller.get_current_server_info()
        if current_server_info is None:
            current_server_info = {"running": False, "playerCount": 0, "players": []}

        if settings.showServerIPAddress:
            current_server_info["IPAddress"] = self._get_server_ip()
        else:
            current_server_info["IPAddress"] = "Unknown"

        # Get persistent player data
        player_data = self._get_player_data()

        # Get theme from cookie, default to 'light' if not specified
        theme = request.cookies.get("theme", "light")
        if theme not in ["light", "dark"]:
            theme = "light"

        return render_template(
            "index.html",
            controlServerThroughWeb=settings.controlServerThroughWeb,
            showServerIPAddress=settings.showServerIPAddress,
            data=current_server_info,
            players=player_data["players"],
            total_player_count=player_data["total_player_count"],
            autoStopDelay=round(settings.autoStopDelay),
            updateInterval=settings.updateInterval,
            initialTheme=theme,
            git_hash=settings.get_git_hash(),
            current_user=current_user,
        )

    def _handle_action(self):
        """Handle server action requests."""
        action = request.form.get("action")

        logging.info(
            f"Server action '{action}' by {current_user.username} from {request.remote_addr}"
        )

        if action == "startServer":
            self.palworld_controller.start_server()
        elif action == "stopServer":
            self.palworld_controller.stop_server()

        current_server_info = self.palworld_controller.get_current_server_info()
        if current_server_info is None:
            current_server_info = {"running": False, "playerCount": 0, "players": []}

        # Get persistent player data
        player_data = self._get_player_data()

        return jsonify(
            data=current_server_info,
            players=player_data["players"],
            total_player_count=player_data["total_player_count"],
            autoStopDelay=round(settings.autoStopDelay),
            banned_players=self.palworld_controller.get_banned_players(),
        )

    def _handle_kick(self):
        """Handle player kick requests."""
        steam_id = request.form.get("steam_id")

        if not steam_id:
            return jsonify(success=False, message="Steam ID is required"), 400

        logging.info(
            f"Kick player {steam_id} by {current_user.username} from {request.remote_addr}"
        )

        # Attempt to kick the player
        success = self.palworld_controller.kick_player(steam_id)

        # Get updated server info and player data
        current_server_info = self.palworld_controller.get_current_server_info()
        if current_server_info is None:
            current_server_info = {"running": False, "playerCount": 0, "players": []}

        player_data = self._get_player_data()

        return jsonify(
            success=success,
            message=f"Player {'kicked successfully' if success else 'kick failed'}",
            data=current_server_info,
            players=player_data["players"],
            total_player_count=player_data["total_player_count"],
        )

    def _handle_ban(self):
        """Handle player ban requests."""
        steam_id = request.form.get("steam_id")

        if not steam_id:
            return jsonify(success=False, message="Steam ID is required"), 400

        logging.info(
            f"Ban player {steam_id} by {current_user.username} from {request.remote_addr}"
        )

        # Attempt to ban the player
        success = self.palworld_controller.ban_player(steam_id)

        # Get updated server info and player data
        current_server_info = self.palworld_controller.get_current_server_info()
        if current_server_info is None:
            current_server_info = {"running": False, "playerCount": 0, "players": []}

        player_data = self._get_player_data()

        return jsonify(
            success=success,
            message=f"Player {'banned successfully' if success else 'ban failed'}",
            data=current_server_info,
            players=player_data["players"],
            total_player_count=player_data["total_player_count"],
            banned_players=self.palworld_controller.get_banned_players(),
        )

    def _handle_unban(self):
        """Handle player unban requests."""
        steam_id = request.form.get("steam_id")

        if not steam_id:
            return jsonify(success=False, message="Steam ID is required"), 400

        logging.info(
            f"Unban player {steam_id} by {current_user.username} from {request.remote_addr}"
        )

        # Attempt to unban the player
        success = self.palworld_controller.unban_player(steam_id)

        # Get updated banned players list
        banned_players = self.palworld_controller.get_banned_players()

        return jsonify(
            success=success,
            message=f"Player {'unbanned successfully' if success else 'unban failed'}",
            banned_players=banned_players,
        )

    def _handle_get_banned(self):
        """Handle request to get list of banned players."""
        banned_players = self.palworld_controller.get_banned_players()
        return jsonify(success=True, banned_players=banned_players)

    def run(self):
        """Start the web server in a separate thread."""
        # Log web server start with host and port information
        logging.info(
            f"Web server start - listening on 0.0.0.0:{settings.webServerPort}"
        )

        def start_flask():
            # Suppress Flask development server INFO messages by configuring werkzeug logger
            import logging as flask_logging

            flask_logging.getLogger("werkzeug").setLevel(flask_logging.ERROR)

            try:
                self.app.run(host="0.0.0.0", port=settings.webServerPort, debug=False)
            except Exception as e:
                # Preserve existing ERROR level logging for web server failures
                logging.error(f"Web server failed to start: {e}")
                raise

        thread = threading.Thread(target=start_flask)
        thread.daemon = True  # Make thread daemon so it exits when main process exits
        thread.start()
