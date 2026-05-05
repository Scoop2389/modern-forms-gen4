"""Models for Async IO Modern Forms."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .const import (
    DEFAULT_WIND_SPEED,
    INFO_CLIENT_ID,
    INFO_DEVICE_NAME,
    INFO_FAN_MOTOR_TYPE,
    INFO_FAN_TYPE,
    INFO_FEDERATED_IDENTITY,
    INFO_FIRMWARE_URL,
    INFO_FIRMWARE_VERSION,
    INFO_LIGHT_TYPE,
    INFO_MAC,
    INFO_MAIN_MCU_FIRMWARE_VERSION,
    INFO_OWNER,
    INFO_PRODUCT_SKU,
    INFO_PRODUCTION_LOT_NUMBER,
    STATE_ADAPTIVE_LEARNING,
    STATE_AWAY_MODE,
    STATE_FAN_DIRECTION,
    STATE_FAN_POWER,
    STATE_FAN_SLEEP_TIMER,
    STATE_FAN_SPEED,
    STATE_LIGHT_BRIGHTNESS,
    STATE_LIGHT_COLOR_TEMP,
    STATE_LIGHT_POWER,
    STATE_LIGHT_SLEEP_TIMER,
    STATE_UPLIGHT_BRIGHTNESS,
    STATE_UPLIGHT_COLOR_TEMP,
    STATE_UPLIGHT_POWER,
    STATE_WIND_POWER,
    STATE_WIND_SPEED,
)


@dataclass
class Info:
    """Info about the Modern Forms device."""

    client_id: str
    mac_address: str
    light_type: str
    fan_type: str
    fan_motor_type: str
    production_lot_number: str
    product_sku: str
    owner: str
    federated_identity: str
    device_name: str
    firmware_version: str
    main_mcu_firmware_version: str
    firmware_url: str

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Info:
        """Return Info object from Modern Forms API response."""
        return Info(
            client_id=data.get(INFO_CLIENT_ID, ""),
            mac_address=data.get(INFO_MAC, ""),
            light_type=data.get(INFO_LIGHT_TYPE, ""),
            fan_type=data.get(INFO_FAN_TYPE, ""),
            fan_motor_type=data.get(INFO_FAN_MOTOR_TYPE, ""),
            production_lot_number=data.get(INFO_PRODUCTION_LOT_NUMBER, ""),
            product_sku=data.get(INFO_PRODUCT_SKU, ""),
            owner=data.get(INFO_OWNER, ""),
            federated_identity=data.get(INFO_FEDERATED_IDENTITY, ""),
            device_name=data.get(INFO_DEVICE_NAME, ""),
            firmware_version=data.get(INFO_FIRMWARE_VERSION, ""),
            main_mcu_firmware_version=data.get(INFO_MAIN_MCU_FIRMWARE_VERSION, ""),
            firmware_url=data.get(INFO_FIRMWARE_URL, ""),
        )


@dataclass
class State:
    """Object holding the state of Modern Forms Device."""

    fan_on: bool
    fan_speed: int
    fan_direction: str
    fan_sleep_timer: int
    light_on: bool
    light_brightness: int
    light_color_temp_kelvin: int | None
    light_sleep_timer: int
    uplight_on: bool | None
    uplight_brightness: int | None
    uplight_color_temp_kelvin: int | None
    away_mode_enabled: bool
    adaptive_learning_enabled: bool
    wind: bool | None
    wind_speed: int

    @staticmethod
    def from_dict(data: dict[str, Any]) -> State:
        """Return State object from Modern Forms API response."""
        return State(
            fan_on=data.get(STATE_FAN_POWER, False),
            fan_speed=data.get(STATE_FAN_SPEED, 6),
            fan_direction=data.get(STATE_FAN_DIRECTION, "forward"),
            fan_sleep_timer=data.get(STATE_FAN_SLEEP_TIMER, 0),
            light_on=data.get(STATE_LIGHT_POWER, False),
            light_brightness=data.get(STATE_LIGHT_BRIGHTNESS, 100),
            light_color_temp_kelvin=data.get(STATE_LIGHT_COLOR_TEMP),
            light_sleep_timer=data.get(STATE_LIGHT_SLEEP_TIMER, 0),
            uplight_on=data.get(STATE_UPLIGHT_POWER),
            uplight_brightness=data.get(STATE_UPLIGHT_BRIGHTNESS),
            uplight_color_temp_kelvin=data.get(STATE_UPLIGHT_COLOR_TEMP),
            away_mode_enabled=data.get(STATE_AWAY_MODE, False),
            adaptive_learning_enabled=data.get(STATE_ADAPTIVE_LEARNING, False),
            wind=data.get(STATE_WIND_POWER),
            wind_speed=data.get(STATE_WIND_SPEED, DEFAULT_WIND_SPEED),
        )


class Device:
    """Object holding all information of Modern Forms Device."""

    info: Info
    state: State

    def __init__(self, state_data: dict, info_data: dict) -> None:
        """Initialize an empty Modern Forms device class."""
        self.update_from_dict(state_data=state_data, info_data=info_data)

    def update_from_dict(
        self, state_data: dict | None = None, info_data: dict | None = None
    ) -> Device:
        """Update the device status with the passed dict."""
        if state_data is not None:
            self.state = State.from_dict(state_data)
        if info_data is not None:
            self.info = Info.from_dict(info_data)
        return self

    def has_wind(self) -> bool:
        """See if the Fan has Breeze Mode."""
        return self.state.wind is not None

    def has_uplight(self) -> bool:
        """See if the Fan has an Uplight fixture."""
        return self.state.uplight_on is not None
