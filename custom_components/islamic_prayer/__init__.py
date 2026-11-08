"""Islamic Prayers integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import IslamicPrayerTimesCoordinator
from .helpers import (
    config_signature,
    get_calc_method,
    get_latitude,
    get_longitude,
    get_next_prayer_toggles,
    get_offsets,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["event", "number", "sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Islamic Prayers from a config entry."""
    coordinator = IslamicPrayerTimesCoordinator(
        hass,
        latitude=get_latitude(entry),
        longitude=get_longitude(entry),
        calc_method=get_calc_method(entry),
        offsets=get_offsets(entry),
        next_prayer_toggles=get_next_prayer_toggles(entry),
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Apply live settings, reloading only when location or method changed."""
    coordinator: IslamicPrayerTimesCoordinator | None = hass.data.get(
        DOMAIN, {}
    ).get(entry.entry_id)
    if coordinator is None:
        return

    if coordinator.settings_signature != config_signature(entry):
        await hass.config_entries.async_reload(entry.entry_id)
        return

    if coordinator.apply_settings(
        get_offsets(entry), get_next_prayer_toggles(entry)
    ):
        await coordinator.async_recalculate()


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
