"""Async IO client for Generation 4 Modern Forms fans."""

from __future__ import annotations

import contextlib
import json
import socket
from typing import TYPE_CHECKING, Any, Self

import aiohttp
import async_timeout

from .const import (
    DEFAULT_PORT,
    DEFAULT_TIMEOUT_SECS,
    FAN_DIRECTION_FORWARD,
    FAN_DIRECTION_REVERSE,
    FAN_SPEED_HIGH_VALUE,
    FAN_SPEED_LOW_VALUE,
    LIGHT_BRIGHTNESS_HIGH_VALUE,
    LIGHT_BRIGHTNESS_LOW_VALUE,
    WIND_SPEED_HIGH_VALUE,
    WIND_SPEED_LOW_VALUE,
)
from .exceptions import (
    ModernFormsConnectionError,
    ModernFormsConnectionTimeoutError,
    ModernFormsEmptyResponseError,
    ModernFormsError,
    ModernFormsInvalidSettingsError,
    ModernFormsNotInitializedError,
)
from .models import Device

if TYPE_CHECKING:
    from .models import Info, State

# G4 API endpoints
G4_DEVICE_ENDPOINT = "device"
G4_FIXTURE_ENDPOINT = "fixture"

# G4 fixture type bytes (prepended to last 3 MAC bytes to form fixture address)
G4_FAN_TYPE_BYTE = 0x0D
G4_DOWNLIGHT_TYPE_BYTE = 0x05

# G4 fixture actions
G4_ACTION_QUERY = 3
G4_ACTION_CONTROL = 4

# G4 brightness scale (G4 uses 1-10000, legacy uses 1-100)
G4_BRIGHTNESS_SCALE = 100

# systemType values that identify G4 fans
G4_SYSTEM_TYPES = {"fan_g4"}


def _compute_g4_fixture_addrs(ap_mac: str) -> tuple[int, int, int]:
    """
    Compute G4 fixture addresses from the AP MAC address.

    Address format: (type_byte << 24) | last_3_mac_bytes
    - Fan:       type_byte=0x0D
    - Downlight: type_byte=0x05
    - Uplight:   downlight_addr + 1
    """
    mac_bytes = [int(b, 16) for b in ap_mac.split(":")]
    suffix = (mac_bytes[-3] << 16) | (mac_bytes[-2] << 8) | mac_bytes[-1]
    fan_addr = (G4_FAN_TYPE_BYTE << 24) | suffix
    downlight_addr = (G4_DOWNLIGHT_TYPE_BYTE << 24) | suffix
    uplight_addr = downlight_addr + 1
    return fan_addr, downlight_addr, uplight_addr


