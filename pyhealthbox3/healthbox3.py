from __future__ import annotations

import asyncio

from aiohttp import ClientSession, ClientError, ClientResponseError
from aiohttp.hdrs import METH_GET, METH_PUT, METH_POST

import async_timeout

import logging

from socket import *
from .models import Healthbox3DataObject, Healthbox3Room, Healthbox3RoomBoost

_LOGGER = logging.getLogger(__name__)

class Healthbox3():
    """Healthbox3 Device."""

    _session: ClientSession | None
    _close_session: bool = True
    _request_timeout: int = 10
    _advanced_features: bool = False

    def __init__(self, host: str, api_key: str | None = None , session: ClientSession = None) -> None:

        self._host: str = host
        self._session = session
        self._close_session = False

        if api_key:
            self._api_key = api_key
        
    @property
    def advanced_api_enabled(self) -> bool:
        """Return whether advanced api is enabled."""
        return self._advanced_features

    @property
    def host(self) -> str:
        """Return the hostname of the device."""
        return self._host

    @property
    def serial(self) -> str:
        """Return the serial of the device."""
        return self._data.serial

    @property
    def description(self) -> str:
        """Return the Model Description."""
        return self._data.description
    
    @property
    def warranty_number(self) -> str:
        """Return the warranty number of the device."""
        return self._data.warranty_number
    
    @property
    def global_aqi(self) -> float:
        """Return the global air quality index"""
        return self._data.global_aqi
    
    @property
    def rooms(self) -> list[Healthbox3Room]:
        """Return all HB3 rooms"""
        return self._data.rooms

    async def async_get_data(self) -> any:
        """Get data from the API."""
        general_data = await self.request(
            method=METH_GET, endpoint="/v2/api/data/current"
        )
        self._data = Healthbox3DataObject(general_data, advanced_features=self._advanced_features)
        for room in self._data.rooms:
            room.boost = await self.async_get_room_boost_data(room_id=room.room_id)
        return general_data

    async def async_start_room_boost(
        self, room_id: int, boost_level: int, boost_timeout: int
    ) -> any:
        """Start Boosting HB3 Room."""
        data = {"enable": True, "level": boost_level, "timeout": boost_timeout}
        await self.request(
            method=METH_PUT,
            endpoint=f"/v2/api/boost/{room_id}",
            data=data,
        )

    async def async_stop_room_boost(self, room_id: int) -> any:
        """Stop Boosting HB3 Room."""
        data = {"enable": False}
        await self.request(
            method=METH_PUT,
            endpoint=f"/v2/api/boost/{room_id}",
            data=data,
        )

    async def async_get_room_boost_data(self, room_id: int) -> Healthbox3RoomBoost:
        """Get boost data from the API."""
        try:
            data = await self.request(
                method=METH_GET, endpoint=f"/v2/api/boost/{room_id}"
            )
            return Healthbox3RoomBoost(level=data["level"],enabled=data["enable"],remaining=data["remaining"])
        except:
            return Healthbox3RoomBoost()
        

    async def async_enable_advanced_api_features(self):
        """Enable advanced API Features."""
        if self._api_key:
            await self.request(
                method=METH_POST,
                endpoint="/v2/api/api_key",
                data=f"{self._api_key}",
                expect_json_error=True,
            )
            await asyncio.sleep(5)
            if await self._async_validate_advanced_api_features() == False:
                await self.close()
                raise Healthbox3ApiClientAuthenticationError
        else:
            raise Healthbox3ApiClientAuthenticationError

    async def async_validate_connectivity(self):
        """Validate API Connectivity."""
        await self.request(
            method=METH_GET, endpoint="/v2/api/data/current"
        )

    async def _async_validate_advanced_api_features(self) -> bool:
        """Validate API Advanced Features."""
        authentication_status = await self.request(
            method=METH_GET, endpoint="/v2/api/api_key/status"
        )
        if authentication_status["state"] != "valid":
            return False
        else:
            self._advanced_features = True
            return True

    async def request(self, endpoint: str, method: str = METH_GET, data: object = None, headers: dict = None, expect_json_error: bool = False) -> any:
        """Send request to the API."""
        if self._session is None:
            self._session = ClientSession()
            self._close_session = True

        url: str = f"http://{self.host}{endpoint}"

        _LOGGER.debug(f"{method}, {url}, {data}")

        try:
            async with async_timeout.timeout(self._request_timeout):
                response = await self._session.request(
                    method,
                    url,
                    headers=headers,
                    json=data
                )
                _LOGGER.debug("%s, %s", response.status, await response.text("utf-8"))
                if response.status in (401, 403):
                    raise Healthbox3ApiClientAuthenticationError(
                        "Invalid credentials",
                    )
                response.raise_for_status()

                if expect_json_error:
                    return await response.text()
                return await response.json()    
                        
        except asyncio.TimeoutError as exception:
            raise Healthbox3ApiClientCommunicationError(
                "Timeout occurred while connecting to the Healthbox device"
            ) from exception
        except (ClientError, ClientResponseError) as exception:
            raise Healthbox3ApiClientError(
                "Error occurred while communicating with the Healthbox device"
            ) from exception
        
    async def close(self) -> None:
        """Close client session."""
        _LOGGER.debug("Closing clientsession")
        if self._session and self._close_session:
            await self._session.close()   

    async def __aexit__(self, *_exc_info: any) -> None:
        """Async exit.
        Args:
            _exc_info: Exec type.
        """
        await self.close()        

class Healthbox3ApiClientError(Exception):
    """Exception to indicate a general API error."""


class Healthbox3ApiClientCommunicationError(Healthbox3ApiClientError):
    """Exception to indicate a communication error."""


class Healthbox3ApiClientAuthenticationError(Healthbox3ApiClientError):
    """Exception to indicate an authentication error."""