"""Event platform for Islamic Prayer Times."""

from __future__ import annotations

from homeassistant.components.event import EventEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CALC_METHODS,
    CONF_CALC_METHOD,
    DEFAULT_CALC_METHOD,
    DOMAIN,
    EVENT_PRAYER_TIME,
    EVENT_TYPES,
    PRAYER_NAMES,
)
from .coordinator import IslamicPrayerTimesCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up prayer time event entity from a config entry."""
    coordinator: IslamicPrayerTimesCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([PrayerTimeEvent(coordinator, entry)])


class PrayerTimeEvent(
    CoordinatorEntity[IslamicPrayerTimesCoordinator], EventEntity
):
    """Event entity that fires when a prayer time arrives."""

    _attr_has_entity_name = True
    _attr_translation_key = EVENT_PRAYER_TIME
    _attr_event_types = EVENT_TYPES

    def __init__(
        self,
        coordinator: IslamicPrayerTimesCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_{EVENT_PRAYER_TIME}"
        self._attr_name = "Prayer Time"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Islamic Prayer Times",
            manufacturer="adhanpy",
            model=CALC_METHODS.get(
                entry.data.get(CONF_CALC_METHOD, DEFAULT_CALC_METHOD), "Unknown"
            ),
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        prayer_key = self.coordinator.last_arrived_prayer
        if prayer_key is not None:
            self._trigger_event(
                prayer_key,
                {"name": PRAYER_NAMES.get(prayer_key, prayer_key)},
            )
            self.coordinator.last_arrived_prayer = None
        self.async_write_ha_state()