class ModernFormsDeviceG4:
    """Generation 4 Modern Forms device using /device and /fixture endpoints."""

    _device: Device | None = None

    def __init__(  # noqa: PLR0913
        self,
        host: str,
        port: int = DEFAULT_PORT,
        request_timeout: float = DEFAULT_TIMEOUT_SECS,
        session: aiohttp.client.ClientSession = None,
        *,
        tls: bool = False,
        verify_ssl: bool = True,
    ) -> None:
        """Initialize connection with G4 Modern Forms fan."""
        self._session = session
        self._close_session = False
        self._host = host
        self._port = port
        self._request_timeout = request_timeout
        self._tls = tls
        self._verify_ssl = verify_ssl

        self._fan_addr: int | None = None
        self._downlight_addr: int | None = None
        self._uplight_addr: int | None = None
        self._has_downlight: bool | None = None

    async def _raw_request(self, endpoint: str, payload: dict) -> Any:
        """Make a POST request to a G4 endpoint."""
        scheme = "https" if self._tls else "http"
        url = f"{scheme}://{self._host}:{self._port}/{endpoint}"

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        if self._session is None:
            self._session = aiohttp.ClientSession()
            self._close_session = True

        try:
            with async_timeout.timeout(self._request_timeout):
                response = await self._session.request(
                    "POST",
                    url,
                    json=payload,
                    headers=headers,
                    ssl=self._verify_ssl,
                )
        except TimeoutError as exception:
            msg = (
                "Timeout occurred while connecting to Modern Forms device at"
                f" {self._host}"
            )
            raise ModernFormsConnectionTimeoutError(msg) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            msg = (
                "Error occurred while communicating with Modern Forms device at"
                f" {self._host}"
            )
            raise ModernFormsConnectionError(msg) from exception

        content_type = response.headers.get("Content-Type", "")
        if (response.status // 100) in [4, 5]:
            contents = await response.read()
            response.close()
            if content_type == "application/json":
                raise ModernFormsError(
                    response.status, json.loads(contents.decode("utf8"))
                )
            raise ModernFormsError(
                response.status, {"message": contents.decode("utf8")}
            )

        data = await response.json()

        if not data:
            msg = f"Modern Forms G4 device at {self._host} returned an empty response"
            raise ModernFormsEmptyResponseError(msg)

        return data

    async def _request_device(self, payload: dict) -> dict:
        """POST to the /device endpoint."""
        return await self._raw_request(G4_DEVICE_ENDPOINT, payload)

    async def _request_fixture(self, payload: dict) -> dict:
        """POST to the /fixture endpoint."""
        return await self._raw_request(G4_FIXTURE_ENDPOINT, payload)

    def _build_state_and_info(
        self,
        device_data: dict,
        fan_fixture: dict,
        light_fixture: dict | None,
    ) -> tuple[dict, dict]:
        """Build state_data and info_data dicts using legacy API key names."""
        fan_state = fan_fixture.get("state", {})

        # Map to legacy Info keys
        info_data: dict[str, Any] = {
            "mac": device_data.get("staMac", device_data.get("apMac", "")),
            "deviceName": device_data.get("deviceName", ""),
            "fanType": device_data.get("deviceModel", ""),
            "firmwareVersion": device_data.get("iotmVer", ""),
            "mainMcuFirmwareVersion": device_data.get("scmVer", ""),
            "owner": device_data.get("owner", ""),
            # Indicate a light is present so the light entity is created
            "lightType": "G4" if self._has_downlight else "",
            # Fields not available in G4
            "clientId": "",
            "fanMotorType": "",
            "productionLotNumber": "",
            "productSku": "",
            "federatedIdentity": "",
            "firmwareUrl": "",
        }

        # fanDirection: G4 boolean (false=forward, true=reverse) → legacy string
        raw_direction = fan_state.get("fanDirection", False)
        fan_direction = (
            FAN_DIRECTION_REVERSE if raw_direction else FAN_DIRECTION_FORWARD
        )

        # wind: only include if present in fixture state
        wind_value = fan_state.get("wind")

        # Map to legacy State keys
        state_data: dict[str, Any] = {
            "fanOn": fan_state.get("status", False),
            "fanSpeed": fan_state.get("fanSpeed", 1),
            "fanDirection": fan_direction,
            "fanSleepTimer": 0,
            "awayModeEnabled": device_data.get("awayModeEnabled", False),
            "adaptiveLearning": False,
            "wind": wind_value,
            "windSpeed": fan_state.get("windSpeed", 1),
        }

        if light_fixture:
            light_state = light_fixture.get("state", {})
            # G4 scale is 1-10000; default to full brightness (10000)
            raw_level = light_state.get("level", 10000)
            # Convert G4's 0-10000 scale to legacy 1-100
            brightness_pct = max(1, min(100, round(raw_level / G4_BRIGHTNESS_SCALE)))
            state_data["lightOn"] = light_state.get("status", False)
            state_data["lightBrightness"] = brightness_pct
            state_data["lightSleepTimer"] = 0
        else:
            state_data["lightOn"] = False
            state_data["lightBrightness"] = 100
            state_data["lightSleepTimer"] = 0

        return state_data, info_data

    async def update(self, *, full_update: bool = False) -> Device:
        """Get all information about the G4 device in a single call."""
        device_data = await self._request_device({"query": True})

        # Validate this is actually a G4 device
        system_type = device_data.get("systemType", "")
        if not any(g4 in system_type.lower() for g4 in G4_SYSTEM_TYPES):
            raise ModernFormsError(
                0,
                {
                    "message": (
                        f"Device at {self._host} is not a G4 fan"
                        f" (systemType={system_type!r})"
                    )
                },
            )

        ap_mac = device_data.get("apMac", "")
        if self._fan_addr is None and ap_mac:
            self._fan_addr, self._downlight_addr, self._uplight_addr = (
                _compute_g4_fixture_addrs(ap_mac)
            )

        if self._fan_addr is None:
            raise ModernFormsError(
                0, {"message": "Unable to determine fixture addresses: missing apMac"}
            )

        fan_fixture = await self._request_fixture(
            {"action": G4_ACTION_QUERY, "addr": self._fan_addr}
        )

        # Probe for light on first update
        light_fixture: dict | None = None
        if self._has_downlight is None:
            try:
                light_fixture = await self._request_fixture(
                    {"action": G4_ACTION_QUERY, "addr": self._downlight_addr}
                )
                self._has_downlight = True
            except ModernFormsError:
                self._has_downlight = False
        elif self._has_downlight:
            light_fixture = await self._request_fixture(
                {"action": G4_ACTION_QUERY, "addr": self._downlight_addr}
            )

        state_data, info_data = self._build_state_and_info(
            device_data, fan_fixture, light_fixture
        )

        if self._device is None or full_update:
            self._device = Device(state_data=state_data, info_data=info_data)
        else:
            self._device.update_from_dict(state_data=state_data)

        return self._device

    async def fan(  # noqa: PLR0912, PLR0913
        self,
        *,
        on: bool | None = None,
        speed: int | None = None,
        direction: str | None = None,
        wind: bool | None = None,
        wind_speed: int | None = None,
        sleep: int | None = None,  # noqa: ARG002  # Not supported on G4; accepted for API compatibility
    ) -> None:
        """Change fan state."""
        if self._device is None:
            await self.update()

        if speed is not None and (
            not isinstance(speed, int)
            or speed < FAN_SPEED_LOW_VALUE
            or speed > FAN_SPEED_HIGH_VALUE
        ):
            msg = (
                f"speed value must be between {FAN_SPEED_LOW_VALUE}"
                f" and {FAN_SPEED_HIGH_VALUE}"
            )
            raise ModernFormsInvalidSettingsError(msg)

        if direction is not None and direction not in [
            FAN_DIRECTION_FORWARD,
            FAN_DIRECTION_REVERSE,
        ]:
            msg = (
                f"fan direction must be {FAN_DIRECTION_FORWARD}"
                f" or {FAN_DIRECTION_REVERSE}"
            )
            raise ModernFormsInvalidSettingsError(msg)

        if wind_speed is not None and (
            not isinstance(wind_speed, int)
            or wind_speed < WIND_SPEED_LOW_VALUE
            or wind_speed > WIND_SPEED_HIGH_VALUE
        ):
            msg = (
                f"wind_speed value must be between {WIND_SPEED_LOW_VALUE}"
                f" and {WIND_SPEED_HIGH_VALUE}"
            )
            raise ModernFormsInvalidSettingsError(msg)

        state: dict[str, Any] = {}
        if on is not None:
            state["status"] = on
        if speed is not None:
            state["fanSpeed"] = speed
        if direction is not None:
            state["fanDirection"] = direction == FAN_DIRECTION_REVERSE
        if wind is not None:
            state["wind"] = wind
        if wind_speed is not None:
            state["windSpeed"] = wind_speed

        if state:
            await self._request_fixture(
                {"action": G4_ACTION_CONTROL, "addr": self._fan_addr, "state": state}
            )

        # Optimistically update local state
        if on is not None:
            self._device.state.fan_on = on  # type: ignore[union-attr]
        if speed is not None:
            self._device.state.fan_speed = speed  # type: ignore[union-attr]
        if direction is not None:
            self._device.state.fan_direction = direction  # type: ignore[union-attr]
        if wind is not None:
            self._device.state.wind = wind  # type: ignore[union-attr]
        if wind_speed is not None:
            self._device.state.wind_speed = wind_speed  # type: ignore[union-attr]

    async def light(
        self,
        *,
        brightness: int | None = None,
        on: bool | None = None,
        sleep: int | None = None,  # noqa: ARG002  # Not supported on G4; accepted for API compatibility
    ) -> None:
        """Change light state."""
        if self._device is None:
            await self.update()

        if not self._has_downlight:
            return

        if brightness is not None and (
            not isinstance(brightness, int)
            or brightness < LIGHT_BRIGHTNESS_LOW_VALUE
            or brightness > LIGHT_BRIGHTNESS_HIGH_VALUE
        ):
            msg = (
                f"brightness value must be between {LIGHT_BRIGHTNESS_LOW_VALUE}"
                f" and {LIGHT_BRIGHTNESS_HIGH_VALUE}"
            )
            raise ModernFormsInvalidSettingsError(msg)

        state: dict[str, Any] = {}
        if on is not None:
            state["status"] = on
        if brightness is not None:
            # Convert 1-100 to G4's 1-10000 scale
            state["level"] = max(1, min(10000, brightness * G4_BRIGHTNESS_SCALE))

        if state:
            await self._request_fixture(
                {
                    "action": G4_ACTION_CONTROL,
                    "addr": self._downlight_addr,
                    "state": state,
                }
            )

        # Optimistically update local state
        if on is not None:
            self._device.state.light_on = on  # type: ignore[union-attr]
        if brightness is not None:
            self._device.state.light_brightness = brightness  # type: ignore[union-attr]

    async def away(self, *, away: bool = False) -> None:
        """Set away mode via /device endpoint."""
        if self._device is None:
            await self.update()
        await self._request_device({"awayModeEnabled": away})
        self._device.state.away_mode_enabled = away  # type: ignore[union-attr]

    async def adaptive_learning(self, *, adaptive_learning: bool = False) -> None:
        """Adaptive learning is not supported on G4 fans (no-op)."""

    async def reboot(self) -> None:
        """Reboot the G4 fan."""
        with contextlib.suppress(ModernFormsConnectionTimeoutError):
            await self._request_device({"reboot": True})

    def has_breeze_mode(self) -> bool:
        """See if the fan has Breeze/Wind mode."""
        if self._device is None:
            msg = (
                "The device has not been initialized. "
                "Please run update on the device before getting state"
            )
            raise ModernFormsNotInitializedError(msg)
        return self._device.has_wind()

    @property
    def status(self) -> State:
        """Return fan state."""
        if self._device is None:
            msg = (
                "The device has not been initialized. "
                "Please run update on the device before getting state"
            )
            raise ModernFormsNotInitializedError(msg)
        return self._device.state

    @property
    def info(self) -> Info:
        """Return fan info."""
        if self._device is None:
            msg = (
                "The device has not been initialized. "
                "Please run update on the device before getting info"
            )
            raise ModernFormsNotInitializedError(msg)
        return self._device.info

    async def close(self) -> None:
        """Close open client session."""
        if self._session and self._close_session:
            await self._session.close()

    async def __aenter__(self) -> Self:
        """Async enter."""
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        """Async exit."""
        await self.close()
