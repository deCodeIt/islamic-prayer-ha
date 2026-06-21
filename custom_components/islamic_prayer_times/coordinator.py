"""DataUpdateCoordinator for Islamic Prayer Times."""

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
    EVENT_PRAYER_TIME,
    PRAYER_FAJR,
    PRAYER_NAMES,
    PRAYER_ZUHR,
    PRAYER_ASR,
    PRAYER_MAGHRIB,
    PRAYER_ISHA,
    PRAYERS,
    PRAYTIMES_KEY_MAP,
)

_LOGGER = logging.getLogger(__name__)

NEXT_PRAYER_ORDER = [PRAYER_FAJR, PRAYER_ZUHR, PRAYER_ASR, PRAYER_MAGHRIB, PRAYER_ISHA]

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
        self.offsets = offsets
        self.next_prayer_toggles = next_prayer_toggles
        self._cached_date: str | None = None
        self._cached_times: dict[str, datetime] = {}
        self._announced_prayers: set[str] = set()
        self._initialized: bool = False

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

    def _fire_prayer_events(
        self, times: dict[str, datetime], now: datetime
    ) -> None:
        """Fire events for prayers whose time has just arrived."""
        for prayer_key in PRAYERS:
            if prayer_key in self._announced_prayers:
                continue
            prayer_dt = times.get(prayer_key)
            if prayer_dt and prayer_dt <= now:
                self._announced_prayers.add(prayer_key)
                if not self._initialized:
                    continue
                self.hass.bus.async_fire(
                    EVENT_PRAYER_TIME,
                    {
                        "prayer": prayer_key,
                        "name": PRAYER_NAMES.get(prayer_key, prayer_key),
                        "time": prayer_dt.strftime("%H:%M"),
                    },
                )
                _LOGGER.debug("Fired %s event for %s", EVENT_PRAYER_TIME, prayer_key)
        if not self._initialized:
            self._initialized = True
            _LOGGER.debug(
                "Initialized announced prayers (skipped events for already-passed: %s)",
                self._announced_prayers,
            )

    async def _async_update_data(self) -> PrayerTimeData:
        """Recalculate prayer times and determine next prayer."""
        tz = ZoneInfo(self.hass.config.time_zone)
        now = datetime.now(tz)
        today_str = now.strftime("%Y-%m-%d")

        if self._cached_date != today_str:
            self._cached_times = await self.hass.async_add_executor_job(
                self._calculate_times, now, tz
            )
            self._cached_date = today_str
            self._announced_prayers.clear()

        self._fire_prayer_events(self._cached_times, now)

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
            prayer_times=self._cached_times,
            next_prayer=next_prayer,
            next_prayer_time=next_time,
            enabled_prayers=enabled,
        )
