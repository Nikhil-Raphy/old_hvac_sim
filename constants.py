from types import SimpleNamespace

# Aquastat/Pipe Sensor Constants
AquastatBoardMode = SimpleNamespace(
    ON="On",
    OFF="Off"
)

AquastatState = SimpleNamespace(
    OPEN="Open",
    CLOSED="Closed"
)

DEVICE_LIST = ["athena","nike","apollo","vulcan","ares","artemis","attisPro","attisRetail",]

# DEFAULT_HVAC_IP = "0.0.0.0"
DEFAULT_SESSION_TTL = 3600  # 1 hour
