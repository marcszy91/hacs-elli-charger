"""The Elli Charger integration."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from elli_client import ElliAPIClient

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

UPDATE_INTERVAL = timedelta(minutes=5)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Elli Charger from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Initialize the API client
    client = ElliAPIClient()

    # Login with user credentials
    try:
        await hass.async_add_executor_job(
            client.login,
            entry.data[CONF_EMAIL],
            entry.data[CONF_PASSWORD]
        )
    except Exception as err:
        _LOGGER.error("Failed to login to Elli API: %s", err)
        return False

    # Create coordinator for data updates
    coordinator = ElliDataUpdateCoordinator(hass, client, entry.data)

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Forward the setup to the sensor platform
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        coordinator.client.close()

    return unload_ok


class ElliDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Elli data from the API."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: ElliAPIClient,
        config_data: dict
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self.client = client
        self._email = config_data[CONF_EMAIL]
        self._password = config_data[CONF_PASSWORD]

    async def _async_update_data(self) -> dict:
        """Fetch data from API endpoint."""
        try:
            # Ensure we're authenticated (token might have expired)
            if not self.client.access_token:
                await self.hass.async_add_executor_job(
                    self.client.login,
                    self._email,
                    self._password
                )

            # Fetch charging sessions
            sessions = await self.hass.async_add_executor_job(
                self.client.get_charging_sessions
            )

            # Fetch stations (chargers)
            stations = await self.hass.async_add_executor_job(
                self.client.get_stations
            )

            # Fetch firmware information and merge with stations
            try:
                firmware_stations = await self.hass.async_add_executor_job(
                    self.client.get_firmware_info
                )
                # Create a map of station_id -> firmware_info
                firmware_map = {s.id: s.installed_firmware for s in firmware_stations if s.installed_firmware}

                # Merge firmware info into stations
                for station in stations:
                    if station.id in firmware_map:
                        station.installed_firmware = firmware_map[station.id]
                        station.firmware_version = firmware_map[station.id].version
            except Exception as fw_err:
                _LOGGER.warning("Could not fetch firmware info: %s", fw_err)

            return {
                "sessions": sessions,
                "stations": stations,
            }
        except Exception as err:
            _LOGGER.error("Error communicating with API: %s", err)
            # Try to re-authenticate on error
            try:
                await self.hass.async_add_executor_job(
                    self.client.login,
                    self._email,
                    self._password
                )
                # Retry once after re-authentication
                sessions = await self.hass.async_add_executor_job(
                    self.client.get_charging_sessions
                )
                stations = await self.hass.async_add_executor_job(
                    self.client.get_stations
                )
                # Try to fetch firmware info again
                try:
                    firmware_stations = await self.hass.async_add_executor_job(
                        self.client.get_firmware_info
                    )
                    firmware_map = {s.id: s.installed_firmware for s in firmware_stations if s.installed_firmware}
                    for station in stations:
                        if station.id in firmware_map:
                            station.installed_firmware = firmware_map[station.id]
                            station.firmware_version = firmware_map[station.id].version
                except Exception as fw_err:
                    _LOGGER.warning("Could not fetch firmware info: %s", fw_err)

                return {
                    "sessions": sessions,
                    "stations": stations,
                }
            except Exception as retry_err:
                raise UpdateFailed(f"Error communicating with API: {retry_err}") from retry_err
