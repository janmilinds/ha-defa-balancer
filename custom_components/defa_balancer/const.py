"""Constants for defa_balancer."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "defa_balancer"
PARALLEL_UPDATES = 1

DEFAULT_MULTICAST_GROUP = "234.222.250.1"
DEFAULT_MULTICAST_PORT = 57082
DEFAULT_UPDATE_INTERVAL_SECONDS = 10
DEFAULT_PHASE_VOLTAGE = 230.0

CONF_MULTICAST_GROUP = "multicast_group"
CONF_MULTICAST_PORT = "multicast_port"
CONF_SERIAL = "serial"
CONF_UPDATE_INTERVAL = "update_interval"

DATA_L1 = "l1"
DATA_L2 = "l2"
DATA_L3 = "l3"
DATA_L1_POWER = "l1_power"
DATA_L2_POWER = "l2_power"
DATA_L3_POWER = "l3_power"
DATA_TOTAL_POWER = "total_power"
DATA_FIRMWARE = "firmware"
DATA_PACKET_COUNT = "packet_count"

PACKET_LENGTH = 54

SCAN_TIMEOUT_INITIAL = 5.0
SCAN_TIMEOUT_RETRY = 10.0
