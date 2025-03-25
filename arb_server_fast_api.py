import os
import signal
import time
from binascii import b2a_hex
from os import urandom
from typing import Dict, Optional
from service_logging import log

from fastapi import FastAPI, Request, HTTPException, Depends
from pydantic import BaseModel
from fastapi.responses import JSONResponse

from constants import DEFAULT_SESSION_TTL
from relay_board import RelayBoard


class HVACSimServer:
    """HVAC Simulator Server with FastAPI"""

    VALID_MODELS = ("athena", "nike", "apollo", "vulcan","ares", "artemis", "attisPro", "attisRetail")

    def __init__(self):
        self.app = FastAPI(title="HVAC Simulator API")
        self._init_state()
        self._setup_routes()
        self._init_relay_board()

    # --------------------------
    # Pydantic Models
    # --------------------------
    class SessionConfig(BaseModel):
        model: str
        has_rc: bool
        has_rh: bool
        has_pek: bool
        in_phase: bool
        acc_minus: bool

    class RelayConfig(BaseModel):
        config: str
        session_id: str

    class SessionID(BaseModel):
        session_id: str

    # --------------------------
    # Initialization
    # --------------------------
    def _init_state(self):
        """Initialize server state"""
        self.session_id = None
        self.last_event_time = 0
        self.rb = None
        self.valid_config_commands = {}
        self._success_response = {
            "state": "success",
            "session_id": "",
            "start_time": None,
            "value": None
        }

    def _init_relay_board(self, model: str = "ares"):
        """Initialize the RelayBoard"""
        self.rb = RelayBoard(model)
        self._update_valid_commands()
        self.rb.configure(self.rb.configurations.CONFIG_POWER)

    def _update_valid_commands(self):
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

    # --------------------------
    # Dependency Injections
    # --------------------------
    def _validate_session(self, request: Request) -> Dict:
        """Validate session and return request data"""
        try:
            data = request.model_dump()
        except:
            raise HTTPException(status_code=400, detail="Invalid request body")
        if self._check_session_timeout():
            raise HTTPException(status_code=400, detail="Session Expired")

        if not data.get("session_id"):
            raise HTTPException(status_code=400, detail="Session ID missing")
        if data["session_id"] != self.session_id:
            raise HTTPException(status_code=401, detail="Invalid session ID")

        self.last_event_time = time.time()
        return data

    def _require_no_active_session(self):
        """Ensure no active session exists"""
        if not self._check_session_timeout():
            raise HTTPException(status_code=400, detail="Session already exists")

    # --------------------------
    # Core Methods
    # --------------------------
    def _check_session_timeout(self) -> bool:
        """Check if session has timed out"""
        if self.session_id:
            if (time.time() - self.last_event_time) > DEFAULT_SESSION_TTL:
                self.last_event_time = time.time()
                self._cleanup_session()
                return True
            elapsed_time = time.time() - self.last_event_time
            log.info("Time between events: " + str(elapsed_time))
            return False

        self.last_event_time = time.time()
        return True

    def _cleanup_session(self):
        """Clean up current session"""
        if self.rb:
            self.rb.cleanup()
        self.session_id = None
        self._init_relay_board()

    # --------------------------
    # Endpoints
    # --------------------------
    def _setup_routes(self):
        """Configure all API endpoints"""
        # Session endpoints
        self.app.post("/api/session/")(self.start_session)
        self.app.delete("/api/session/")(self.end_session)
        self.app.get("/api/status/")(self.get_status)

        # Relay endpoints
        self.app.post("/api/relays/")(self.get_relay_state)
        self.app.post("/api/relays/configure/")(self.set_relay_state)

        # Maintenance endpoints
        self.app.delete("/api/clear/")(self.clear_all_sessions)
        self.app.delete("/api/stop/")(self.stop_server)
        self.app.get("/api/get_arb_config/")(self.get_arb_config)

        # Aquastat endpoints
        self.app.post("/api/aquastat/start/")(self.start_aquastat_mode)
        self.app.post("/api/aquastat/end/")(self.end_aquastat_mode)
        self.app.post("/api/aquastat/open/")(self.open_aquastat)
        self.app.post("/api/aquastat/close/")(self.close_aquastat)
        self.app.get("/api/aquastat/mode/")(self.get_aquastat_mode)
        self.app.get("/api/aquastat/state/")(self.get_aquastat_state)

    def start_session(self, config: SessionConfig):
        """Start a new HVAC simulation session"""
        self._require_no_active_session()

        if config.model not in self.VALID_MODELS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid model. Must be one of: {self.VALID_MODELS}"
            )

        try:
            if self.rb:
                self.rb.cleanup()

            self.rb = RelayBoard(
                model=config.model,
                has_pek=config.has_pek,
                has_rh=config.has_rh,
                has_rc=config.has_rc,
                in_phase=config.in_phase,
                acc_minus=config.acc_minus
            )
            self._update_valid_commands()
            self.rb.configure(self.rb.configurations.CONFIG_POWER)
        except ValueError as e:
            self._cleanup_session()
            raise HTTPException(status_code=418, detail=str(e))

        self.session_id = b2a_hex(urandom(15)).decode("utf-8")
        response = self._success_response.copy()
        response.update({
            "session_id": self.session_id,
            "start_time": time.ctime(time.time())
        })
        return response

    def end_session(self, request: SessionID):
        """End the current session"""
        self._validate_session(request)
        self._cleanup_session()
        return JSONResponse(status_code=204)

    def get_relay_state(self, request: SessionID)-> Dict[str, bool]:
        """Get current relay states"""
        self._validate_session(request)
        return json.loads(self.rb.sense_module.get_relay_states())

    def set_relay_state(self, request: RelayConfig):
        """Configure relay states"""
        data = self._validate_session(request)

        if "config" not in data or data["config"] not in self.valid_config_commands:
            raise HTTPException(status_code=400, detail="Invalid configuration command")

        try:
            self.rb.configure(self.valid_config_commands[data["config"]])
            return {
                "start_time": time.ctime(time.time()),
                "relay_states": self.rb.switch_module.read_config_str()
            }
        except ValueError as e:
            self._cleanup_session()
            raise HTTPException(status_code=500, detail=str(e))

    def get_status(self):
        """Get server availability status"""
        return "Available" if self._check_session_timeout() else "Busy"

    def clear_all_sessions(self):
        """Force clear all sessions"""
        self._cleanup_session()
        return {"message": "Sessions cleared"}

    def stop_server(self):
        """Shutdown the server"""
        try:
            if self.rb:
                self.rb.cleanup()
            os.kill(os.getpid(), signal.SIGINT)
            return {"message": "Server shutdown initiated"}
        except Exception as e:
            raise HTTPException(status_code=409, detail=str(e))

    def get_arb_config(self):
        """Get current ARB configuration"""
        return self.rb.switch_module.read_config()

    # Aquastat Endpoints
    def start_aquastat_mode(self, request: SessionID):
        self._validate_session(request)
        return self.rb.switch_module.start_aquastat_mode()

    def end_aquastat_mode(self, request: SessionID):
        self._validate_session(request)
        return self.rb.switch_module.end_aquastat_mode()

    def open_aquastat(self, request: SessionID):
        self._validate_session(request)
        return self.rb.switch_module.open_aquastat()

    def close_aquastat(self, request: SessionID):
        self._validate_session(request)
        return self.rb.switch_module.close_aquastat()

    def get_aquastat_mode(self, request: SessionID):
        self._validate_session(request)
        return self.rb.switch_module.get_aquastat_mode()

    def get_aquastat_state(self, request: SessionID):
        self._validate_session(request)
        return self.rb.switch_module.get_aquastat_state()


def run_server():
    """Run the HVAC simulator server"""
    import uvicorn
    server = HVACSimServer()
    uvicorn.run(
        server.app,
        host="0.0.0.0",
        port=5000,
        log_level="info"
    )


if __name__ == "__main__":
    run_server()