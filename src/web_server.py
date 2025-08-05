import socket
from flask import Flask, render_template, request, jsonify, Response
from functools import wraps
from settings import settings
from palworld_control import PalWorldController
import logging
import threading


def check_auth(username, password):
    """Check if username and password match the expected credentials."""
    return username == 'admin' and password == settings.palworldAdminPassword


def authenticate():
    """Send a 401 response that enables basic auth."""
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})


def requires_auth(f):
    """Decorator to require basic authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


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
        @requires_auth
        def index():
            return self._handle_index()
        
        @self.app.route("/action", methods=["POST"])
        @requires_auth
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
            ip = ip + ":" + str(settings.palworldServerPort)
            return ip
        except Exception as e:
            logging.error(f"Error while getting server IP, {e}")
            return "unknown"
    
    def _get_player_data(self):
        """Get player data from the player manager."""
        player_manager = self.palworld_controller.get_player_manager()
        return {
            'all_players': player_manager.get_all_players(),
            'online_players': player_manager.get_online_players(),
            'offline_players': player_manager.get_offline_players(),
            'total_player_count': player_manager.get_total_player_count()
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
        
        # Get theme from URL parameter (optional, JavaScript handles default)
        theme = request.args.get('theme')

        return render_template(
            "index.html",
            controlServerThroughWeb=settings.controlServerThroughWeb,
            showServerIPAddress=settings.showServerIPAddress,
            data=current_server_info,
            all_players=player_data['all_players'],
            online_players=player_data['online_players'],
            offline_players=player_data['offline_players'],
            total_player_count=player_data['total_player_count'],
            autoStopDelay=round(settings.autoStopDelay),
            updateInterval=settings.updateInterval,
            theme=theme
        )
    
    def _handle_action(self):
        """Handle server action requests."""
        action = request.form.get("action")

        if action == "startServer":
            self.palworld_controller.start_server()
        elif action == "stopServer":
            self.palworld_controller.stop_server()
        #elif action == "getStatus":
            # Just refresh the page with current server info (no server update triggered)

        current_server_info = self.palworld_controller.get_current_server_info()
        if current_server_info is None:
            current_server_info = {"running": False, "playerCount": 0, "players": []}

        # Get persistent player data
        player_data = self._get_player_data()

        return jsonify(
            data=current_server_info,
            all_players=player_data['all_players'],
            online_players=player_data['online_players'],
            offline_players=player_data['offline_players'],
            total_player_count=player_data['total_player_count'],
            autoStopDelay=round(settings.autoStopDelay)
        )
    
    def run(self):
        """Start the web server in a separate thread."""
        # Log web server start with host and port information
        logging.info(f"Web server start - listening on {settings.webServerHost}:{settings.webServerPort}")
        
        def start_flask():
            # Suppress Flask development server INFO messages by configuring werkzeug logger
            import logging as flask_logging
            flask_logging.getLogger('werkzeug').setLevel(flask_logging.ERROR)
            
            try:
                self.app.run(host=settings.webServerHost, port=settings.webServerPort, debug=False)
            except Exception as e:
                # Preserve existing ERROR level logging for web server failures
                logging.error(f"Web server failed to start: {e}")
                raise
        
        thread = threading.Thread(target=start_flask)
        thread.daemon = True  # Make thread daemon so it exits when main process exits
        thread.start()
