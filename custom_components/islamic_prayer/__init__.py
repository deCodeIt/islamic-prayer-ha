"""Islamic Prayer Times integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_CALC_METHOD,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    DEFAULT_CALC_METHOD,
    DOMAIN,
    PRAYER_NEXT_TOGGLE_MAP,
    PRAYER_OFFSET_MAP,
)
from .coordinator import IslamicPrayerTimesCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["event", "sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Islamic Prayer Times from a config entry."""
    data = entry.data

    offsets = {
        prayer_key: int(data.get(offset_key, 0))
        for prayer_key, offset_key in PRAYER_OFFSET_MAP.items()
    }

    next_prayer_toggles = {
        prayer_key: data.get(toggle_key, True)
        for prayer_key, toggle_key in PRAYER_NEXT_TOGGLE_MAP.items()
    }

    coordinator = IslamicPrayerTimesCoordinator(
        hass,
        latitude=data[CONF_LATITUDE],
        longitude=data[CONF_LONGITUDE],
        calc_method=data.get(CONF_CALC_METHOD, DEFAULT_CALC_METHOD),
        offsets=offsets,
        next_prayer_toggles=next_prayer_toggles,
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload integration when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
