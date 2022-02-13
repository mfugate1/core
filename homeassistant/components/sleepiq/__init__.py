"""Support for SleepIQ from SleepNumber."""
from __future__ import annotations

import dataclasses
from datetime import timedelta
import logging

from sleepyq import Sleepyq
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
    Platform,
)
from homeassistant.core import HomeAssistant, callback
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import (
    BED,
    CONFIG_ENTRY_UPDATE_SIGNAL_TEMPLATE,
    DOMAIN,
    ICON_OCCUPIED,
    SENSOR_TYPES,
)

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: {
            vol.Required(CONF_USERNAME): cv.string,
            vol.Required(CONF_PASSWORD): cv.string,
        }
    },
    extra=vol.ALLOW_EXTRA,
)

DATA_SLEEPIQ = "data_sleepiq"

DEFAULT_COMPONENT_NAME = "SleepIQ {}"
DEFAULT_SCAN_INTERVAL = timedelta(seconds=60)

PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the SleepIQ config entry."""
    client = Sleepyq(entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD])
    try:
        await hass.async_add_executor_job(client.login)
    except ValueError:
        _LOGGER.error("SleepIQ login failed, double check your username and password")
        return False

    if CONF_SCAN_INTERVAL in entry.data:
        update_interval = timedelta(seconds=entry.data[CONF_SCAN_INTERVAL])
    else:
        update_interval = DEFAULT_SCAN_INTERVAL

    coordinator = SleepIQDataUpdateCoordinator(
        hass,
        client=client,
        update_interval=update_interval,
        username=entry.data[CONF_USERNAME],
    )

    # Call the SleepIQ API to refresh data
    await coordinator.async_config_entry_first_refresh()

    # Listen to config entry updates
    entry.async_on_unload(entry.add_update_listener(_async_signal_options_update))
    entry.async_on_unload(
        async_dispatcher_connect(
            hass,
            _config_entry_update_signal_name(entry),
            coordinator.async_update_config,
        )
    )

    hass.data[DATA_SLEEPIQ] = SleepIQHassData()
    hass.data[DATA_SLEEPIQ].coordinators[entry.data[CONF_USERNAME]] = coordinator

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload the config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        config_entry, PLATFORMS
    )

    hass.data[DATA_SLEEPIQ].coordinators.pop(config_entry.data[CONF_USERNAME])

    return unload_ok


def _config_entry_update_signal_name(config_entry: ConfigEntry) -> str:
    """Get signal name for updates to a config entry."""
    return CONFIG_ENTRY_UPDATE_SIGNAL_TEMPLATE.format(config_entry.unique_id)


async def _async_signal_options_update(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> None:
    """Signal config entry options update."""
    async_dispatcher_send(
        hass, _config_entry_update_signal_name(config_entry), config_entry
    )


class SleepIQDataUpdateCoordinator(DataUpdateCoordinator[dict[str, dict]]):
    """SleepIQ data update coordinator."""

    def __init__(
        self,
        hass: HomeAssistant,
        *,
        client: Sleepyq,
        update_interval: timedelta,
        username: str,
    ) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass, _LOGGER, name=f"{username}@SleepIQ", update_interval=update_interval
        )
        self.client = client

    async def async_update_config(self, config_entry: ConfigEntry) -> None:
        """Handle config update."""
        self.update_interval = timedelta(
            seconds=config_entry.options[CONF_SCAN_INTERVAL]
        )

    async def _async_update_data(self) -> dict[str, dict]:
        return await self.hass.async_add_executor_job(self.update_data)

    def update_data(self) -> dict[str, dict]:
        """Get latest data from the client."""
        data = {}
        for bed in self.client.beds_with_sleeper_status():
            data[bed.bed_id] = {BED: bed}

        return data


@dataclasses.dataclass
class SleepIQHassData:
    """Home Assistant SleepIQ runtime data."""

    coordinators: dict[str, SleepIQDataUpdateCoordinator] = dataclasses.field(
        default_factory=dict
    )


class SleepIQSensor(CoordinatorEntity):
    """Implementation of a SleepIQ sensor."""

    _attr_icon = ICON_OCCUPIED

    def __init__(
        self,
        coordinator: SleepIQDataUpdateCoordinator,
        bed_id: str,
        side: str,
        name: str,
    ) -> None:
        """Initialize the SleepIQ side entity."""
        super().__init__(coordinator)
        self.bed_id = bed_id
        self.side = side

        self._async_update_attrs()

        self._attr_name = f"SleepNumber {self._bed.name} {self._side.sleeper.first_name} {SENSOR_TYPES[name]}"
        self._attr_unique_id = f"{self.bed_id}_{self._side.sleeper.first_name}_{name}"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._async_update_attrs()
        super()._handle_coordinator_update()

    @callback
    def _async_update_attrs(self) -> None:
        """Update sensor attributes."""
        self._bed = self.coordinator.data[self.bed_id][BED]
        self._side = getattr(self._bed, self.side)
