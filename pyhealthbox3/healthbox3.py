from __future__ import annotations

import asyncio

from aiohttp import ClientSession, ClientError, ClientResponseError
from aiohttp.hdrs import METH_GET, METH_PUT, METH_POST

import async_timeout

import logging

from .models import Healthbox3DataObject, Healthbox3Room, Healthbox3RoomBoost, Healthbox3WIFIConnectionDataObject

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
        """Return the global air quality index."""
        return self._data.global_aqi
    
    @property
    def error_count(self) -> int:
        """Return the device error count."""
        return self._data.error_count
    
    @property
    def rooms(self) -> list[Healthbox3Room]:
        """Return all HB3 rooms"""
        return self._data.rooms
    
    @property
    def firmware_version(self) -> str:
        """Return the Firmware Version."""
        return self._data.firmware_version
    
    @property
    def wifi(self) -> Healthbox3WIFIConnectionDataObject:
        """Return the WiFi Data."""
        return self._data.wifi

    async def async_get_data(self) -> any:
        """Get data from the API."""
        general_data = await self.request(
            method=METH_GET, endpoint="/v2/api/data/current"
        )
        self._data = Healthbox3DataObject(general_data, advanced_features=self._advanced_features)
        await self._async_get_errors()
        await self._async_get_global_core_data()
        await self._async_get_wifi_status()
        # await self._async_packages_data()
        for room in self._data.rooms:
            _LOGGER.debug(f"Found room: {room.name}")
            _LOGGER.debug(f"\tAirflow Ventilation Rate: {room.airflow_ventilation_rate}")
            _LOGGER.debug(f"\tAQI: {room.indoor_aqi}")
            _LOGGER.debug(f"\tCO²: {room.indoor_co2_concentration}")
            _LOGGER.debug(f"\tHumidity: {room.indoor_humidity}")
            _LOGGER.debug(f"\tTemperature: {room.indoor_temperature}")
            _LOGGER.debug(f"\tVOC PPM: {room.indoor_voc_ppm}")
            _LOGGER.debug(f"\tVOC µg/m³: {room.indoor_voc_microg_per_cubic}")

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
        
    async def _async_get_errors(self) -> list[dict] | None:
        """Get errors from the API."""
        try:
            _LOGGER.debug("Retreiving errors")
            data = await self.request(
                method=METH_GET, endpoint=f"/v2/device/error"
            )
            self._data.error_count = len(data)
            return data
        except:
            return None  
        finally:
            _LOGGER.debug(f"\tError Count: {self._data.error_count}")

    async def _async_get_global_core_data(self) -> dict | None:
        """Get global core data from the API."""
        try:
            
            _LOGGER.debug("Retreiving core data")
            data = await self.request(
                method=METH_GET, endpoint=f"/renson_core/v2/global"
            )
            if "firmware version" in data:
                self._data.firmware_version = data["firmware version"]
            return data
        except:
            return None  
        finally:
            _LOGGER.debug(f"\tFirmware Version: {self._data.firmware_version}")

    async def _async_get_wifi_status(self) -> Healthbox3WIFIConnectionDataObject | None:
        """Get WiFi status from the API."""
        try:
            
            _LOGGER.debug("Retreiving WiFi Status data")
            data = await self.request(
                method=METH_GET, endpoint=f"/renson_core/v1/wifi/client/status"
            )
            wifi_data = Healthbox3WIFIConnectionDataObject()

            wifi_data.status = data["status"] if "status" in data else None
            wifi_data.internet_connection = data["internet_connection"] if "internet_connection" in data else None
            wifi_data.ssid = data["ssid"] if "ssid" in data else None
            wifi_data.connection_error = data["connection_error"] if "connection_error" in data else None
            
            self._data.wifi = wifi_data

            return wifi_data
        except:
            return None  
        finally:
            _LOGGER.debug(f"\tStatus: {self._data.wifi.status}")
            _LOGGER.debug(f"\tInternet Connection: {self._data.wifi.internet_connection}")
            _LOGGER.debug(f"\tSSID: {self._data.wifi.ssid}")
            _LOGGER.debug(f"\tConnection Error: {self._data.wifi.status}")

    # async def _async_packages_data(self) -> dict | None:
    #     """Get packages data from the API."""
    #     try:
            
    #         _LOGGER.debug("Retreiving packages data")
    #         data = await self.request(
    #             method=METH_GET, endpoint=f"/renson_core/v1/packages"
    #         )
    #         if "installed" in data:
    #             active_app_version = [d for d in data["installed"] if d["version_active"] == True and d["name"] == "APP_hb3"]
    #             if len(active_app_version) == 1:
    #                 version_object = active_app_version[0]["version"]
    #                 version_object = map(str, version_object)
                    
    #                 version = ".".join(version_object) + f"_{ active_app_version[0]['date']}"
    #                 self._data.app_version = version
    #         return data
    #     except Exception as e:
    #         print(e)
    #         return None  
    #     finally:
    #         _LOGGER.debug(f"\tFirmware Version: {self._data.firmware_version}")

    async def async_enable_advanced_api_features(self, pre_validation: bool = True):
        """Enable advanced API Features."""
        if self._api_key:
            already_valid = False
            if pre_validation:
                _LOGGER.debug("Pre validating advanced API to check if already enabled.")
                already_valid = await self._async_validate_advanced_api_features()
            if not already_valid:
                _LOGGER.debug("Enabling Advanced API.")
                await self.request(
                    method=METH_POST,
                    endpoint="/v2/api/api_key",
                    data=f"{self._api_key}",
                    expect_json_error=True,
                )
                await asyncio.sleep(10)
                if await self._async_validate_advanced_api_features() == False:
                    await self.close()
                    raise Healthbox3ApiClientAuthenticationError
            else:
                _LOGGER.debug("Advanced API already enabled.")
        else:
            raise Healthbox3ApiClientAuthenticationError

    async def async_validate_connectivity(self):
        """Validate API Connectivity."""
        _LOGGER.debug("Validating Connectivity")
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

        # _LOGGER.debug(f"{method}, {url}, {data}")

        try:
            async with async_timeout.timeout(self._request_timeout):
                response = await self._session.request(
                    method,
                    url,
                    headers=headers,
                    json=data
                )
                # _LOGGER.debug("%s, %s", response.status, await response.text("utf-8"))
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