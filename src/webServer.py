import socket
from flask import Flask, render_template, request, jsonify
from settings import Settings
from palWorldControl import PalWorldController
from autoStop import STOP_SERVER_VARIABLES
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
        self.app = Flask(__name__, static_folder='static')
        self.ip = "Unknown"
        
        # Register custom filters
        self._register_filters()
        
        # Register routes
        self._register_routes()
    
    def _register_routes(self):
        """Register Flask routes with the application."""
        
        @self.app.route("/")
        def index():
            return self._handle_index()
        
        @self.app.route("/action", methods=["POST"])
        def web_server_action():
            return self._handle_action()
    
    def _register_filters(self):
        """Register custom Jinja2 filters."""
        
        @self.app.template_filter('datetime')
        def format_datetime(timestamp):
            """Format timestamp to readable datetime string."""
            try:
                if isinstance(timestamp, (int, float)):
                    from datetime import datetime
                    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                else:
                    return str(timestamp)
            except:
                return str(timestamp)
    
    def _get_server_ip(self):
        """Get the server IP address."""
        try:
            ip = socket.gethostbyname(socket.gethostname())
            ip = ip + ":" + str(Settings.palworldServerPort)
            return ip
        except Exception as e:
            logging.error(f"Error while getting server IP, {e}")
            return "unknown"
    
    def _handle_index(self):
        """Handle the main page route."""
        current_server_info = self.palworld_controller.update_current_server_info()
        if current_server_info is None:
            current_server_info = {"running": False, "playerCount": 0, "players": []}
        
        if Settings.showServerIPAddress:
            current_server_info["IPAddress"] = self._get_server_ip()
        else:
            current_server_info["IPAddress"] = "Unknown"
        
        # Get persistent player data
        all_players = self.palworld_controller.get_all_players()
        online_players = self.palworld_controller.get_online_players()
        offline_players = self.palworld_controller.get_offline_players()
        total_player_count = self.palworld_controller.get_total_player_count()
        
        # Get theme from URL parameter (optional, JavaScript handles default)
        theme = request.args.get('theme')

        # Get auto-stop variables if available
        is_running_stopwatch = round(STOP_SERVER_VARIABLES["isRunningStopwatchToStopServer"])
        left_time_to_stop = round(STOP_SERVER_VARIABLES["leftTimeToStopServer"])

        return render_template(
            "index.html",
            showAction=Settings.showAction,
            showServerOnBtn=Settings.showServerOnBtn,
            showServerOffBtn=Settings.showServerOffBtn,
            showUpdateServerStatusBtn=Settings.showUpdateServerStatusBtn,
            showServerIPAddress=Settings.showServerIPAddress,
            data=current_server_info,
            all_players=all_players,
            online_players=online_players,
            offline_players=offline_players,
            total_player_count=total_player_count,
            ServerAutoStopSeconds=round(Settings.ServerAutoStopSeconds),
            isRunningStopwatchToStopServer=is_running_stopwatch,
            leftTimeToStopServer=left_time_to_stop,
            theme=theme
        )
    
    def _handle_action(self):
        """Handle server action requests."""
        action = request.form.get("action")

        current_server_info = self.palworld_controller.update_current_server_info()
        if current_server_info is None:
            current_server_info = {"running": False, "playerCount": 0, "players": []}

        if action == "startServer":
            self.palworld_controller.start_server()
        elif action == "stopServer":
            self.palworld_controller.stop_server(1)
        #elif action == "getStatus":
            # do nothing

        # Get persistent player data
        all_players = self.palworld_controller.get_all_players()
        online_players = self.palworld_controller.get_online_players()
        offline_players = self.palworld_controller.get_offline_players()
        total_player_count = self.palworld_controller.get_total_player_count()

        is_running_stopwatch = round(STOP_SERVER_VARIABLES["isRunningStopwatchToStopServer"])
        left_time_to_stop = round(STOP_SERVER_VARIABLES["leftTimeToStopServer"])

        return jsonify(
            data=current_server_info,
            all_players=all_players,
            online_players=online_players,
            offline_players=offline_players,
            total_player_count=total_player_count,
            ServerAutoStopSeconds=round(Settings.ServerAutoStopSeconds),
            isRunningStopwatchToStopServer=is_running_stopwatch,
            leftTimeToStopServer=left_time_to_stop
        )
    
    def run(self):
        """Start the web server in a separate thread."""
        logging.info("Start webserver")
        
        def start_flask():
            # Set Flask log level to only show errors
            import logging as flask_logging
            flask_logging.getLogger('werkzeug').setLevel(flask_logging.ERROR)
            self.app.run(host=Settings.webServerHost, port=Settings.webServerPort, debug=False)
        
        thread = threading.Thread(target=start_flask)
        thread.daemon = True  # Make thread daemon so it exits when main process exits
        thread.start()
