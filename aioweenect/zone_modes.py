"""Available notification modes for zones."""
from enum import Enum


class ZoneNotificationMode(Enum):
    """Available notification modes for zones."""

    NONE = 0
    ENTER_ONLY = 1
    EXIT_ONLY = 2
    ENTER_AND_EXIT = 3
