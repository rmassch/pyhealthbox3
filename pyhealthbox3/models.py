"""Healthbox 3 Models."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

class Healthbox3RoomBoost:
    """Healthbox 3 Room Boost object."""

    level: float
    enabled: bool
    remaining: int

    def __init__(
        self, level: float = None, enabled: bool = False, remaining: int = None
    ) -> None:
        """Initialize the HB3 Room Boost."""
        self.level = level
        self.enabled = enabled
        self.remaining = remaining


class Healthbox3Room:
    """Healthbox 3 Room object."""

    boost: Healthbox3RoomBoost = Healthbox3RoomBoost()

    def __init__(self, room_id: int, room_data: object, advanced_features: bool = False) -> None:
        """Initialize the HB3 Room."""
        self._advanced_features = advanced_features
        self.room_id: int = room_id
        self.name: str = room_data["name"]
        self.type: str = room_data["type"]
        self.sensors_data: list = room_data["sensor"]
        self.room_type: str = room_data["type"]


    @property
    def indoor_temperature(self) -> Decimal | None:
        """HB3 Indoor Temperature."""
        temperature = None
        if self._advanced_features:
            temperature = [
                sensor["parameter"]["temperature"]["value"]
                for sensor in self.sensors_data
                if "temperature" in sensor["parameter"]
            ][0]
        return temperature

    @property
    def indoor_humidity(self) -> Decimal | None:
        """HB3 Indoor Humidity."""
        humidity = None
        if self._advanced_features:
            humidity =  [
                sensor["parameter"]["humidity"]["value"]
                for sensor in self.sensors_data
                if "humidity" in sensor["parameter"]
            ][0]
        return humidity

    @property
    def indoor_co2_concentration(self) -> Decimal | None:
        """HB3 Indoor CO2 Concentration."""
        co2_concentration = None
        if self._advanced_features:
            co2_concentration = [
                sensor["parameter"]["concentration"]["value"]
                for sensor in self.sensors_data
                if "concentration" in sensor["parameter"]
            ][0]
        return co2_concentration


    @property
    def indoor_aqi(self) -> Decimal | None:
        """HB3 Indoor Air Quality Index."""
        aqi = None
        if self._advanced_features:
            aqi = [
                sensor["parameter"]["index"]["value"]
                for sensor in self.sensors_data
                if "index" in sensor["parameter"]
            ][0]
        return aqi


class Healthbox3DataObject:
    """Healthbox3 Data Object."""

    serial: str
    description: str
    warranty_number: str

    global_aqi: float = None

    rooms: list[Healthbox3Room]

    def __init__(self, data: any, advanced_features: bool = False) -> None:
        """Initialize."""
        self.serial = data["serial"]
        self.description = data["description"]
        self.warranty_number = data["warranty_number"]

        self.global_aqi = self._get_global_aqi_from_data(data)

        hb3_rooms: list[Healthbox3Room] = []
        for room in data["room"]:
            hb3_room = Healthbox3Room(room, data["room"][room], advanced_features=advanced_features)
            hb3_rooms.append(hb3_room)

        self.rooms = hb3_rooms

    def _get_global_aqi_from_data(self, data: any) -> float | None:
        """Set Global AQI from Data Object."""
        sensors = data["sensor"]
        for sensor in sensors:
            if sensor["type"] == "global air quality index":
                return sensor["parameter"]["index"]["value"]
        return None
