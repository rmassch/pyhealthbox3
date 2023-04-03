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
    enabled_sensors: list[str] = []
    
    def __init__(self, room_id: int, room_data: object, advanced_features: bool = False) -> None:
        """Initialize the HB3 Room."""
        self._advanced_features = advanced_features
        self.room_id: int = room_id
        self.name: str = room_data["name"]
        self.type: str = room_data["type"]
        self.sensors_data: list = room_data["sensor"]
        self.enabled_sensors = [sensor["type"] for sensor in self.sensors_data]
        self.room_type: str = room_data["type"]
        self._parameters: dict = room_data["parameter"]
        self._actuator: list[dict] = room_data["actuator"]
        self._profile: str = room_data["profile_name"]


    @property
    def indoor_temperature(self) -> Decimal | None:
        """HB3 Indoor Temperature."""
        temperature = None
        sensor_type: str = "indoor temperature"
        if self._advanced_features and sensor_type in self.enabled_sensors:
            temperature = self._get_sensor_value(sensor_type)
        return temperature

    @property
    def indoor_humidity(self) -> Decimal | None:
        """HB3 Indoor Humidity."""
        humidity = None
        sensor_type: str = "indoor relative humidity" 
        if self._advanced_features and sensor_type in self.enabled_sensors:
            humidity = self._get_sensor_value(sensor_type)
        return humidity

    @property
    def indoor_co2_concentration(self) -> Decimal | None:
        """HB3 Indoor CO2 Concentration."""
        co2_concentration = None
        sensor_type: str = "indoor CO2"
        if self._advanced_features and sensor_type in self.enabled_sensors:
            co2_concentration = self._get_sensor_value(sensor_type)
        return co2_concentration

    @property
    def indoor_aqi(self) -> Decimal | None:
        """HB3 Indoor Air Quality Index."""
        aqi = None
        sensor_type: str = "indoor air quality index"
        if self._advanced_features and sensor_type in self.enabled_sensors:
            aqi = self._get_sensor_value(sensor_type)
        return aqi

    @property
    def indoor_voc_ppm(self) -> Decimal | None:
        """HB3 Volatile Organic Compounds."""
        ppm = None
        sensor_type: str = "indoor volatile organic compounds"
        if self._advanced_features and sensor_type in self.enabled_sensors:
            ppm = self._get_sensor_value(sensor_type)
        return ppm
    
    @property
    def indoor_voc_microg_per_cubic(self) -> Decimal | None:
        """HB3 Volatile Organic Compounds."""
        mgpc = None
        sensor_type: str = "indoor volatile organic compounds"
        if self._advanced_features and sensor_type in self.enabled_sensors:
            mgpc = self._get_sensor_value(sensor_type)
            if mgpc:
                mgpc = mgpc * 1000
        return mgpc
    
    @property
    def airflow_ventilation_rate(self) -> float | None:
        """HB3 Airflow Ventilation Rate."""
        ventilation_rate = self._get_airflow_ventilation_rate()
        return ventilation_rate

    @property
    def profile_name(self) -> str | None:
        """HB3 Room Profile Name."""
        return self._profile.capitalize()
     
    def _validate_sensor(self, sensor: dict, sensor_key: str) -> bool:
        """Validate the sensor."""
        valid: bool = False
        if "parameter" in sensor:

            "Sensors are sometimes empty ..."
            if sensor_key in sensor["parameter"]:
                valid =  True
            
        return valid

    def _get_airflow_ventilation_rate(self) -> float | None:
        """Extract the airflow ventilation rate."""
        nominal: float = None
        offset: float = None
        flow_rate: float = None

        # Nominal
        try:
            nominal = self._parameters["nominal"]["value"]
        except KeyError:
            return None

        # Offset
        try:
            offset = self._parameters["offset"]["value"]
        except KeyError:            
            offset = 0

        # Flow Rate
        flow_rate_sensors: list[dict] = [
            x for x in self._actuator if x["type"] == "air valve"
        ]
        if len(flow_rate_sensors) == 0:
            return None
        
        try:
            flow_rate: float = flow_rate_sensors[0]["parameter"]["flow_rate"]["value"]
        except KeyError:
            return None


        ventilation_rate: float = flow_rate / (nominal + offset)
        return ventilation_rate

    def _get_sensor_value(self, sensor_type: str) -> float | None:
        """Get sensor value."""
        sensor_type_keys: dict = {
            "indoor volatile organic compounds": "concentration",
            "indoor volatile organic compounds": "concentration",
            "indoor air quality index": "index",
            "indoor CO2": "concentration",
            "indoor relative humidity": "humidity",
            "indoor temperature": "temperature"
        }
        sensor: dict = [sensor for sensor in self.sensors_data if sensor_type in sensor["type"]][0]
        sensor_key = sensor_type_keys[sensor_type]
        valid = self._validate_sensor(sensor, sensor_key=sensor_key)
        if valid:
            return sensor["parameter"][sensor_key]["value"]
        else:
            return None




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
