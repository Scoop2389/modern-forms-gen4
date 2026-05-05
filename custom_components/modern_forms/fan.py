"""Support for Modern Forms Fan Fans."""

from typing import TYPE_CHECKING, Any

import voluptuous as vol
from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.helpers import entity_platform

from . import modernforms_exception_handler
from .aiomodernforms.const import FAN_POWER_OFF, FAN_POWER_ON
from .const import (
    ATTR_SLEEP_TIME,
    CLEAR_TIMER,
    OPT_ON,
    OPT_SPEED,
    SERVICE_CLEAR_FAN_SLEEP_TIMER,
    SERVICE_SET_FAN_SLEEP_TIMER,
)
from .entity import ModernFormsDeviceEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

    from .coordinator import ModernFormsConfigEntry, ModernFormsDataUpdateCoordinator


async def async_setup_entry(
    _hass: HomeAssistant,
    config_entry: ModernFormsConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up a Modern Forms platform from config entry."""
    coordinator = config_entry.runtime_data

    platform = entity_platform.async_get_current_platform()

    platform.async_register_entity_service(
        SERVICE_SET_FAN_SLEEP_TIMER,
        {
            vol.Required(ATTR_SLEEP_TIME): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=1440)
            ),
        },
        "async_set_fan_sleep_timer",
    )

    platform.async_register_entity_service(
        SERVICE_CLEAR_FAN_SLEEP_TIMER,
        None,
        "async_clear_fan_sleep_timer",
    )

    async_add_entities(
        [ModernFormsFanEntity(entry_id=config_entry.entry_id, coordinator=coordinator)]
    )


class ModernFormsFanEntity(FanEntity, ModernFormsDeviceEntity):
    """Defines a Modern Forms fan."""

    _attr_supported_features = (
        FanEntityFeature.DIRECTION
        | FanEntityFeature.SET_SPEED
        | FanEntityFeature.TURN_OFF
        | FanEntityFeature.TURN_ON
    )
    _attr_translation_key = "fan"

    def __init__(
        self, entry_id: str, coordinator: ModernFormsDataUpdateCoordinator
    ) -> None:
        """Initialize Modern Forms fan."""
        super().__init__(
            entry_id=entry_id,
            coordinator=coordinator,
        )
        self._attr_unique_id = f"{self.coordinator.data.info.mac_address}"

    @property
    def percentage(self) -> int | None:
        """Return the current speed percentage."""
        state = self.coordinator.data.state
        if not bool(state.fan_on):
            return 0
        if state.wind:
            return max(0, min(100, round(state.wind_speed / 3 * 100)))
        return max(0, min(100, round(state.fan_speed / 6 * 100)))

    @property
    def speed_count(self) -> int:
        """Return the number of speeds the fan supports."""
        if self.coordinator.data.state.wind:
            return 3
        return 6

    @property
    def current_direction(self) -> str:
        """Return the current direction of the fan."""
        return self.coordinator.data.state.fan_direction

    @property
    def is_on(self) -> bool:
        """Return the state of the fan."""
        return bool(self.coordinator.data.state.fan_on)

    @modernforms_exception_handler
    async def async_set_direction(self, direction: str) -> None:
        """Set the direction of the fan."""
        await self.coordinator.modern_forms.fan(direction=direction)

    @modernforms_exception_handler
    async def async_set_percentage(self, percentage: int) -> None:
        """Set the speed percentage of the fan."""
        if percentage > 0:
            if self.coordinator.data.state.wind:
                speed = max(1, min(3, round(percentage / 100 * 3)))
                await self.coordinator.modern_forms.fan(
                    **{OPT_ON: FAN_POWER_ON, "wind_speed": speed}
                )
            else:
                speed = max(1, min(6, round(percentage / 100 * 6)))
                await self.coordinator.modern_forms.fan(
                    **{OPT_ON: FAN_POWER_ON, OPT_SPEED: speed}
                )
        else:
            await self.async_turn_off()

    @modernforms_exception_handler
    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **_kwargs: Any,
    ) -> None:
        """Turn on the fan."""
        if preset_mode is not None:
            await self.async_set_preset_mode(preset_mode)
            return
        if percentage is not None:
            await self.async_set_percentage(percentage)
            return
        await self.coordinator.modern_forms.fan(**{OPT_ON: FAN_POWER_ON})

    @modernforms_exception_handler
    async def async_turn_off(self, **_kwargs: Any) -> None:
        """Turn the fan off."""
        await self.coordinator.modern_forms.fan(on=FAN_POWER_OFF)

    @modernforms_exception_handler
    async def async_set_fan_sleep_timer(
        self,
        sleep_time: int,
    ) -> None:
        """Set a Modern Forms fan sleep timer."""
        await self.coordinator.modern_forms.fan(sleep=sleep_time * 60)

    @modernforms_exception_handler
    async def async_clear_fan_sleep_timer(
        self,
    ) -> None:
        """Clear a Modern Forms fan sleep timer."""
        await self.coordinator.modern_forms.fan(sleep=CLEAR_TIMER)
