"""Exceptions for aioweenect."""


class WeenectError(Exception):
    """Generic aioweenect exception."""


class WeenectConnectionError(WeenectError):
    """aioweenect connection exception."""
