"""Support for SleepIQ sensors."""
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_USERNAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DATA_SLEEPIQ, SleepIQDataUpdateCoordinator, SleepIQSensor
from .const import BED, ICON_EMPTY, ICON_OCCUPIED, IS_IN_BED, SIDES


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the SleepIQ bed binary sensors."""
    coordinator = hass.data[DATA_SLEEPIQ].coordinators[config_entry.data[CONF_USERNAME]]
    entities = []

    for bed_id in coordinator.data:
        for side in SIDES:
            if getattr(coordinator.data[bed_id][BED], side) is not None:
                entities.append(IsInBedBinarySensor(coordinator, bed_id, side))

    async_add_entities(entities)


class IsInBedBinarySensor(SleepIQSensor, BinarySensorEntity):
    """Implementation of a SleepIQ presence sensor."""

    _attr_device_class = BinarySensorDeviceClass.OCCUPANCY

    def __init__(
        self,
        coordinator: SleepIQDataUpdateCoordinator,
        bed_id: str,
        side: str,
    ) -> None:
        """Initialize the SleepIQ bed side binary sensor."""
        super().__init__(coordinator, bed_id, side, IS_IN_BED)

    @callback
    def _async_update_attrs(self) -> None:
        """Update sensor attributes."""
        super()._async_update_attrs()
        self._attr_is_on = getattr(self._side, IS_IN_BED)
        self._attr_icon = ICON_OCCUPIED if self.is_on else ICON_EMPTY
