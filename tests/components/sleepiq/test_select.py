"""Tests for the SleepIQ select platform."""
from homeassistant.components.select import DOMAIN
from homeassistant.const import ATTR_FRIENDLY_NAME, ATTR_ICON
from homeassistant.helpers import entity_registry as er

from tests.components.sleepiq.conftest import (
    BED_ID,
    BED_NAME,
    BED_NAME_LOWER,
    PRESET_L_STATE,
    PRESET_R_STATE,
    setup_platform,
)


async def test_foundation_preset(hass, mock_asyncsleepiq):
    """Test the SleepIQ select entity for foundation presets."""
    entry = await setup_platform(hass, DOMAIN)
    entity_registry = er.async_get(hass)

    state = hass.states.get(
        f"select.sleepnumber_{BED_NAME_LOWER}_foundation_preset_right"
    )
    assert state.state == PRESET_R_STATE
    assert state.attributes.get(ATTR_ICON) == "mdi:bed"
    assert (
        state.attributes.get(ATTR_FRIENDLY_NAME)
        == f"SleepNumber {BED_NAME} Foundation Preset Right"
    )

    entry = entity_registry.async_get(
        f"select.sleepnumber_{BED_NAME_LOWER}_foundation_preset_right"
    )
    assert entry
    assert entry.unique_id == f"{BED_ID}_preset_R"

    state = hass.states.get(
        f"select.sleepnumber_{BED_NAME_LOWER}_foundation_preset_left"
    )
    assert state.state == PRESET_L_STATE
    assert state.attributes.get(ATTR_ICON) == "mdi:bed"
    assert (
        state.attributes.get(ATTR_FRIENDLY_NAME)
        == f"SleepNumber {BED_NAME} Foundation Preset Left"
    )

    entry = entity_registry.async_get(
        f"select.sleepnumber_{BED_NAME_LOWER}_foundation_preset_left"
    )
    assert entry
    assert entry.unique_id == f"{BED_ID}_preset_L"
