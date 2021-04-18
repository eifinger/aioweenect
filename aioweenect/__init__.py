"""Asynchronous Python client for the weenect API."""

from .aioweenect import (
    AioWeenect,
    WeenectConnectionError,
    WeenectError,
    ZoneNotificationMode,
)

__all__ = [
    "AioWeenect",
    "WeenectConnectionError",
    "WeenectError",
    "ZoneNotificationMode",
]

__version__ = "1.0.1"
