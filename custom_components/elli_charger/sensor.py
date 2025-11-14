"""Support for Elli Charger sensors."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Elli Charger sensors based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []

    # Add station (charger) sensors with their corresponding session sensors
    if stations := coordinator.data.get("stations"):
        for station in stations:
            station_id = station.id
            # Wallbox status sensor
            entities.append(
                ElliWallboxSensor(coordinator, station_id, entry.entry_id)
            )
            # Last session sensor
            entities.append(
                ElliLastSessionSensor(coordinator, station_id, entry.entry_id)
            )
            # Session energy sensor (for Energy Dashboard)
            entities.append(
                ElliSessionEnergySensor(coordinator, station_id, entry.entry_id)
            )

    async_add_entities(entities)


class ElliWallboxSensor(CoordinatorEntity, SensorEntity):
    """Representation of an Elli Wallbox sensor."""

    def __init__(
        self, coordinator, station_id: str, entry_id: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._station_id = station_id
        self._attr_icon = "mdi:ev-station"

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{self.coordinator.config_entry.entry_id}_wallbox_{self._station_id}"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        station = self._get_station()
        if station:
            return f"Elli Wallbox {station.name}"
        return f"Elli Wallbox {self._station_id}"

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        if self._is_charging():
            return "Charging"
        elif self._has_active_session():
            return "Connected"
        return "Idle"

    def _get_station(self):
        """Get the station object."""
        stations = self.coordinator.data.get("stations", [])
        for station in stations:
            if station.id == self._station_id:
                return station
        return None

    def _get_latest_session(self):
        """Get the latest session for this station."""
        sessions = self.coordinator.data.get("sessions", [])
        for session in sessions:
            if session.station_id == self._station_id:
                return session
        return None

    def _has_active_session(self) -> bool:
        """Check if station has an active session."""
        session = self._get_latest_session()
        return session and session.lifecycle_state == "active"

    def _is_charging(self) -> bool:
        """Check if station is currently charging."""
        session = self._get_latest_session()
        if not session:
            return False
        # Check if charging (either by charging_state or by power > 0)
        if session.charging_state and "charging" in session.charging_state.lower():
            return True
        if session.momentary_charging_speed_watts and session.momentary_charging_speed_watts > 0:
            return True
        return False

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        station = self._get_station()
        if not station:
            return {}

        attrs = {
            "station_id": station.id,
            "name": station.name,
        }
        if station.serial_number:
            attrs["serial_number"] = station.serial_number
        if station.model:
            attrs["model"] = station.model
        if station.firmware_version:
            attrs["firmware_version"] = station.firmware_version

        return attrs


class ElliLastSessionSensor(CoordinatorEntity, SensorEntity):
    """Representation of an Elli last/current session sensor."""

    def __init__(
        self, coordinator, station_id: str, entry_id: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._station_id = station_id
        self._attr_icon = "mdi:ev-plug-type2"

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{self.coordinator.config_entry.entry_id}_wallbox_{self._station_id}_last_session"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        station = self._get_station()
        if station:
            return f"Elli Wallbox {station.name} Last Session"
        return f"Elli Wallbox {self._station_id} Last Session"

    def _get_station(self):
        """Get the station object."""
        stations = self.coordinator.data.get("stations", [])
        for station in stations:
            if station.id == self._station_id:
                return station
        return None

    def _get_latest_session(self):
        """Get the latest session for this station."""
        sessions = self.coordinator.data.get("sessions", [])
        for session in sessions:
            if session.station_id == self._station_id:
                return session
        return None

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor (charging state)."""
        session = self._get_latest_session()
        if not session:
            return "idle"

        # Prefer charging_state field
        if session.charging_state:
            return session.charging_state
        # Fall back to lifecycle_state
        if session.lifecycle_state:
            return session.lifecycle_state
        return "unknown"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        session = self._get_latest_session()
        if not session:
            return {}

        attrs = {
            "session_id": session.id,
            "station_id": session.station_id,
        }

        # Energy and power
        if session.energy_consumption_wh is not None:
            attrs["session_energy"] = round(session.energy_consumption_wh / 1000, 2)
        if session.momentary_charging_speed_watts is not None:
            attrs["session_power"] = session.momentary_charging_speed_watts

        # State information
        if session.lifecycle_state:
            attrs["lifecycle_state"] = session.lifecycle_state
        if session.charging_state:
            attrs["charging_state"] = session.charging_state

        # Authentication information
        if session.authentication_method:
            attrs["authentication_method"] = session.authentication_method
        if session.rfid_card_serial_number:
            attrs["rfid_card"] = session.rfid_card_serial_number
        if session.connector_id:
            attrs["connector_id"] = session.connector_id

        # Timestamps
        if session.start_date_time:
            attrs["start_time"] = session.start_date_time
        if session.end_date_time:
            attrs["end_time"] = session.end_date_time
        if session.last_updated:
            attrs["last_updated"] = session.last_updated

        return attrs


class ElliSessionEnergySensor(CoordinatorEntity, SensorEntity):
    """Representation of an Elli session energy sensor for Energy Dashboard."""

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR

    def __init__(
        self, coordinator, station_id: str, entry_id: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._station_id = station_id
        self._attr_icon = "mdi:battery-charging"

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{self.coordinator.config_entry.entry_id}_wallbox_{self._station_id}_session_energy"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        station = self._get_station()
        if station:
            return f"Elli Wallbox {station.name} Session Energy"
        return f"Elli Wallbox {self._station_id} Session Energy"

    def _get_station(self):
        """Get the station object."""
        stations = self.coordinator.data.get("stations", [])
        for station in stations:
            if station.id == self._station_id:
                return station
        return None

    def _get_latest_session(self):
        """Get the latest session for this station."""
        sessions = self.coordinator.data.get("sessions", [])
        for session in sessions:
            if session.station_id == self._station_id:
                return session
        return None

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor (energy in kWh)."""
        session = self._get_latest_session()
        if session and session.energy_consumption_wh is not None:
            # Convert Wh to kWh
            return round(session.energy_consumption_wh / 1000, 2)
        return None
