"""Sensor platform for Islamic Prayer Times."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CALC_METHODS,
    CONF_CALC_METHOD,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    DEFAULT_CALC_METHOD,
    DOMAIN,
    PRAYER_NAMES,
    PRAYER_NEXT,
    PRAYER_OFFSET_MAP,
    PRAYERS,
)
from .coordinator import IslamicPrayerTimesCoordinator, PrayerTimeData


def _device_info(entry: ConfigEntry) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name="Islamic Prayer Times",
        manufacturer="adhanpy",
        model=CALC_METHODS.get(
            entry.data.get(CONF_CALC_METHOD, DEFAULT_CALC_METHOD), "Unknown"
        ),
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up prayer time sensors from a config entry."""
    coordinator: IslamicPrayerTimesCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = []

    for prayer_key in PRAYERS:
        entities.append(PrayerTimeSensor(coordinator, entry, prayer_key))

    entities.append(NextPrayerSensor(coordinator, entry))
    async_add_entities(entities)


class PrayerTimeSensor(
    CoordinatorEntity[IslamicPrayerTimesCoordinator], SensorEntity
):
    """Sensor showing today's time for a specific prayer."""

    _attr_icon = "mdi:mosque"

    def __init__(
        self,
        coordinator: IslamicPrayerTimesCoordinator,
        entry: ConfigEntry,
        prayer_key: str,
    ) -> None:
        super().__init__(coordinator)
        self._prayer_key = prayer_key
        self._entry = entry
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_{prayer_key}"
        self._attr_name = PRAYER_NAMES.get(prayer_key, prayer_key.title())
        self._attr_device_info = _device_info(entry)
        self._attr_has_entity_name = True

    @property
    def native_value(self) -> str | None:
        data: PrayerTimeData | None = self.coordinator.data
        if data is None:
            return None
        dt = data.prayer_times.get(self._prayer_key)
        if dt is None:
            return None
        return dt.strftime("%H:%M")

    @property
    def extra_state_attributes(self) -> dict:
        data = self._entry.data
        offset_key = PRAYER_OFFSET_MAP.get(self._prayer_key)
        return {
            "adjustment_minutes": data.get(offset_key, 0) if offset_key else 0,
            "calculation_method": CALC_METHODS.get(
                data.get(CONF_CALC_METHOD, DEFAULT_CALC_METHOD), "Unknown"
            ),
            "latitude": data.get(CONF_LATITUDE),
            "longitude": data.get(CONF_LONGITUDE),
        }


class NextPrayerSensor(
    CoordinatorEntity[IslamicPrayerTimesCoordinator], SensorEntity
):
    """Sensor showing which prayer is next and the countdown."""

    _attr_icon = "mdi:timer-sand"

    def __init__(
        self,
        coordinator: IslamicPrayerTimesCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_{PRAYER_NEXT}"
        self._attr_name = "Next Prayer"
        self._attr_device_info = _device_info(entry)
        self._attr_has_entity_name = True

    @property
    def native_value(self) -> str | None:
        data: PrayerTimeData | None = self.coordinator.data
        if data is None or data.next_prayer is None:
            return None
        return PRAYER_NAMES.get(data.next_prayer, data.next_prayer)

    @property
    def extra_state_attributes(self) -> dict:
        data: PrayerTimeData | None = self.coordinator.data
        if data is None:
            return {}
        attrs: dict = {}
        if data.next_prayer_time:
            attrs["time"] = data.next_prayer_time.strftime("%H:%M")
            tz = ZoneInfo(self.coordinator.hass.config.time_zone)
            now = datetime.now(tz)
            remaining = data.next_prayer_time - now
            total_seconds = max(int(remaining.total_seconds()), 0)
            hours, remainder = divmod(total_seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            attrs["countdown"] = f"{hours}h {minutes}m"
            attrs["remaining_seconds"] = total_seconds
        attrs["enabled_prayers"] = [
            PRAYER_NAMES.get(p, p) for p in data.enabled_prayers
        ]
        return attrs
