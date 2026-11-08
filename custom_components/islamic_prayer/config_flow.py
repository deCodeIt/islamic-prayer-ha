"""Config flow for Islamic Prayers."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CALC_METHODS,
    CONF_CALC_METHOD,
    CONF_LATITUDE,
    CONF_LOCATION,
    CONF_LONGITUDE,
    DEFAULT_CALC_METHOD,
    DOMAIN,
    OFFSET_CONF_KEYS,
    OFFSET_MAX_MINUTES,
    OFFSET_MIN_MINUTES,
    OFFSET_STEP_MINUTES,
    TOGGLE_CONF_KEYS,
)
from .helpers import (
    get_calc_method,
    get_latitude,
    get_longitude,
    get_offset_config,
    get_toggle_config,
)

CALC_METHOD_OPTIONS = [
    selector.SelectOptionDict(value=k, label=v)
    for k, v in CALC_METHODS.items()
]

LOCATION_SELECTOR = selector.LocationSelector(
    selector.LocationSelectorConfig(radius=False)
)


def _adjustments_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    """Build the offsets/toggles schema, defaulting to the live values."""
    d = defaults or {}
    offset_selector = selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=OFFSET_MIN_MINUTES,
            max=OFFSET_MAX_MINUTES,
            step=OFFSET_STEP_MINUTES,
            mode=selector.NumberSelectorMode.BOX,
        )
    )

    schema: dict[Any, Any] = {}
    for key in OFFSET_CONF_KEYS:
        schema[vol.Optional(key, default=d.get(key, 0))] = offset_selector
    for key in TOGGLE_CONF_KEYS:
        schema[vol.Optional(key, default=d.get(key, True))] = selector.BooleanSelector()
    return vol.Schema(schema)


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
                    ): LOCATION_SELECTOR,
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
                            "latitude": get_latitude(self._config_entry),
                            "longitude": get_longitude(self._config_entry),
                        },
                    ): LOCATION_SELECTOR,
                }
            ),
        )

    async def async_step_method(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Options Step 2: Calculation method."""
        if user_input is not None:
            self._new_data[CONF_CALC_METHOD] = user_input[CONF_CALC_METHOD]
            return await self.async_step_adjustments()

        return self.async_show_form(
            step_id="method",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_CALC_METHOD,
                        default=get_calc_method(self._config_entry),
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
        """Options Step 3: Offsets and toggles applied without a reload."""
        if user_input is not None:
            # Offsets live in the entry options so the number entities stay the
            # single source of truth; toggles stay in the entry data.
            offsets = {
                key: value
                for key, value in user_input.items()
                if key in OFFSET_CONF_KEYS
            }
            toggles = {
                **get_toggle_config(self._config_entry),
                **{
                    key: value
                    for key, value in user_input.items()
                    if key in TOGGLE_CONF_KEYS
                },
            }
            self.hass.config_entries.async_update_entry(
                self._config_entry,
                data={**self._new_data, **toggles},
            )
            # OptionsFlow result data becomes the entry options, so return the
            # merged offsets to keep the number entities in sync.
            return self.async_create_entry(
                title="",
                data={**self._config_entry.options, **offsets},
            )

        return self.async_show_form(
            step_id="adjustments",
            data_schema=_adjustments_schema(
                {
                    **get_offset_config(self._config_entry),
                    **get_toggle_config(self._config_entry),
                }
            ),
        )
