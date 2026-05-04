"""Support for Modern Forms Fan lights."""

from typing import TYPE_CHECKING, Any, ClassVar

import voluptuous as vol
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP_K,
    ColorMode,
    LightEntity,
)
from homeassistant.helpers import entity_platform
from homeassistant.util.percentage import (
    percentage_to_ranged_value,
    ranged_value_to_percentage,
)

from . import modernforms_exception_handler
from .aiomodernforms.const import (
    LIGHT_COLOR_TEMP_MAX_KELVIN,
    LIGHT_COLOR_TEMP_MIN_KELVIN,
    LIGHT_POWER_OFF,
    LIGHT_POWER_ON,
)
from .const import (
    ATTR_SLEEP_TIME,
    CLEAR_TIMER,
    OPT_BRIGHTNESS,
    OPT_COLOR_TEMP,
    OPT_ON,
    SERVICE_CLEAR_LIGHT_SLEEP_TIMER,
    SERVICE_SET_LIGHT_SLEEP_TIMER,
)
from .entity import ModernFormsDeviceEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

    from .coordinator import ModernFormsConfigEntry, ModernFormsDataUpdateCoordinator

BRIGHTNESS_RANGE = (1, 255)


async def async_setup_entry(
    _hass: HomeAssistant,
    config_entry: ModernFormsConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up a Modern Forms platform from config entry."""
    coordinator = config_entry.runtime_data

    # if no light unit installed no light entity
    if not coordinator.data.info.light_type:
        return

    platform = entity_platform.async_get_current_platform()

    platform.async_register_entity_service(
        SERVICE_SET_LIGHT_SLEEP_TIMER,
        {
            vol.Required(ATTR_SLEEP_TIME): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=1440)
            ),
        },
        "async_set_light_sleep_timer",
    )

    platform.async_register_entity_service(
        SERVICE_CLEAR_LIGHT_SLEEP_TIMER,
        None,
        "async_clear_light_sleep_timer",
    )

    async_add_entities(
        [
            ModernFormsLightEntity(
                entry_id=config_entry.entry_id, coordinator=coordinator
            )
        ]
    )


class ModernFormsLightEntity(ModernFormsDeviceEntity, LightEntity):
    """Defines a Modern Forms downlight."""

    _attr_min_color_temp_kelvin = LIGHT_COLOR_TEMP_MIN_KELVIN
    _attr_max_color_temp_kelvin = LIGHT_COLOR_TEMP_MAX_KELVIN
    _attr_translation_key = "downlight"

    def __init__(
        self, entry_id: str, coordinator: ModernFormsDataUpdateCoordinator
    ) -> None:
        """Initialize Modern Forms downlight."""
        super().__init__(
            entry_id=entry_id,
            coordinator=coordinator,
        )
        self._attr_unique_id = f"{self.coordinator.data.info.mac_address}"

    @property
    def color_mode(self) -> ColorMode:
        """Return the current color mode."""
        if self.coordinator.data.state.light_color_temp_kelvin is not None:
            return ColorMode.COLOR_TEMP
        return ColorMode.BRIGHTNESS

    @property
    def supported_color_modes(self) -> set[ColorMode]:
        """Return the supported color modes."""
        if self.coordinator.data.state.light_color_temp_kelvin is not None:
            return {ColorMode.COLOR_TEMP}
        return {ColorMode.BRIGHTNESS}

    @property
    def brightness(self) -> int | None:
        """Return the brightness of this light between 1..255."""
        return round(
            percentage_to_ranged_value(
                BRIGHTNESS_RANGE, self.coordinator.data.state.light_brightness
            )
        )

    @property
    def color_temp_kelvin(self) -> int | None:
        """Return the color temperature in Kelvin."""
        return self.coordinator.data.state.light_color_temp_kelvin

    @property
    def is_on(self) -> bool:
        """Return the state of the light."""
        return bool(self.coordinator.data.state.light_on)

    @modernforms_exception_handler
    async def async_turn_off(self, **_kwargs: Any) -> None:
        """Turn off the light."""
        await self.coordinator.modern_forms.light(on=LIGHT_POWER_OFF)

    @modernforms_exception_handler
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the light."""
        data: dict[str, Any] = {OPT_ON: LIGHT_POWER_ON}

        if ATTR_BRIGHTNESS in kwargs:
            data[OPT_BRIGHTNESS] = ranged_value_to_percentage(
                BRIGHTNESS_RANGE, kwargs[ATTR_BRIGHTNESS]
            )

        if ATTR_COLOR_TEMP_K in kwargs:
            data[OPT_COLOR_TEMP] = kwargs[ATTR_COLOR_TEMP_K]

        await self.coordinator.modern_forms.light(**data)

    @modernforms_exception_handler
    async def async_set_light_sleep_timer(
        self,
        sleep_time: int,
    ) -> None:
        """Set a Modern Forms light sleep timer."""
        await self.coordinator.modern_forms.light(sleep=sleep_time * 60)

    @modernforms_exception_handler
    async def async_clear_light_sleep_timer(
        self,
    ) -> None:
        """Clear a Modern Forms light sleep timer."""
        await self.coordinator.modern_forms.light(sleep=CLEAR_TIMER)
