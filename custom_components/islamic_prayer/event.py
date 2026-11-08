"""Event platform for Islamic Prayers."""

from __future__ import annotations

from homeassistant.components.event import EventEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, EVENT_PRAYER_TIME, EVENT_TYPES, PRAYER_NAMES
from .coordinator import IslamicPrayerTimesCoordinator
from .helpers import device_info


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
        self._attr_device_info = device_info(entry)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        while self.coordinator.arrived_prayers:
            prayer_key = self.coordinator.arrived_prayers.pop(0)
            self._trigger_event(
                prayer_key,
                {"name": PRAYER_NAMES.get(prayer_key, prayer_key)},
            )
        self.async_write_ha_state()
