"""A module to query the weenect web api."""
from __future__ import annotations

import asyncio
import json
import socket
from importlib import metadata
from typing import Any, Mapping

import aiohttp
import async_timeout
from yarl import URL

from .exceptions import WeenectConnectionError, WeenectError
from .zone_modes import ZoneNotificationMode

SCHEME = "https"
APP_HOST = "my.weenect.com"
APP_URL = str(URL.build(scheme=SCHEME, host=APP_HOST))
API_HOST = "apiv4.weenect.com"
API_VERSION = "/v4"


class AioWeenect:
    """Main class for handling connections with weenect."""

    def __init__(
        self,
        password: str,
        username: str,
        request_timeout: int = 10,
        session: aiohttp.client.ClientSession | None = None,
        user_agent: str | None = None,
    ) -> None:
        """Initialize connection with weenect.
        Class constructor for setting up an AioWeenect object to
        communicate with the weenect API.
        Args:
            password: Password for HTTP authentification.
            request_timeout: Max timeout to wait for a response from the API.
            session: Optional, shared, aiohttp client session.
            user_agent: Defaults to AioWeenect/<version>.
            username: Username for HTTP authentification.
        """
        self._session = session
        self._close_session = False
        self._auth_token: str | None = None

        self.password = password
        self.request_timeout = request_timeout
        self.username = username
        self.user_agent = user_agent

        if user_agent is None:
            version = metadata.version(__package__)
            self.user_agent = f"AioWeenect/{version}"

    async def login(self) -> None:
        """Log into the weenect API.
        Retrieves a JSON web token and stores it.
        It will be attached to every request.
        Raises:
            WeenectConnectionError: An error occurred while communicating
                with the weenect API (connection issues).
            WeenectHomeError: An error occurred while processing the
                response from the weenect API (invalid data).
        """
        response = await self.request(
            uri="user/login",
            method="POST",
            json_data={"username": self.username, "password": self.password},
        )

        if response is None:
            raise WeenectConnectionError(
                "Error occurred while authenticating with the weenect API."
            )

        jwt = response["access_token"]
        self._auth_token = f"JWT {jwt}"

    async def authenticated_request(
        self,
        uri: str,
        method: str = "GET",
        additional_headers: dict | None = None,
        data: Any | None = None,
        json_data: dict | None = None,
        params: Mapping[str, str] | None = None,
    ) -> Any:
        """Handle a request to the weenect API.
        Makes sure the client is authenticated and
        makes a request against the weenect API and handles the response.
        Args:
            uri: The request URI on the weenect API to call.
            method: HTTP method to use for the request; e.g., GET, POST.
            data: RAW HTTP request data to send with the request.
            json_data: Dictionary of data to send as JSON with the request.
            params: Mapping of request parameters to send with the request.
        Returns:
            The response from the API. In case the response is a JSON response,
            the method will return a decoded JSON response as a Python
            dictionary. In other cases, it will return the RAW text response.
        Raises:
            WeenectConnectionError: An error occurred while communicating
                with the weenect API (connection issues).
            WeenectHomeError: An error occurred while processing the
                response from the weenect API (invalid data).
        """
        if self._auth_token is None:
            await self.login()
        return await self.request(
            uri=uri,
            method=method,
            additional_headers=additional_headers,
            data=data,
            json_data=json_data,
            params=params,
        )

    async def request(
        self,
        uri: str,
        method: str = "GET",
        additional_headers: dict | None = None,
        data: Any | None = None,
        json_data: dict | None = None,
        params: Mapping[str, str] | None = None,
    ) -> Any:
        """Handle a request to the weenect API.
        Make a request against the weenect API and handles the response.
        Args:
            uri: The request URI on the weenect API to call.
            method: HTTP method to use for the request; e.g., GET, POST.
            data: RAW HTTP request data to send with the request.
            json_data: Dictionary of data to send as JSON with the request.
            params: Mapping of request parameters to send with the request.
        Returns:
            The response from the API. In case the response is a JSON response,
            the method will return a decoded JSON response as a Python
            dictionary. In other cases, it will return the RAW text response.
        Raises:
            WeenectConnectionError: An error occurred while communicating
                with the weenect API (connection issues).
            WeenectHomeError: An error occurred while processing the
                response from the weenect API (invalid data).
        """
        url = URL.build(scheme=SCHEME, host=API_HOST, path=API_VERSION) / uri

        headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/json, text/plain, */*",
            "Origin": APP_URL,
            "x-app-version": "0.1.0",
            "x-app-user-id": "",
            "x-app-type": "userspace",
            "DNT": "1",
        }
        if self._auth_token is not None:
            headers.update({"Authorization": self._auth_token})

        if additional_headers is not None:
            headers.update(additional_headers)

        if self._session is None:
            self._session = aiohttp.ClientSession()
            self._close_session = True

        try:
            with async_timeout.timeout(self.request_timeout):
                response = await self._session.request(
                    method,
                    url,
                    data=data,
                    json=json_data,
                    params=params,
                    headers=headers,
                )
        except asyncio.TimeoutError as exception:
            raise WeenectConnectionError(
                "Timeout occurred while connecting to the weenect API."
            ) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            raise WeenectConnectionError(
                "Error occurred while communicating with the weenect API."
            ) from exception

        content_type = response.headers.get("Content-Type", "")
        if response.status // 100 in [4, 5]:
            contents = await response.read()
            response.close()

            if content_type == "application/json":
                raise WeenectError(response.status, json.loads(contents.decode("utf8")))
            raise WeenectError(response.status, {"message": contents.decode("utf8")})

        if response.status == 204:  # NO CONTENT
            return None

        if "application/json" in content_type:
            return await response.json()

        text = await response.text()
        return {"message": text}

    async def get_user(self, user_id: str | None = None) -> dict[str, Any]:
        """Get the user information.
        Args:
            user_id: The id of the user.
        Returns:
            The response from the API.
        Raises:
            WeenectConnectionError: An error occurred while communicating
                with the weenect API (connection issues).
            WeenectHomeError: An error occurred while processing the
                response from the weenect API (invalid data).
        """
        if user_id is not None:
            return await self.authenticated_request(  # type: ignore[no-any-return]
                uri=f"user/{user_id}"
            )
        return await self.authenticated_request(  # type: ignore[no-any-return]
            uri="myuser"
        )

    async def get_subscription_offers(self) -> list[dict[str, Any]]:
        """Get subscription offers.
        Returns:
            A list containing subscription offers.
        Raises:
            WeenectConnectionError: An error occurred while communicating
                with the weenect API (connection issues).
            WeenectHomeError: An error occurred while processing the
                response from the weenect API (invalid data).
        """
        return await self.authenticated_request(  # type: ignore[no-any-return]
            uri="subscriptionoffer"
        )

    async def get_subscription(self, subscription_id: str) -> dict[str, Any]:
        """Get subscription information.
        Args:
            subscription_id: The id of the subscription.
        Returns:
            Subscription information.
        Raises:
            WeenectConnectionError: An error occurred while communicating
                with the weenect API (connection issues).
            WeenectHomeError: An error occurred while processing the
                response from the weenect API (invalid data).
        """
        return await self.authenticated_request(  # type: ignore[no-any-return]
            uri=f"mysubscription/{subscription_id}"
        )

    async def get_zones(self, tracker_id: str) -> dict[str, Any]:
        """Get all available zones for this tracker.
        Args:
            tracker_id: The id of the tracker.
        Returns:
            All available zones for the tracker_id.
        Raises:
            WeenectConnectionError: An error occurred while communicating
                with the weenect API (connection issues).
            WeenectHomeError: An error occurred while processing the
                response from the weenect API (invalid data).
        """
        return await self.authenticated_request(  # type: ignore[no-any-return]
            uri=f"mytracker/{tracker_id}/zones"
        )

    async def add_zone(
        self,
        tracker_id: str,
        address: str,
        latitude: float,
        longitude: float,
        name: str,
        active: bool | None = True,
        distance: int | None = 100,
        is_outside: bool | None = False,
        mode: ZoneNotificationMode = ZoneNotificationMode.ENTER_AND_EXIT,
    ) -> dict[str, Any]:
        """Add a zone for this tracker.
        Args:
            tracker_id: The id of the tracker.
            address: The address of the zone center.
            latitude: The latitude of the zone center.
            longitude: The longitude of the zone center.
            name: The name of the zone.
            active: Is the zone active?
            distance: The radius of the zone in meters.
            is_outside: If the zone is outside.
                If yes this increases enter/exit detection precision.
            mode: The ZoneNotificationMode of the zone.

        Returns:
            The created zone.
        Raises:
            WeenectConnectionError: An error occurred while communicating
                with the weenect API (connection issues).
            WeenectHomeError: An error occurred while processing the
                response from the weenect API (invalid data).
        """
        data = {
            "active": active,
            "address": address,
            "distance": distance,
            "is_outside": is_outside,
            "latitude": latitude,
            "longitude": longitude,
            "mode": mode.value,
            "name": name,
        }
        return await self.authenticated_request(  # type: ignore[no-any-return]
            uri=f"mytracker/{tracker_id}/zones", method="POST", json_data=data
        )

    async def remove_zone(
        self,
        tracker_id: str,
        zone_id: str,
    ) -> dict[str, Any]:
        """Remove a zone for this tracker.
        Args:
            tracker_id: The id of the tracker.
            zone_id: The id of the zone.
        Raises:
            WeenectConnectionError: An error occurred while communicating
                with the weenect API (connection issues).
            WeenectHomeError: An error occurred while processing the
                response from the weenect API (invalid data).
        """
        return await self.authenticated_request(  # type: ignore[no-any-return]
            uri=f"mytracker/{tracker_id}/zones/{zone_id}", method="DELETE"
        )

    async def get_position(
        self, tracker_id: str, start: str | None = None, end: str | None = None
    ) -> list[dict[str, Any]]:
        """Get position data for the tracker id.
        Args:
            tracker_id: The id of the tracker.
            start: Optional, only return data after this timestamp.
            end: Optional, only return data before this timestamp.
        Returns:
            A list containing location dictionaries.
        Raises:
            WeenectConnectionError: An error occurred while communicating
                with the weenect API (connection issues).
            WeenectHomeError: An error occurred while processing the
                response from the weenect API (invalid data).
        """
        return await self.authenticated_request(  # type: ignore[no-any-return]
            uri=f"mytracker/{tracker_id}/position"
        )

    async def get_activity(
        self, tracker_id: str, start: str, end: str | None = None
    ) -> list[dict[str, Any]]:
        """Get activity data for the tracker id.
        Args:
            tracker_id: The id of the tracker.
            start: Optional, only return data after this timestamp.
            end: Optional, only return data before this timestamp.
        Returns:
            A list containing location dictionaries.
        Raises:
            WeenectConnectionError: An error occurred while communicating
                with the weenect API (connection issues).
            WeenectHomeError: An error occurred while processing the
                response from the weenect API (invalid data).
        """
        return await self.authenticated_request(  # type: ignore[no-any-return]
            uri=f"mytracker/{tracker_id}/activity"
        )

    async def get_trackers(self) -> list[dict[str, Any]]:
        """Get all available trackers.
        Returns:
            All available trackers.
        Raises:
            WeenectConnectionError: An error occurred while communicating
                with the weenect API (connection issues).
            WeenectHomeError: An error occurred while processing the
                response from the weenect API (invalid data).
        """
        return await self.authenticated_request(  # type: ignore[no-any-return]
            uri="mytracker"
        )

    async def set_update_interval(
        self,
        tracker_id: str,
        update_interval: str,
    ) -> None:
        """Set the update interval for this tracker id.
        Args:
            tracker_id: The id of the tracker.
            update_interval: The new update interval.
        Raises:
            WeenectConnectionError: An error occurred while communicating
                with the weenect API (connection issues).
            WeenectHomeError: An error occurred while processing the
                response from the weenect API (invalid data).
        """
        return await self.authenticated_request(  # type: ignore[no-any-return]
            uri=f"mytracker/{tracker_id}/mode",
            method="POST",
            json_data={"mode": update_interval},
        )

    async def activate_super_live(
        self,
        tracker_id: str,
    ) -> None:
        """Activate the super live mode for this tracker id.
        Args:
            tracker_id: The id of the tracker.
        Raises:
            WeenectConnectionError: An error occurred while communicating
                with the weenect API (connection issues).
            WeenectHomeError: An error occurred while processing the
                response from the weenect API (invalid data).
        """
        return await self.authenticated_request(  # type: ignore[no-any-return]
            uri=f"mytracker/{tracker_id}/st-mode", method="POST"
        )

    async def refresh_location(
        self,
        tracker_id: str,
    ) -> None:
        """Request a position refresh for this tracker id.
        Args:
            tracker_id: The id of the tracker.
        Raises:
            WeenectConnectionError: An error occurred while communicating
                with the weenect API (connection issues).
            WeenectHomeError: An error occurred while processing the
                response from the weenect API (invalid data).
        """
        return await self.authenticated_request(  # type: ignore[no-any-return]
            uri=f"mytracker/{tracker_id}/position/refresh", method="POST"
        )

    async def vibrate(
        self,
        tracker_id: str,
    ) -> None:
        """Send a vibration command for this tracker id.
        Args:
            tracker_id: The id of the tracker.
        Raises:
            WeenectConnectionError: An error occurred while communicating
                with the weenect API (connection issues).
            WeenectHomeError: An error occurred while processing the
                response from the weenect API (invalid data).
        """
        return await self.authenticated_request(  # type: ignore[no-any-return]
            uri=f"mytracker/{tracker_id}/vibrate", method="POST"
        )

    async def ring(
        self,
        tracker_id: str,
    ) -> None:
        """Send a ring command for this tracker id.
        Args:
            tracker_id: The id of the tracker.
        Raises:
            WeenectConnectionError: An error occurred while communicating
                with the weenect API (connection issues).
            WeenectHomeError: An error occurred while processing the
                response from the weenect API (invalid data).
        """
        return await self.authenticated_request(  # type: ignore[no-any-return]
            uri=f"mytracker/{tracker_id}/ring", method="POST"
        )

    async def close(self) -> None:
        """Close open client session."""
        if self._session and self._close_session:
            await self._session.close()

    async def __aenter__(self) -> AioWeenect:
        """Async enter.
        Returns:
            The AioWeenect object.
        """
        return self

    async def __aexit__(self, *_exc_info) -> None:
        """Async exit.
        Args:
            _exc_info: Exec type.
        """
        await self.close()
