"""The Modern Forms integration."""

import logging
from typing import TYPE_CHECKING, Any, Concatenate

from homeassistant.const import Platform

from .aiomodernforms import ModernFormsConnectionError, ModernFormsError
from .coordinator import ModernFormsConfigEntry, ModernFormsDataUpdateCoordinator
from .entity import ModernFormsDeviceEntity

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine

    from homeassistant.core import HomeAssistant

PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.FAN,
    Platform.LIGHT,
    Platform.SENSOR,
    Platform.SWITCH,
]
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ModernFormsConfigEntry) -> bool:
    """Set up a Modern Forms device from a config entry."""
    # Create Modern Forms instance for this entry
    coordinator = ModernFormsDataUpdateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    # Set up all platforms for this device/entry.
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: ModernFormsConfigEntry
) -> bool:
    """Unload Modern Forms config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


def modernforms_exception_handler[
    ModernFormsDeviceEntityT: ModernFormsDeviceEntity,
    **P,
](
    func: Callable[Concatenate[ModernFormsDeviceEntityT, P], Any],
) -> Callable[Concatenate[ModernFormsDeviceEntityT, P], Coroutine[Any, Any, None]]:
    """
    Decorate Modern Forms calls to handle Modern Forms exceptions.

    A decorator that wraps the passed in function, catches Modern Forms errors,
    and handles the availability of the device in the data coordinator.
    """

    async def handler(
        self: ModernFormsDeviceEntityT, *args: P.args, **kwargs: P.kwargs
    ) -> None:
        try:
            await func(self, *args, **kwargs)
            self.coordinator.async_update_listeners()

        except ModernFormsConnectionError:
            _LOGGER.exception("Error communicating with API")
            self.coordinator.last_update_success = False
            self.coordinator.async_update_listeners()

        except ModernFormsError:
            _LOGGER.exception("Invalid response from API")

    return handler
