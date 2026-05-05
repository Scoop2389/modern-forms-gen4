"""Coordinator for the Modern Forms integration."""

import logging
from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .aiomodernforms import ModernFormsDeviceAuto as ModernFormsDevice
from .aiomodernforms import ModernFormsError
from .aiomodernforms.models import Device as ModernFormsDeviceState
from .const import DOMAIN

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

SCAN_INTERVAL = timedelta(seconds=5)
_LOGGER = logging.getLogger(__name__)


ModernFormsConfigEntry = ConfigEntry["ModernFormsDataUpdateCoordinator"]


class ModernFormsDataUpdateCoordinator(DataUpdateCoordinator[ModernFormsDeviceState]):
    """Class to manage fetching Modern Forms data from single endpoint."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize global Modern Forms data updater."""
        self.modern_forms = ModernFormsDevice(
            config_entry.data[CONF_HOST], session=async_get_clientsession(hass)
        )

        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self) -> ModernFormsDeviceState:
        """Fetch data from Modern Forms."""
        try:
            return await self.modern_forms.update(
                full_update=not self.last_update_success
            )
        except ModernFormsError as error:
            msg = f"Invalid response from API: {error}"
            raise UpdateFailed(msg) from error
