"""DataUpdateCoordinator for Islamic Prayers."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from praytimes import PrayTimes

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CUSTOM_PRAYTIMES_METHODS,
    DEFAULT_CALC_METHOD,
    DOMAIN,
    PRAYER_ASR,
    PRAYER_FAJR,
    PRAYER_ISHA,
    PRAYER_MAGHRIB,
    PRAYER_ZUHR,
    PRAYERS,
    PRAYTIMES_KEY_MAP,
)

_LOGGER = logging.getLogger(__name__)

NEXT_PRAYER_ORDER = [PRAYER_FAJR, PRAYER_ZUHR, PRAYER_ASR, PRAYER_MAGHRIB, PRAYER_ISHA]

# An arrival is only announced if it was detected close to its actual time.
# Anything older (HA asleep, clock jump, offset moved a time into the past) is
# treated as already passed and never raises an event.
ARRIVAL_GRACE = timedelta(minutes=5)

# Register custom methods on the PrayTimes class once
for _key, _config in CUSTOM_PRAYTIMES_METHODS.items():
    if _key not in PrayTimes.methods:
        PrayTimes.methods[_key] = _config


@dataclass
class PrayerTimeData:
    """Container for calculated prayer times and next prayer info."""

    prayer_times: dict[str, datetime] = field(default_factory=dict)
    next_prayer: str | None = None
    next_prayer_time: datetime | None = None
    enabled_prayers: list[str] = field(default_factory=list)


class IslamicPrayerTimesCoordinator(DataUpdateCoordinator[PrayerTimeData]):
    """Coordinator to calculate prayer times and track next prayer."""

    def __init__(
        self,
        hass: HomeAssistant,
        latitude: float,
        longitude: float,
        calc_method: str,
        offsets: dict[str, int],
        next_prayer_toggles: dict[str, bool],
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=30),
        )
        self.latitude = latitude
        self.longitude = longitude
        self.calc_method = calc_method
        self.offsets = dict(offsets)
        self.next_prayer_toggles = dict(next_prayer_toggles)
        self._cached_date: str | None = None
        self._cached_times: dict[str, datetime] = {}
        self._announced_prayers: set[str] = set()
        # Prayers whose time just arrived; drained by the event entity
        self.arrived_prayers: list[str] = []

    @property
    def settings_signature(self) -> tuple:
        """Settings that only take effect after a reload."""
        return (
            self.latitude,
            self.longitude,
            self.calc_method,
        )

    def apply_settings(
        self,
        offsets: dict[str, int],
        next_prayer_toggles: dict[str, bool],
    ) -> bool:
        """Apply live-editable settings. Returns True if anything changed."""
        changed = False
        for prayer_key, minutes in offsets.items():
            if self.offsets.get(prayer_key) != minutes:
                self.offsets[prayer_key] = minutes
                changed = True
        for prayer_key, enabled in next_prayer_toggles.items():
            if self.next_prayer_toggles.get(prayer_key) != enabled:
                self.next_prayer_toggles[prayer_key] = enabled
                changed = True
        return changed

    async def async_set_offset(self, prayer_key: str, minutes: int) -> None:
        """Update a single prayer offset and recalculate immediately."""
        if self.offsets.get(prayer_key) == minutes:
            return
        self.offsets[prayer_key] = minutes
        await self.async_recalculate()

    async def async_recalculate(self) -> None:
        """Recalculate today's times and push the result to all listeners."""
        tz = ZoneInfo(self.hass.config.time_zone)
        now = datetime.now(tz)
        await self._async_refresh_times(now, tz)
        self.async_set_updated_data(await self._async_build_data(now, tz))

    def _calculate_times(
        self, for_date: datetime, tz: ZoneInfo
    ) -> dict[str, datetime]:
        """Calculate prayer times using praytimes library."""
        method = self.calc_method if self.calc_method in PrayTimes.methods else DEFAULT_CALC_METHOD
        pt = PrayTimes()
        pt.adjust(PrayTimes.methods[method]["params"])
        utc_offset = for_date.utcoffset()
        tz_hours = utc_offset.total_seconds() / 3600 if utc_offset else 0

        raw = pt.getTimes(
            [for_date.year, for_date.month, for_date.day],
            [self.latitude, self.longitude],
            tz_hours,
        )

        times: dict[str, datetime] = {}
        for prayer_key in PRAYERS:
            pt_key = PRAYTIMES_KEY_MAP[prayer_key]
            time_str = raw.get(pt_key, "")
            if not time_str or time_str == "-----":
                continue
            hour, minute = map(int, time_str.split(":"))
            prayer_dt = for_date.replace(
                hour=hour, minute=minute, second=0, microsecond=0
            )
            offset_minutes = self.offsets.get(prayer_key, 0)
            times[prayer_key] = prayer_dt + timedelta(minutes=offset_minutes)
        return times

    async def _async_refresh_times(self, now: datetime, tz: ZoneInfo) -> None:
        """Recalculate and cache today's times.

        Times already behind ``now`` (for example because an offset just moved
        them into the past) are marked as announced, so they never raise an
        arrival event.
        """
        self._cached_times = await self.hass.async_add_executor_job(
            self._calculate_times, now, tz
        )
        self._cached_date = now.strftime("%Y-%m-%d")
        self._mark_past_as_announced(self._cached_times, now)

    def _mark_past_as_announced(
        self, times: dict[str, datetime], now: datetime
    ) -> None:
        """Silently mark prayers that already happened today."""
        for prayer_key in NEXT_PRAYER_ORDER:
            prayer_dt = times.get(prayer_key)
            if prayer_dt is not None and prayer_dt <= now:
                self._announced_prayers.add(prayer_key)

    def _collect_arrivals(
        self, times: dict[str, datetime], now: datetime
    ) -> None:
        """Queue prayers whose time has just arrived."""
        for prayer_key in NEXT_PRAYER_ORDER:
            prayer_dt = times.get(prayer_key)
            if prayer_dt is None or prayer_dt > now:
                continue
            if prayer_key in self._announced_prayers:
                continue
            self._announced_prayers.add(prayer_key)
            if now - prayer_dt > ARRIVAL_GRACE:
                _LOGGER.debug(
                    "Skipping event for %s, its time %s is too far in the past",
                    prayer_key,
                    prayer_dt,
                )
                continue
            if self.next_prayer_toggles.get(prayer_key, True):
                self.arrived_prayers.append(prayer_key)

    def _determine_next_prayer(
        self, times: dict[str, datetime], now: datetime
    ) -> tuple[str | None, datetime | None, list[str]]:
        """Find the next upcoming prayer (Tark-e-Seher excluded)."""
        enabled = [
            p for p in NEXT_PRAYER_ORDER
            if self.next_prayer_toggles.get(p, True)
        ]
        for prayer_key in NEXT_PRAYER_ORDER:
            if prayer_key in enabled and times.get(prayer_key):
                if times[prayer_key] > now:
                    return prayer_key, times[prayer_key], enabled
        return None, None, enabled

    async def _async_build_data(
        self, now: datetime, tz: ZoneInfo
    ) -> PrayerTimeData:
        """Build the coordinator payload for the current moment."""
        next_prayer, next_time, enabled = self._determine_next_prayer(
            self._cached_times, now
        )

        if next_prayer is None and enabled:
            tomorrow = now + timedelta(days=1)
            tomorrow_times = await self.hass.async_add_executor_job(
                self._calculate_times, tomorrow, tz
            )
            for prayer_key in NEXT_PRAYER_ORDER:
                if prayer_key in enabled and tomorrow_times.get(prayer_key):
                    next_prayer = prayer_key
                    next_time = tomorrow_times[prayer_key]
                    break

        return PrayerTimeData(
            prayer_times=dict(self._cached_times),
            next_prayer=next_prayer,
            next_prayer_time=next_time,
            enabled_prayers=enabled,
        )

    async def _async_update_data(self) -> PrayerTimeData:
        """Recalculate prayer times and determine next prayer."""
        tz = ZoneInfo(self.hass.config.time_zone)
        now = datetime.now(tz)
        today_str = now.strftime("%Y-%m-%d")

        if self._cached_date != today_str:
            self._announced_prayers.clear()
            await self._async_refresh_times(now, tz)

        self._collect_arrivals(self._cached_times, now)

        return await self._async_build_data(now, tz)
