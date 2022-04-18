
from enum import Enum


class STATUS_MESSAGES(Enum):
    # Client to server:
    DATA_OK = "DATA_OK"
    STARTUP_ERROR = "STARTUP_ERROR"
    DATA_ERROR = "DATA_ERROR"
    HEARTBEAT_ACK = "HEARTBEAT_ACK"
    STOP_ACK = "STOP_ACK"

    # Server to client
    GET_DATA = "GET_DATA"
    HEARTBEAT_SYN = "HEARTBEAT_SYN"
    STOP = "STOP"
