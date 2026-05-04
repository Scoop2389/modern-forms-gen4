"""Auto-detecting Modern Forms device client.

Tries the Generation 4 API (/device + /fixture) first;
falls back to the legacy API (/mf) if the device is not a G4 fan.
"""
from __future__ import annotations

from typing import Optional, Union

import aiohttp

from .const import DEFAULT_PORT, DEFAULT_TIMEOUT_SECS
from .exceptions import ModernFormsConnectionError, ModernFormsError
from .modernforms import ModernFormsDevice
from .modernforms_g4 import ModernFormsDeviceG4
from .models import Device


class ModernFormsDeviceAuto:
    """Auto-detecting Modern Forms device.

    On the first ``update()`` call this class tries the G4 API first.
    If the device is not a G4 fan (or the endpoint doesn't exist) it
    transparently falls back to the legacy ``/mf`` API.  All subsequent
    calls are forwarded directly to the detected client.
    """

    def __init__(
        self,
        host: str,
        port: int = DEFAULT_PORT,
        request_timeout: float = DEFAULT_TIMEOUT_SECS,
        session: Optional[aiohttp.client.ClientSession] = None,
        tls: bool = False,
        verify_ssl: bool = True,
    ) -> None:
        """Initialise the auto-detecting client."""
        self._host = host
        self._port = port
        self._request_timeout = request_timeout
        self._session = session
        self._tls = tls
        self._verify_ssl = verify_ssl
        self._client: Optional[Union[ModernFormsDeviceG4, ModernFormsDevice]] = None

    # ------------------------------------------------------------------
    # Detection

    async def _detect_and_update(self, full_update: bool = False) -> Device:
        """Try G4 first; fall back to legacy on API errors."""
        g4 = ModernFormsDeviceG4(
            self._host,
            port=self._port,
            request_timeout=self._request_timeout,
            session=self._session,
            tls=self._tls,
            verify_ssl=self._verify_ssl,
        )
        try:
            result = await g4.update(full_update=full_update)
            self._client = g4
            return result
        except ModernFormsConnectionError:
            # Real connectivity problem – surface it immediately, don't try legacy.
            raise
        except ModernFormsError:
            # API-level error (e.g. endpoint not found) – device uses legacy API.
            pass

        legacy = ModernFormsDevice(
            self._host,
            port=self._port,
            request_timeout=self._request_timeout,
            session=self._session,
            tls=self._tls,
            verify_ssl=self._verify_ssl,
        )
        result = await legacy.update(full_update=full_update)
        self._client = legacy
        return result

    # ------------------------------------------------------------------
    # Public interface (mirrors ModernFormsDevice / ModernFormsDeviceG4)

    async def update(self, full_update: bool = False) -> Device:
        """Update and return the device state."""
        if self._client is None:
            return await self._detect_and_update(full_update=full_update)
        return await self._client.update(full_update=full_update)

    async def fan(self, **kwargs) -> None:
        """Change fan state."""
        await self._client.fan(**kwargs)  # type: ignore[union-attr]

    async def light(self, **kwargs) -> None:
        """Change light state."""
        await self._client.light(**kwargs)  # type: ignore[union-attr]

    async def away(self, away: bool = False) -> None:
        """Set away mode."""
        await self._client.away(away=away)  # type: ignore[union-attr]

    async def adaptive_learning(self, adaptive_learning: bool = False) -> None:
        """Set adaptive learning."""
        await self._client.adaptive_learning(  # type: ignore[union-attr]
            adaptive_learning=adaptive_learning
        )

    async def reboot(self) -> None:
        """Reboot the fan."""
        await self._client.reboot()  # type: ignore[union-attr]

    def has_breeze_mode(self) -> bool:
        """Return whether the fan supports Breeze/Wind mode."""
        return self._client.has_breeze_mode()  # type: ignore[union-attr]

    @property
    def status(self):
        """Return current fan state."""
        return self._client.status  # type: ignore[union-attr]

    @property
    def info(self):
        """Return fan info."""
        return self._client.info  # type: ignore[union-attr]

    async def close(self) -> None:
        """Close open client session."""
        if self._client is not None:
            await self._client.close()

    async def __aenter__(self) -> "ModernFormsDeviceAuto":
        """Async enter."""
        return self

    async def __aexit__(self, *exc_info) -> None:
        """Async exit."""
        await self.close()
