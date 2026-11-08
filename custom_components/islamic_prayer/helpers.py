"""Shared helpers for the Islamic Prayers integration."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo

from .const import (
    CALC_METHODS,
    CONF_CALC_METHOD,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    DEFAULT_CALC_METHOD,
    DOMAIN,
    PRAYER_NEXT_TOGGLE_MAP,
    PRAYER_OFFSET_MAP,
)


def _config_value(entry: ConfigEntry, key: str, default: Any = None) -> Any:
    """Return the effective config value (options override data)."""
    return entry.options.get(key, entry.data.get(key, default))


def get_calc_method(entry: ConfigEntry) -> str:
    """Return the configured calculation method."""
    method = _config_value(entry, CONF_CALC_METHOD, DEFAULT_CALC_METHOD)
    return method if method in CALC_METHODS else DEFAULT_CALC_METHOD


def get_latitude(entry: ConfigEntry) -> float:
    """Return the configured latitude."""
    return float(_config_value(entry, CONF_LATITUDE, 0.0))


def get_longitude(entry: ConfigEntry) -> float:
    """Return the configured longitude."""
    return float(_config_value(entry, CONF_LONGITUDE, 0.0))


def get_offsets(entry: ConfigEntry) -> dict[str, int]:
    """Return per-prayer offsets in minutes keyed by prayer."""
    offsets: dict[str, int] = {}
    for prayer_key, offset_key in PRAYER_OFFSET_MAP.items():
        try:
            offsets[prayer_key] = int(_config_value(entry, offset_key, 0))
        except (TypeError, ValueError):
            offsets[prayer_key] = 0
    return offsets


def get_next_prayer_toggles(entry: ConfigEntry) -> dict[str, bool]:
    """Return the Next Prayer toggles keyed by prayer."""
    return {
        prayer_key: bool(_config_value(entry, toggle_key, True))
        for prayer_key, toggle_key in PRAYER_NEXT_TOGGLE_MAP.items()
    }


def get_offset_config(entry: ConfigEntry) -> dict[str, int]:
    """Return per-prayer offsets keyed by config key."""
    return {
        PRAYER_OFFSET_MAP[prayer_key]: minutes
        for prayer_key, minutes in get_offsets(entry).items()
    }


def get_toggle_config(entry: ConfigEntry) -> dict[str, bool]:
    """Return Next Prayer toggles keyed by config key."""
    return {
        PRAYER_NEXT_TOGGLE_MAP[prayer_key]: enabled
        for prayer_key, enabled in get_next_prayer_toggles(entry).items()
    }


def config_signature(entry: ConfigEntry) -> tuple:
    """Return the settings that require a reload when changed.

    Offsets and Next Prayer toggles are applied live by the coordinator, so
    they are deliberately excluded from this signature.
    """
    return (
        get_latitude(entry),
        get_longitude(entry),
        get_calc_method(entry),
    )


def device_info(entry: ConfigEntry) -> DeviceInfo:
    """Return the device info shared by all entities of an entry."""
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name="Islamic Prayers",
        manufacturer="adhanpy",
        model=CALC_METHODS.get(get_calc_method(entry), "Unknown"),
    )
