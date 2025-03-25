import os
import signal
import time
from binascii import b2a_hex
from os import urandom
from service_logging import log

from flask import Response, abort, jsonify, make_response, request, Flask

from constants import DEFAULT_SESSION_TTL
from relay_board import RelayBoard


class HVACSimServer:
    """HVAC Simulator server"""
    def __init__(self):
        self.app = None
        self._success_response = {}
        self.session_id = None  # Initializing None session_id, ie. no session in progress.
        self.last_event_time = 0  # Last event does not exist before server is launched
        self.valid_config_commands = {}
        self.app = Flask(__name__)  # Flask server initializing
        self.init_server()

    def set_valid_config_commands(self):
        """Initialize valid config commands via rb.configurations. This needs to be in it's own helper function as each
        state defined is dependent on environment variables (e.g. has_pek), which in theory can change along with
        configurations sent into start_session. I.e. default configurations initialized above do not necessarily reflect
        the state set in start_session (hence why it is called there as well as in __init__)."""
        self.valid_config_commands = {  # Valid config commands found in relay_board.py
            "CONFIG_POWER": self.rb.configurations.CONFIG_POWER,

            "CONFIG_FAN": self.rb.configurations.CONFIG_FAN,
            "CONFIG_FAN_2_STAGE": self.rb.configurations.CONFIG_FAN_2_STAGE,
            "CONFIG_FAN_3_STAGE": self.rb.configurations.CONFIG_FAN_3_STAGE,
            "CONFIG_FAN_ACC": self.rb.configurations.CONFIG_FAN_ACC,
            "CONFIG_FAN_2_STAGE_ACC": self.rb.configurations.CONFIG_FAN_2_STAGE_ACC,
            "CONFIG_FAN_3_STAGE_ACC": self.rb.configurations.CONFIG_FAN_3_STAGE_ACC,

            "CONFIG_FAN_ACC_2_STAGE": self.rb.configurations.CONFIG_FAN_ACC_2_STAGE,
            "CONFIG_FAN_2_STAGE_ACC_2_STAGE": self.rb.configurations.CONFIG_FAN_2_STAGE_ACC_2_STAGE,
            "CONFIG_FAN_3_STAGE_ACC_2_STAGE": self.rb.configurations.CONFIG_FAN_3_STAGE_ACC_2_STAGE,

            "CONFIG_BO_1_STAGE": self.rb.configurations.CONFIG_BO_1_STAGE,
            "CONFIG_BO_2_STAGE": self.rb.configurations.CONFIG_BO_2_STAGE,
            "CONFIG_BO_1_STAGE_ACC": self.rb.configurations.CONFIG_BO_1_STAGE_ACC,
            "CONFIG_BO_2_STAGE_ACC": self.rb.configurations.CONFIG_BO_2_STAGE_ACC,
            "CONFIG_BO_1_STAGE_ACC_2_STAGE": self.rb.configurations.CONFIG_BO_1_STAGE_ACC_2_STAGE,
            "CONFIG_BO_2_STAGE_ACC_2_STAGE": self.rb.configurations.CONFIG_BO_2_STAGE_ACC_2_STAGE,

            "CONFIG_FN_1_STAGE": self.rb.configurations.CONFIG_FN_1_STAGE,
            "CONFIG_FN_1_STAGE_FAN_2_STAGE": self.rb.configurations.CONFIG_FN_1_STAGE_FAN_2_STAGE,
            "CONFIG_FN_1_STAGE_FAN_3_STAGE": self.rb.configurations.CONFIG_FN_1_STAGE_FAN_3_STAGE,
            "CONFIG_FN_1_STAGE_ACC": self.rb.configurations.CONFIG_FN_1_STAGE_ACC,
            "CONFIG_FN_1_STAGE_FAN_2_STAGE_ACC": self.rb.configurations.CONFIG_FN_1_STAGE_FAN_2_STAGE_ACC,
            "CONFIG_FN_1_STAGE_FAN_3_STAGE_ACC": self.rb.configurations.CONFIG_FN_1_STAGE_FAN_3_STAGE_ACC,
            "CONFIG_FN_1_STAGE_ACC_2_STAGE": self.rb.configurations.CONFIG_FN_1_STAGE_ACC_2_STAGE,
            "CONFIG_FN_1_STAGE_FAN_2_STAGE_ACC_2_STAGE":
                self.rb.configurations.CONFIG_FN_1_STAGE_FAN_2_STAGE_ACC_2_STAGE,
            "CONFIG_FN_1_STAGE_FAN_3_STAGE_ACC_2_STAGE":
                self.rb.configurations.CONFIG_FN_1_STAGE_FAN_3_STAGE_ACC_2_STAGE,

            "CONFIG_AC_1_STAGE": self.rb.configurations.CONFIG_AC_1_STAGE,
            "CONFIG_AC_1_STAGE_FAN_2_STAGE": self.rb.configurations.CONFIG_AC_1_STAGE_FAN_2_STAGE,
            "CONFIG_AC_1_STAGE_FAN_3_STAGE": self.rb.configurations.CONFIG_AC_1_STAGE_FAN_3_STAGE,
            "CONFIG_AC_1_STAGE_ACC": self.rb.configurations.CONFIG_AC_1_STAGE_ACC,
            "CONFIG_AC_1_STAGE_FAN_2_STAGE_ACC": self.rb.configurations.CONFIG_AC_1_STAGE_FAN_2_STAGE_ACC,
            "CONFIG_AC_1_STAGE_FAN_3_STAGE_ACC": self.rb.configurations.CONFIG_AC_1_STAGE_FAN_3_STAGE_ACC,
            "CONFIG_AC_1_STAGE_ACC_2_STAGE": self.rb.configurations.CONFIG_AC_1_STAGE_ACC_2_STAGE,
            "CONFIG_AC_1_STAGE_FAN_2_STAGE_ACC_2_STAGE":
                self.rb.configurations.CONFIG_AC_1_STAGE_FAN_2_STAGE_ACC_2_STAGE,
            "CONFIG_AC_1_STAGE_FAN_3_STAGE_ACC_2_STAGE":
                self.rb.configurations.CONFIG_AC_1_STAGE_FAN_3_STAGE_ACC_2_STAGE,

            "CONFIG_BO_1_STAGE_AC_1_STAGE": self.rb.configurations.CONFIG_BO_1_STAGE_AC_1_STAGE,
            "CONFIG_BO_1_STAGE_AC_1_STAGE_FAN_2_STAGE": self.rb.configurations.CONFIG_BO_1_STAGE_AC_1_STAGE_FAN_2_STAGE,
            "CONFIG_BO_1_STAGE_AC_1_STAGE_FAN_3_STAGE": self.rb.configurations.CONFIG_BO_1_STAGE_AC_1_STAGE_FAN_3_STAGE,
            "CONFIG_BO_1_STAGE_AC_1_STAGE_ACC": self.rb.configurations.CONFIG_BO_1_STAGE_AC_1_STAGE_ACC,
            "CONFIG_BO_1_STAGE_AC_1_STAGE_FAN_2_STAGE_ACC":
                self.rb.configurations.CONFIG_BO_1_STAGE_AC_1_STAGE_FAN_2_STAGE_ACC,
            "CONFIG_BO_1_STAGE_AC_1_STAGE_FAN_3_STAGE_ACC":
                self.rb.configurations.CONFIG_BO_1_STAGE_AC_1_STAGE_FAN_3_STAGE_ACC,
            "CONFIG_BO_1_STAGE_AC_1_STAGE_ACC_2_STAGE": self.rb.configurations.CONFIG_BO_1_STAGE_AC_1_STAGE_ACC_2_STAGE,

            "CONFIG_FN_1_STAGE_AC_1_STAGE": self.rb.configurations.CONFIG_FN_1_STAGE_AC_1_STAGE,
            "CONFIG_FN_1_STAGE_AC_1_STAGE_FAN_2_STAGE": self.rb.configurations.CONFIG_FN_1_STAGE_AC_1_STAGE_FAN_2_STAGE,
            "CONFIG_FN_1_STAGE_AC_1_STAGE_FAN_3_STAGE": self.rb.configurations.CONFIG_FN_1_STAGE_AC_1_STAGE_FAN_3_STAGE,
            "CONFIG_FN_1_STAGE_AC_1_STAGE_ACC": self.rb.configurations.CONFIG_FN_1_STAGE_AC_1_STAGE_ACC,
            "CONFIG_FN_1_STAGE_AC_1_STAGE_PEK_ACC": self.rb.configurations.CONFIG_FN_1_STAGE_AC_1_STAGE_PEK_ACC,
            "CONFIG_FN_1_STAGE_AC_1_STAGE_FAN_2_STAGE_ACC":
                self.rb.configurations.CONFIG_FN_1_STAGE_AC_1_STAGE_FAN_2_STAGE_ACC,
            "CONFIG_FN_1_STAGE_AC_1_STAGE_FAN_3_STAGE_ACC":
                self.rb.configurations.CONFIG_FN_1_STAGE_AC_1_STAGE_FAN_3_STAGE_ACC,
            "CONFIG_FN_1_STAGE_AC_1_STAGE_ACC_2_STAGE": self.rb.configurations.CONFIG_FN_1_STAGE_AC_1_STAGE_ACC_2_STAGE,
            "CONFIG_FN_1_STAGE_AC_1_STAGE_FAN_2_STAGE_ACC_2_STAGE":
                self.rb.configurations.CONFIG_FN_1_STAGE_AC_1_STAGE_FAN_2_STAGE_ACC_2_STAGE,
            "CONFIG_FN_1_STAGE_AC_1_STAGE_FAN_3_STAGE_ACC_2_STAGE":
                self.rb.configurations.CONFIG_FN_1_STAGE_AC_1_STAGE_FAN_3_STAGE_ACC_2_STAGE,

            "CONFIG_FN_2_STAGE": self.rb.configurations.CONFIG_FN_2_STAGE,
            "CONFIG_FN_2_STAGE_FAN_2_STAGE": self.rb.configurations.CONFIG_FN_2_STAGE_FAN_2_STAGE,
            "CONFIG_FN_2_STAGE_ACC": self.rb.configurations.CONFIG_FN_2_STAGE_ACC,
            "CONFIG_FN_2_STAGE_FAN_2_STAGE_ACC": self.rb.configurations.CONFIG_FN_2_STAGE_FAN_2_STAGE_ACC,
            "CONFIG_FN_2_STAGE_ACC_2_STAGE": self.rb.configurations.CONFIG_FN_2_STAGE_ACC_2_STAGE,

            "CONFIG_AC_2_STAGE": self.rb.configurations.CONFIG_AC_2_STAGE,
            "CONFIG_AC_2_STAGE_ACC": self.rb.configurations.CONFIG_AC_2_STAGE_ACC,
            "CONFIG_AC_2_STAGE_ACC_2_STAGE": self.rb.configurations.CONFIG_AC_2_STAGE_ACC_2_STAGE,

            "CONFIG_HPCOOL_1_STAGE": self.rb.configurations.CONFIG_HPCOOL_1_STAGE,
            "CONFIG_HPCOOL_1_STAGE_FAN_2_STAGE": self.rb.configurations.CONFIG_HPCOOL_1_STAGE_FAN_2_STAGE,
            "CONFIG_HPCOOL_1_STAGE_FAN_3_STAGE": self.rb.configurations.CONFIG_HPCOOL_1_STAGE_FAN_3_STAGE,
            "CONFIG_HPCOOL_1_STAGE_ACC": self.rb.configurations.CONFIG_HPCOOL_1_STAGE_ACC,
            "CONFIG_HPCOOL_1_STAGE_FAN_2_STAGE_ACC": self.rb.configurations.CONFIG_HPCOOL_1_STAGE_FAN_2_STAGE_ACC,
            "CONFIG_HPCOOL_1_STAGE_FAN_3_STAGE_ACC": self.rb.configurations.CONFIG_HPCOOL_1_STAGE_FAN_3_STAGE_ACC,
            "CONFIG_HPCOOL_1_STAGE_ACC_2_STAGE": self.rb.configurations.CONFIG_HPCOOL_1_STAGE_ACC_2_STAGE,
            "CONFIG_HPCOOL_1_STAGE_FAN_3_STAGE_ACC_2_STAGE": self.rb.configurations.CONFIG_HPCOOL_1_STAGE_FAN_3_STAGE_ACC_2_STAGE,

            "CONFIG_HPHEAT_1_STAGE": self.rb.configurations.CONFIG_HPHEAT_1_STAGE,
            "CONFIG_HPHEAT_1_STAGE_FAN_2_STAGE": self.rb.configurations.CONFIG_HPHEAT_1_STAGE_FAN_2_STAGE,
            "CONFIG_HPHEAT_1_STAGE_FAN_3_STAGE": self.rb.configurations.CONFIG_HPHEAT_1_STAGE_FAN_3_STAGE,
            "CONFIG_HPHEAT_1_STAGE_ACC": self.rb.configurations.CONFIG_HPHEAT_1_STAGE_ACC,
            "CONFIG_HPHEAT_1_STAGE_FAN_2_STAGE_ACC": self.rb.configurations.CONFIG_HPHEAT_1_STAGE_FAN_2_STAGE_ACC,
            "CONFIG_HPHEAT_1_STAGE_FAN_3_STAGE_ACC": self.rb.configurations.CONFIG_HPHEAT_1_STAGE_FAN_3_STAGE_ACC,
            "CONFIG_HPHEAT_1_STAGE_ACC_2_STAGE": self.rb.configurations.CONFIG_HPHEAT_1_STAGE_ACC_2_STAGE,

            "CONFIG_BO_2_STAGE_AC_1_STAGE": self.rb.configurations.CONFIG_BO_2_STAGE_AC_1_STAGE,
            "CONFIG_BO_1_STAGE_AC_2_STAGE": self.rb.configurations.CONFIG_BO_1_STAGE_AC_2_STAGE,
            "CONFIG_BO_2_STAGE_AC_1_STAGE_ACC": self.rb.configurations.CONFIG_BO_2_STAGE_AC_1_STAGE_ACC,
            "CONFIG_BO_1_STAGE_AC_2_STAGE_ACC": self.rb.configurations.CONFIG_BO_1_STAGE_AC_2_STAGE_ACC,
            "CONFIG_BO_2_STAGE_AC_1_STAGE_ACC_2_STAGE": self.rb.configurations.CONFIG_BO_2_STAGE_AC_1_STAGE_ACC_2_STAGE,
            "CONFIG_BO_1_STAGE_AC_2_STAGE_ACC_2_STAGE": self.rb.configurations.CONFIG_BO_1_STAGE_AC_2_STAGE_ACC_2_STAGE,

            "CONFIG_FN_1_STAGE_AC_2_STAGE": self.rb.configurations.CONFIG_FN_1_STAGE_AC_2_STAGE,
            "CONFIG_FN_2_STAGE_AC_1_STAGE": self.rb.configurations.CONFIG_FN_2_STAGE_AC_1_STAGE,
            "CONFIG_FN_1_STAGE_AC_2_STAGE_ACC": self.rb.configurations.CONFIG_FN_1_STAGE_AC_2_STAGE_ACC,
            "CONFIG_FN_2_STAGE_AC_1_STAGE_ACC": self.rb.configurations.CONFIG_FN_2_STAGE_AC_1_STAGE_ACC,
            "CONFIG_FN_1_STAGE_AC_2_STAGE_ACC_2_STAGE": self.rb.configurations.CONFIG_FN_1_STAGE_AC_2_STAGE_ACC_2_STAGE,
            "CONFIG_FN_2_STAGE_AC_1_STAGE_ACC_2_STAGE": self.rb.configurations.CONFIG_FN_2_STAGE_AC_1_STAGE_ACC_2_STAGE,

            "CONFIG_HPCOOL_2_STAGE": self.rb.configurations.CONFIG_HPCOOL_2_STAGE,
            "CONFIG_HPHEAT_2_STAGE": self.rb.configurations.CONFIG_HPHEAT_2_STAGE,
            "CONFIG_HPCOOL_2_STAGE_ACC": self.rb.configurations.CONFIG_HPCOOL_2_STAGE_ACC,
            "CONFIG_HPHEAT_2_STAGE_ACC": self.rb.configurations.CONFIG_HPHEAT_2_STAGE_ACC,
            "CONFIG_HPCOOL_2_STAGE_ACC_2_STAGE": self.rb.configurations.CONFIG_HPCOOL_2_STAGE_ACC_2_STAGE,
            "CONFIG_HPHEAT_2_STAGE_ACC_2_STAGE": self.rb.configurations.CONFIG_HPHEAT_2_STAGE_ACC_2_STAGE,

            "CONFIG_HPCOOL_1_STAGE_AUX_1_STAGE": self.rb.configurations.CONFIG_HPCOOL_1_STAGE_AUX_1_STAGE,
            "CONFIG_HPCOOL_1_STAGE_AUX_1_STAGE_FAN_2_STAGE":
                self.rb.configurations.CONFIG_HPCOOL_1_STAGE_AUX_1_STAGE_FAN_2_STAGE,
            "CONFIG_HPCOOL_1_STAGE_AUX_1_STAGE_FAN_3_STAGE":
                self.rb.configurations.CONFIG_HPCOOL_1_STAGE_AUX_1_STAGE_FAN_3_STAGE,
            "CONFIG_HPCOOL_1_STAGE_AUX_1_STAGE_ACC": self.rb.configurations.CONFIG_HPCOOL_1_STAGE_AUX_1_STAGE_ACC,
            "CONFIG_HPCOOL_1_STAGE_AUX_1_STAGE_FAN_2_STAGE_ACC":
                self.rb.configurations.CONFIG_HPCOOL_1_STAGE_AUX_1_STAGE_FAN_2_STAGE_ACC,
            "CONFIG_HPCOOL_1_STAGE_AUX_1_STAGE_FAN_3_STAGE_ACC":
                self.rb.configurations.CONFIG_HPCOOL_1_STAGE_AUX_1_STAGE_FAN_3_STAGE_ACC,
            "CONFIG_HPCOOL_1_STAGE_AUX_1_STAGE_ACC_2_STAGE":
                self.rb.configurations.CONFIG_HPCOOL_1_STAGE_AUX_1_STAGE_ACC_2_STAGE,
            "CONFIG_HPCOOL_1_STAGE_AUX_1_STAGE_FAN_2_STAGE_ACC_2_STAGE":
                self.rb.configurations.CONFIG_HPCOOL_1_STAGE_AUX_1_STAGE_FAN_2_STAGE_ACC_2_STAGE,
            "CONFIG_HPCOOL_1_STAGE_AUX_1_STAGE_FAN_3_STAGE_ACC_2_STAGE":
                self.rb.configurations.CONFIG_HPCOOL_1_STAGE_AUX_1_STAGE_FAN_3_STAGE_ACC_2_STAGE,

            "CONFIG_HPHEAT_1_STAGE_AUX_1_STAGE": self.rb.configurations.CONFIG_HPHEAT_1_STAGE_AUX_1_STAGE,
            "CONFIG_HPHEAT_1_STAGE_AUX_1_STAGE_FAN_2_STAGE":
                self.rb.configurations.CONFIG_HPHEAT_1_STAGE_AUX_1_STAGE_FAN_2_STAGE,
            "CONFIG_HPHEAT_1_STAGE_AUX_1_STAGE_FAN_3_STAGE":
                self.rb.configurations.CONFIG_HPHEAT_1_STAGE_AUX_1_STAGE_FAN_3_STAGE,
            "CONFIG_HPHEAT_1_STAGE_AUX_1_STAGE_ACC": self.rb.configurations.CONFIG_HPHEAT_1_STAGE_AUX_1_STAGE_ACC,
            "CONFIG_HPHEAT_1_STAGE_AUX_1_STAGE_FAN_2_STAGE_ACC":
                self.rb.configurations.CONFIG_HPHEAT_1_STAGE_AUX_1_STAGE_FAN_2_STAGE_ACC,
            "CONFIG_HPHEAT_1_STAGE_AUX_1_STAGE_FAN_3_STAGE_ACC":
                self.rb.configurations.CONFIG_HPHEAT_1_STAGE_AUX_1_STAGE_FAN_3_STAGE_ACC,
            "CONFIG_HPHEAT_1_STAGE_AUX_1_STAGE_ACC_2_STAGE":
                self.rb.configurations.CONFIG_HPHEAT_1_STAGE_AUX_1_STAGE_ACC_2_STAGE,
            "CONFIG_HPHEAT_1_STAGE_AUX_1_STAGE_FAN_2_STAGE_ACC_2_STAGE":
                self.rb.configurations.CONFIG_HPHEAT_1_STAGE_AUX_1_STAGE_FAN_2_STAGE_ACC_2_STAGE,
            "CONFIG_HPHEAT_1_STAGE_AUX_1_STAGE_FAN_3_STAGE_ACC_2_STAGE":
                self.rb.configurations.CONFIG_HPHEAT_1_STAGE_AUX_1_STAGE_FAN_3_STAGE_ACC_2_STAGE,

            "CONFIG_HPHEAT_1_STAGE_AUX_2_STAGE": self.rb.configurations.CONFIG_HPHEAT_1_STAGE_AUX_2_STAGE,
            "CONFIG_HPHEAT_1_STAGE_AUX_2_STAGE_ACC": self.rb.configurations.CONFIG_HPHEAT_1_STAGE_AUX_2_STAGE_ACC,
            "CONFIG_HPHEAT_1_STAGE_AUX_2_STAGE_ACC_2_STAGE":
                self.rb.configurations.CONFIG_HPHEAT_1_STAGE_AUX_2_STAGE_ACC_2_STAGE,

            "CONFIG_BO_2_STAGE_AC_2_STAGE": self.rb.configurations.CONFIG_BO_2_STAGE_AC_2_STAGE,
            "CONFIG_BO_2_STAGE_AC_2_STAGE_ACC": self.rb.configurations.CONFIG_BO_2_STAGE_AC_2_STAGE_ACC,
            "CONFIG_BO_2_STAGE_AC_2_STAGE_ACC_2_STAGE": self.rb.configurations.CONFIG_BO_2_STAGE_AC_2_STAGE_ACC_2_STAGE,

            "CONFIG_FN_2_STAGE_AC_2_STAGE": self.rb.configurations.CONFIG_FN_2_STAGE_AC_2_STAGE,
            "CONFIG_FN_2_STAGE_AC_2_STAGE_ACC": self.rb.configurations.CONFIG_FN_2_STAGE_AC_2_STAGE_ACC,
            "CONFIG_FN_2_STAGE_AC_2_STAGE_ACC_2_STAGE": self.rb.configurations.CONFIG_FN_2_STAGE_AC_2_STAGE_ACC_2_STAGE,

            "CONFIG_HPCOOL_1_STAGE_AUX_2_STAGE": self.rb.configurations.CONFIG_HPCOOL_1_STAGE_AUX_2_STAGE,
            "CONFIG_HPCOOL_1_STAGE_AUX_2_STAGE_ACC": self.rb.configurations.CONFIG_HPCOOL_1_STAGE_AUX_2_STAGE_ACC,
            "CONFIG_HPCOOL_1_STAGE_AUX_2_STAGE_ACC_2_STAGE":
                self.rb.configurations.CONFIG_HPCOOL_1_STAGE_AUX_2_STAGE_ACC_2_STAGE,

            "CONFIG_HPCOOL_2_STAGE_AUX_1_STAGE": self.rb.configurations.CONFIG_HPCOOL_2_STAGE_AUX_1_STAGE,
            "CONFIG_HPCOOL_2_STAGE_AUX_1_STAGE_ACC": self.rb.configurations.CONFIG_HPCOOL_2_STAGE_AUX_1_STAGE_ACC,
            "CONFIG_HPCOOL_2_STAGE_AUX_1_STAGE_ACC_2_STAGE":
                self.rb.configurations.CONFIG_HPCOOL_2_STAGE_AUX_1_STAGE_ACC_2_STAGE,

            "CONFIG_HPHEAT_2_STAGE_AUX_1_STAGE": self.rb.configurations.CONFIG_HPHEAT_2_STAGE_AUX_1_STAGE,
            "CONFIG_HPHEAT_2_STAGE_AUX_1_STAGE_ACC": self.rb.configurations.CONFIG_HPHEAT_2_STAGE_AUX_1_STAGE_ACC,
            "CONFIG_HPHEAT_2_STAGE_AUX_1_STAGE_ACC_2_STAGE":
                self.rb.configurations.CONFIG_HPHEAT_2_STAGE_AUX_1_STAGE_ACC_2_STAGE,

            "CONFIG_HPHEAT_2_STAGE_AUX_2_STAGE": self.rb.configurations.CONFIG_HPHEAT_2_STAGE_AUX_2_STAGE,
            "CONFIG_HPHEAT_2_STAGE_AUX_2_STAGE_ACC": self.rb.configurations.CONFIG_HPHEAT_2_STAGE_AUX_2_STAGE_ACC,
            "CONFIG_HPHEAT_2_STAGE_AUX_2_STAGE_ACC_2_STAGE":
                self.rb.configurations.CONFIG_HPHEAT_2_STAGE_AUX_2_STAGE_ACC_2_STAGE,

            "CONFIG_HPCOOL_2_STAGE_AUX_2_STAGE": self.rb.configurations.CONFIG_HPCOOL_2_STAGE_AUX_2_STAGE,
            "CONFIG_HPCOOL_2_STAGE_AUX_2_STAGE_ACC": self.rb.configurations.CONFIG_HPCOOL_2_STAGE_AUX_2_STAGE_ACC,
            "CONFIG_HPCOOL_2_STAGE_AUX_2_STAGE_ACC_2_STAGE":
                self.rb.configurations.CONFIG_HPCOOL_2_STAGE_AUX_2_STAGE_ACC_2_STAGE,
            "CONFIG_ALL": self.rb.configurations.CONFIG_ALL
        }

    def _init_relay_board(self):
        """Initialize the RelayBoard with default values."""
        self.rb = RelayBoard("ares")
        self.set_valid_config_commands()
        # Configure default powered state
        self.rb.configure(self.rb.configurations.CONFIG_POWER)

    def init_server(self):
        """Initializes and runs the Flask server"""
        self._success_response = {"state": "success", "session_id": "", "start_time": None, "value": None}
        # Mapping function calls to flask's error handler.
        self.app.errorhandler(400)(self.bad_request)
        self.app.errorhandler(401)(self.unauthorized)
        self.app.errorhandler(403)(self.forbidden)
        self.app.errorhandler(404)(self.not_found)
        self.app.errorhandler(408)(self.request_timeout)
        # Mapping Flask endpoints to relevant functions.
        self.app.add_url_rule("/api/session/", "start_session", self.start_session, methods=["POST"])  # used
        self.app.add_url_rule("/api/status/", "get_status", self.get_status, methods=["GET"])  # used partially
        self.app.add_url_rule("/api/session/", "end_session", self.end_session, methods=["DELETE"])  # used
        self.app.add_url_rule('/api/relays/', 'get_relay_states', self.get_relay_state, methods=['POST']) # used
        self.app.add_url_rule('/api/relays/configure/', 'set_relay_states', self.set_relay_state, methods=['POST']) # used
        self.app.add_url_rule('/api/clear/', 'clear_all_sessions', self.clear_all_sessions, methods=['DELETE'])
        self.app.add_url_rule('/api/stop/', 'stop_server', self.stop_server, methods=['DELETE'])
        self.app.add_url_rule('/api/get_arb_config/', 'get_arb_config', self.get_arb_config, methods=['GET'])
        # Aquastat requests
        self.app.add_url_rule('/api/aquastat/start/', 'aquastat_start', self.start_aquastat_mode, methods=['POST'])
        self.app.add_url_rule('/api/aquastat/end/', 'aquastat_end', self.end_aquastat_mode, methods=['POST'])
        self.app.add_url_rule('/api/aquastat/open/', 'open_aquastat', self.open_aquastat, methods=['POST'])
        self.app.add_url_rule('/api/aquastat/close/', 'close_aquastat', self.close_aquastat, methods=['POST'])
        self.app.add_url_rule('/api/aquastat/mode/', 'get_aquastat_mode', self.get_aquastat_mode, methods=['GET'])
        self.app.add_url_rule('/api/aquastat/state/', 'get_aquastat_state', self.get_aquastat_state, methods=['GET'])

        self._init_relay_board()
        self.port = 5000
        # Start flask server.
        self.app.run(debug=False, port=self.port, host='0.0.0.0')
        
        
    # Error handler helper functions. Note: these are NOT static methods, as they are called by Flask's error handler,
    # which is itself an object of whatever is using this base class. The error argument is also required, as per
    # Flask's implementation of the errorhandler helper function.

    def bad_request(self, error):
        """Returns 400 Bad Request Error"""
        return make_response(jsonify({"error": "Bad request"}), 400)

    def unauthorized(self, error):
        """Returns 401 Unauthorized Error"""
        if error != 401:
            return make_response(jsonify({"error": f"{error}"}), 401)
        return make_response(jsonify({"error": "Unauthorized"}), 401)

    def forbidden(self, error):
        """Returns 403 Forbidden Error"""
        return make_response(jsonify({"error": "Forbidden"}), 403)

    def not_found(self, error):
        """Returns 404 Not Found Error"""
        return make_response(jsonify({"error": "Not found"}), 404)

    def request_timeout(self, error):
        """Returns 408 Request Timeout Error"""
        return make_response(jsonify({"error": "Request Timeout"}), 408)

    def check_session_timeout(self):
        """Calls parent check_session_timeout, and cleans up session as necessary (i.e. session has timed out).
        Returns True if either the session has timed out or no session exists; False otherwise."""
        if self.session_id:
            if (time.time() - self.last_event_time) > DEFAULT_SESSION_TTL:
                self.last_event_time = time.time()
                self.session_cleanup()
                status = True
            elapsed_time = time.time() - self.last_event_time
            log.info("Time between events: " + str(elapsed_time))
            status =  False

        self.last_event_time = time.time()
        status =  True

        if self.session_id and status:  # If session has timed out
            self.session_cleanup()
        return status

    def session_cleanup(self):
        """Helper function used to clean stale sessions, and initialize the base/default powered state. Additionally
        the device is returned to an available state."""
        self.session_id = None
        if self.rb:
            self.rb.cleanup()
        self._init_relay_board()

        # Decorators used for request validation. Currently all request validation is performed on session_id (and if the
        # user request body exists). These are defined as static methods, despite the child wrapper functions often
        # utilizing non-static methods. This is because the decorated function is passed to the base decorator function
        # instead of self, which is received by the child method via the wrapped function passed in as an argument.

    @staticmethod
    def request_exists_check(func):
        """Verifying that the user sent a request body, throws desired error code if request body is not found."""

        def request_exists_check_wrapper(self):
            user_request = request.get_json()
            if not user_request:
                abort(400)
            return func(self)

        return request_exists_check_wrapper

    @staticmethod
    def verify_valid_session_id(func):
        """Verifying that the session_id found in the user request body matches that of the current session, throws an
        error if it does not. Serves as generic session_id validation for relevant request endpoints."""

        def verify_valid_session_id_wrapper(self):
            session_id = request.json["session_id"]
            if session_id is None:
                abort(400)
            elif session_id != self.session_id:
                abort(401)
            self.last_event_time = time.time()
            return func(self)

        return verify_valid_session_id_wrapper

    @staticmethod
    def verify_no_active_session(func):
        """Verifying that no active session currently exists, throws an error if a session does exist."""

        def verify_no_active_session_wrapper(self):
            if not self.check_session_timeout():
                abort(400)
            return func(self)

        return verify_no_active_session_wrapper

    @staticmethod
    def verify_active_session(response):  # 3rd nested function required to pass arguments to decorator
        """Opposite of verify_no_active_session; verifies a session is in progress, throws an error if a session does
        not exist."""

        def verify_active_session_wrapper(func):
            def verify_session_wrapped(self):
                if self.check_session_timeout():
                    abort(response)
                return func(self)

            return verify_session_wrapped

        return verify_active_session_wrapper

    @verify_no_active_session  # Returns 400 on failure
    @request_exists_check      # Returns 400 on failure
    def start_session(self):
        """Creates a user session if the device does not currently have an active session. The HVAC Simulator is then
        initialized using the user's configuration sent in the request body, and a session_id is returned. This
        session_id is used as verification for all future configuration requests, and is the main proponent of the
        concept of a session. Once the session is ended, this session_id is reset to None until a new session is
        created."""
        if not ("model" or "has_rc" or "has_rh" or "has_pek" or "in_phase" or "acc_minus") in request.json:
            response = make_response("Double check the config.  Must have values for model, has_rc, has_rh, has_pek, "
                                     "in_phase, and acc_minus set in the body.")
            response.status_code = 400
            abort(response)
        if not request.json["model"] in ["athena", "nike", "apollo", "vulcan", "ares", "artemis", "attisPro",
                                         "attisRetail"]:
            response = make_response("Double check the model type.  Must be either athena, nike, apollo, vulcan, ares,"
                                     " artemis, attisPro or attisRetail.")
            response.status_code = 400
            abort(response)
        try:
            if self.rb:
                self.rb.cleanup()
            self.rb = RelayBoard(request.json["model"], request.json["has_pek"], request.json["has_rh"],
                                 request.json["has_rc"], request.json["in_phase"], request.json["acc_minus"])
            self.set_valid_config_commands()
            self.rb.configure(self.rb.configurations.CONFIG_POWER)
        except ValueError as e:
            self.session_cleanup()
            return make_response(e, 418)
        self.session_id = b2a_hex(urandom(15)).decode("utf-8")
        resp = self._success_response
        resp["session_id"] = self.session_id
        resp["start_time"] = time.ctime(time.time())  # Current time & date.
        return make_response(jsonify(resp), 200)


    @request_exists_check        # Returns 400 on failure
    @verify_active_session(404)  # Can't end a session that doesn't exist
    @verify_valid_session_id     # Returns 400/401 on failure
    def end_session(self):
        """Ends the current session, verified by the session_id contained in the request body. Upon ending the session,
        the device falls back to its default powered state."""
        self.session_cleanup()
        return make_response("", 204)

    @request_exists_check
    @verify_active_session(400)
    @verify_valid_session_id
    def get_relay_state(self):
        """Checks and returns the current relay state from the sense module upon receiving a valid session_id."""
        return self.rb.sense_module.get_relay_states()

    @request_exists_check
    @verify_active_session(400)
    @verify_valid_session_id
    def set_relay_state(self):
        """Activates relays according to the state specified in the request body, which are defined explicitly in
        relay_board and switch_module. Note that while the default state is configured for thermostat power, other
        mechanical relays will not be engaged as expected until the corresponding relay state is set."""
        if not request.json["config"] in self.valid_config_commands:
            response = make_response("Invalid config.")
            response.status_code = 400
            abort(response)
        else:
            try:
                self.rb.configure(self.valid_config_commands[request.json["config"]])
                resp = {
                    "start_time": time.ctime(time.time()),
                    "relay states": self.rb.switch_module.read_config_str()
                }
                return make_response(jsonify(resp), 200)
            except ValueError as e:
                self.session_cleanup()
                return make_response(jsonify(e), 500)

    @request_exists_check
    @verify_active_session(400)
    @verify_valid_session_id
    def start_aquastat_mode(self) -> Response:
        """Starts aquastat mode

        :return: HTTP message + status code pertaining to result of start aquastat function
            200 - Success
            417 - Expectation Failed
            428 - Precondition Required
        """
        return self.rb.switch_module.start_aquastat_mode()

    @request_exists_check
    @verify_active_session(400)
    @verify_valid_session_id
    def end_aquastat_mode(self) -> Response:
        """Ends aquastat mode

        :return: HTTP message + status code pertaining to result of end aquastat function
            200 - Success
            417 - Expectation Failed
            428 - Precondition Required
        """
        return self.rb.switch_module.end_aquastat_mode()

    @request_exists_check
    @verify_active_session(400)
    @verify_valid_session_id
    def open_aquastat(self) -> Response:
        """Opens connection between Rh and PEK, thus simulating the aquastat opening

        :return: HTTP message + status code pertaining to result of the open aquastat function
            200 - Success
            417 - Expectation Failed
            428 - Precondition Required
        """
        return self.rb.switch_module.open_aquastat()

    @request_exists_check
    @verify_active_session(400)
    @verify_valid_session_id
    def close_aquastat(self) -> Response:
        """Closes connection between Rh and PEK, thus simulating the aquastat closing

        :return: HTTP message + status code pertaining to result of the close aquastat function
            200 - Success
            417 - Expectation Failed
            428 - Precondition Required
        """
        return self.rb.switch_module.close_aquastat()

    @request_exists_check
    @verify_active_session(400)
    @verify_valid_session_id
    def get_aquastat_mode(self) -> Response:
        """Gets the current aquastat mode (On / Off)

        :return: current aquastat mode (On / Off)
        """
        return self.rb.switch_module.get_aquastat_mode()

    @request_exists_check
    @verify_active_session(400)
    @verify_valid_session_id
    def get_aquastat_state(self) -> Response:
        """Gets the state of the aquastat

        :return: current aquastat state (Open / Closed)
        """
        return self.rb.switch_module.get_aquastat_state()

    def clear_all_sessions(self):
        """Ends the current session (in case the server ends up in a deadlocked state and the session id is unknown)

        and cleans up the relay states to get the server back in a usable state
        NOTE: this isn't used as part of automation, rather as a manual failsafe to recover the server
        """
        self.session_cleanup()
        return make_response("Sessions cleared", 200)

    def stop_server(self):
        """Stops the server from running and kills the Flask app by killing the process on the Pi

        NOTE: this isn't used as part of automation, rather as a manual failsafe to restart the server
        """
        self.rb.cleanup()
        self.session_id = None
        try:
            if self.rb:
                print("Server could not be shutdown, Raspberry Pi could not clean up GPIO properly")
                return make_response("Server could not be shut down", 409)
        except AttributeError:
            print("Shutting down server, closing...")
            os.kill(os.getpid(), signal.SIGINT)
            return make_response("Server shut down", 200)

    def get_arb_config(self) -> Response:
        """Retrives the current HVACSim configuration

        :return: HTTP message + status code indicating the current HVACSim config
        """
        return self.rb.switch_module.read_config()

    def get_status(self):
        """Return the current availability of the device, determined by the check_session_timeout helper function."""
        if self.check_session_timeout():  # Either no session exists or it has timed out.
            return make_response("Available", 200)
        return make_response("Busy", 200)


if __name__ == '__main__':
    HVACSimServer()
