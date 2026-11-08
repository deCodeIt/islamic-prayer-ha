"""Number platform for Islamic Prayers - live per-prayer time offsets."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    OFFSET_MAX_MINUTES,
    OFFSET_MIN_MINUTES,
    OFFSET_STEP_MINUTES,
    PRAYER_ICONS,
    PRAYER_NAMES,
    PRAYER_OFFSET_MAP,
    PRAYERS,
)
from .coordinator import IslamicPrayerTimesCoordinator
from .helpers import device_info


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up a live offset slider for every prayer."""
    coordinator: IslamicPrayerTimesCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        PrayerOffsetNumber(coordinator, entry, prayer_key) for prayer_key in PRAYERS
    )


class PrayerOffsetNumber(
    CoordinatorEntity[IslamicPrayerTimesCoordinator], NumberEntity
):
    """Live-adjustable offset (minutes) for a single prayer.

    The slider is hidden whenever the prayer is excluded from the Next Prayer
    sensor, so both follow the same per-prayer enable setting.
    """

    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = OFFSET_MIN_MINUTES
    _attr_native_max_value = OFFSET_MAX_MINUTES
    _attr_native_step = OFFSET_STEP_MINUTES
    _attr_native_unit_of_measurement = "min"
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: IslamicPrayerTimesCoordinator,
        entry: ConfigEntry,
        prayer_key: str,
    ) -> None:
        super().__init__(coordinator)
        self._prayer_key = prayer_key
        self._entry = entry
        self._offset_key = PRAYER_OFFSET_MAP[prayer_key]
        self._enabled = self._is_enabled()
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_{prayer_key}_offset"
        self._attr_name = f"{PRAYER_NAMES.get(prayer_key, prayer_key)} offset"
        self._attr_icon = PRAYER_ICONS.get(prayer_key)
        self._attr_entity_registry_visible_default = self._enabled
        self._attr_device_info = device_info(entry)

    def _is_enabled(self) -> bool:
        """Return whether this prayer is part of the enabled prayer set."""
        return self.coordinator.next_prayer_toggles.get(self._prayer_key, True)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Hide or show the slider when the prayer's enable setting changes."""
        enabled = self._is_enabled()
        if enabled != self._enabled:
            self._enabled = enabled
            self._async_apply_visibility(enabled)
        super()._handle_coordinator_update()

    @callback
    def _async_apply_visibility(self, enabled: bool) -> None:
        """Mirror the prayer's enable setting onto the registry hidden state."""
        if self.entity_id is None or self.registry_entry is None:
            return
        registry = er.async_get(self.hass)
        entry = registry.async_get(self.entity_id)
        if entry is None:
            return
        if enabled:
            if entry.hidden_by == er.RegistryEntryHider.INTEGRATION:
                registry.async_update_entity(self.entity_id, hidden_by=None)
        elif entry.hidden_by is None:
            registry.async_update_entity(
                self.entity_id, hidden_by=er.RegistryEntryHider.INTEGRATION
            )

    @property
    def native_value(self) -> float:
        """Return the current offset in minutes."""
        return self.coordinator.offsets.get(self._prayer_key, 0)

    async def async_set_native_value(self, value: float) -> None:
        """Apply the offset live and persist it for restarts."""
        minutes = int(round(value))
        await self.coordinator.async_set_offset(self._prayer_key, minutes)
        self.hass.config_entries.async_update_entry(
            self._entry,
            options={**self._entry.options, self._offset_key: minutes},
        )
