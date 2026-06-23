"""Config flow for Islamic Prayers."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CALC_METHODS,
    CONF_ASR_OFFSET,
    CONF_CALC_METHOD,
    CONF_FAJR_OFFSET,
    CONF_ISHA_OFFSET,
    CONF_LATITUDE,
    CONF_LOCATION,
    CONF_LONGITUDE,
    CONF_MAGHRIB_OFFSET,
    CONF_NEXT_PRAYER_ASR,
    CONF_NEXT_PRAYER_FAJR,
    CONF_NEXT_PRAYER_ISHA,
    CONF_NEXT_PRAYER_MAGHRIB,
    CONF_NEXT_PRAYER_ZUHR,
    CONF_TARKE_SEHER_OFFSET,
    CONF_ZUHR_OFFSET,
    DEFAULT_CALC_METHOD,
    DOMAIN,
)

CALC_METHOD_OPTIONS = [
    selector.SelectOptionDict(value=k, label=v)
    for k, v in CALC_METHODS.items()
]


def _adjustments_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    d = defaults or {}
    return vol.Schema(
        {
            vol.Optional(
                CONF_TARKE_SEHER_OFFSET, default=d.get(CONF_TARKE_SEHER_OFFSET, 0)
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=-60, max=60, step=1, mode=selector.NumberSelectorMode.BOX
                )
            ),
            vol.Optional(
                CONF_FAJR_OFFSET, default=d.get(CONF_FAJR_OFFSET, 0)
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=-60, max=60, step=1, mode=selector.NumberSelectorMode.BOX
                )
            ),
            vol.Optional(
                CONF_ZUHR_OFFSET, default=d.get(CONF_ZUHR_OFFSET, 0)
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=-60, max=60, step=1, mode=selector.NumberSelectorMode.BOX
                )
            ),
            vol.Optional(
                CONF_ASR_OFFSET, default=d.get(CONF_ASR_OFFSET, 0)
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=-60, max=60, step=1, mode=selector.NumberSelectorMode.BOX
                )
            ),
            vol.Optional(
                CONF_MAGHRIB_OFFSET, default=d.get(CONF_MAGHRIB_OFFSET, 0)
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=-60, max=60, step=1, mode=selector.NumberSelectorMode.BOX
                )
            ),
            vol.Optional(
                CONF_ISHA_OFFSET, default=d.get(CONF_ISHA_OFFSET, 0)
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=-60, max=60, step=1, mode=selector.NumberSelectorMode.BOX
                )
            ),
            vol.Optional(
                CONF_NEXT_PRAYER_FAJR,
                default=d.get(CONF_NEXT_PRAYER_FAJR, True),
            ): selector.BooleanSelector(),
            vol.Optional(
                CONF_NEXT_PRAYER_ZUHR,
                default=d.get(CONF_NEXT_PRAYER_ZUHR, True),
            ): selector.BooleanSelector(),
            vol.Optional(
                CONF_NEXT_PRAYER_ASR,
                default=d.get(CONF_NEXT_PRAYER_ASR, True),
            ): selector.BooleanSelector(),
            vol.Optional(
                CONF_NEXT_PRAYER_MAGHRIB,
                default=d.get(CONF_NEXT_PRAYER_MAGHRIB, True),
            ): selector.BooleanSelector(),
            vol.Optional(
                CONF_NEXT_PRAYER_ISHA,
                default=d.get(CONF_NEXT_PRAYER_ISHA, True),
            ): selector.BooleanSelector(),
        }
    )


class IslamicPrayerTimesConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Islamic Prayers."""

    VERSION = 1

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Step 1: Location via map picker."""
        if user_input is not None:
            loc = user_input[CONF_LOCATION]
            self._data[CONF_LATITUDE] = loc["latitude"]
            self._data[CONF_LONGITUDE] = loc["longitude"]
            return await self.async_step_method()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_LOCATION,
                        default={
                            "latitude": self.hass.config.latitude,
                            "longitude": self.hass.config.longitude,
                        },
                    ): selector.LocationSelector(
                        selector.LocationSelectorConfig(radius=False)
                    ),
                }
            ),
        )

    async def async_step_method(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Step 2: Calculation method."""
        if user_input is not None:
            self._data[CONF_CALC_METHOD] = user_input[CONF_CALC_METHOD]
            return await self.async_step_adjustments()

        return self.async_show_form(
            step_id="method",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_CALC_METHOD, default=DEFAULT_CALC_METHOD
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=CALC_METHOD_OPTIONS,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            ),
        )

    async def async_step_adjustments(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Step 3: Per-prayer offsets and Next Prayer toggles."""
        if user_input is not None:
            data = {**self._data, **user_input}
            return self.async_create_entry(
                title="Islamic Prayers",
                data=data,
            )

        return self.async_show_form(
            step_id="adjustments",
            data_schema=_adjustments_schema(),
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> IslamicPrayerTimesOptionsFlow:
        return IslamicPrayerTimesOptionsFlow(config_entry)


class IslamicPrayerTimesOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Islamic Prayers."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry
        self._new_data: dict[str, Any] = {}

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Options Step 1: Location."""
        current = self._config_entry.data
        if user_input is not None:
            loc = user_input[CONF_LOCATION]
            self._new_data[CONF_LATITUDE] = loc["latitude"]
            self._new_data[CONF_LONGITUDE] = loc["longitude"]
            return await self.async_step_method()

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_LOCATION,
                        default={
                            "latitude": current.get(
                                CONF_LATITUDE, self.hass.config.latitude
                            ),
                            "longitude": current.get(
                                CONF_LONGITUDE, self.hass.config.longitude
                            ),
                        },
                    ): selector.LocationSelector(
                        selector.LocationSelectorConfig(radius=False)
                    ),
                }
            ),
        )

    async def async_step_method(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Options Step 2: Calculation method."""
        current = self._config_entry.data
        if user_input is not None:
            self._new_data[CONF_CALC_METHOD] = user_input[CONF_CALC_METHOD]
            return await self.async_step_adjustments()

        return self.async_show_form(
            step_id="method",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_CALC_METHOD,
                        default=current.get(CONF_CALC_METHOD, DEFAULT_CALC_METHOD),
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=CALC_METHOD_OPTIONS,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            ),
        )

    async def async_step_adjustments(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Options Step 3: Offsets and toggles."""
        if user_input is not None:
            new_data = {**self._new_data, **user_input}
            self.hass.config_entries.async_update_entry(
                self._config_entry, data=new_data
            )
            return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="adjustments",
            data_schema=_adjustments_schema(dict(self._config_entry.data)),
        )
