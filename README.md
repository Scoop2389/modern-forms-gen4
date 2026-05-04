# Modern Forms (Gen4) — Home Assistant Custom Integration

This is a custom [Home Assistant](https://www.home-assistant.io/) integration for [Modern Forms](https://www.modernforms.com/) smart fans, with added support for **Generation 4** fans (e.g. the Radiant 56″) that are **not supported by the built-in HA integration**.

## Why this custom integration?

The official Home Assistant `modern_forms` integration (and the underlying `aiomodernforms` library) uses the `/mf` REST endpoint, which only works on older fan firmware.  Generation 4 fans returned a **404 "This URI does not exist"** error on setup, making them completely unusable.

Generation 4 fans expose two new endpoints:

| Endpoint | Purpose |
|---|---|
| `POST /device` | Query/set device-level info and settings (device name, firmware, away mode, …) |
| `POST /fixture` | Query or control individual fixtures (fan motor, downlight, uplight) |

This integration **auto-detects** which API to use:

1. On first connection it probes the `/device` endpoint.
2. If the device responds with `systemType` containing `"fan_g4"`, the G4 API is used.
3. Otherwise the legacy `/mf` API is used, identical to the upstream integration.

There is no configuration required — the same UI setup flow works for both fan generations.

## Features

| Feature | Legacy fans | Gen 4 fans |
|---|---|---|
| Fan on/off | ✅ | ✅ |
| Fan speed (6 speeds) | ✅ | ✅ |
| Fan direction | ✅ | ✅ |
| Breeze / Wind mode | ✅ (if supported) | ✅ |
| Light on/off | ✅ (if installed) | ✅ (auto-detected) |
| Light brightness | ✅ | ✅ |
| Away mode switch | ✅ | ✅ |
| Adaptive learning switch | ✅ | — (not available on G4) |
| Fan/Light sleep timers | ✅ | — (not available on G4) |
| Zeroconf/mDNS discovery | ✅ | ✅ |

## G4 fixture address calculation

G4 fans address each fixture (fan motor, downlight, uplight) using a 32-bit integer derived from the device MAC address:

```
address = (type_byte << 24) | last_3_bytes_of_apMac
```

| Fixture | Type byte |
|---|---|
| Fan motor | `0x0D` |
| Downlight | `0x05` |
| Uplight | downlight + 1 |

The `apMac` field is returned by the `/device` endpoint.

## Installation via HACS

1. Open **HACS** → **Integrations** → ⋮ → **Custom repositories**.
2. Add `https://github.com/Scoop2389/modern-forms-gen4` as type **Integration**.
3. Install **Modern Forms (Gen4)** and restart Home Assistant.
4. Go to **Settings** → **Integrations** → **Add Integration** → search for **Modern Forms**.

> **Note:** Because this integration uses the same `domain` (`modern_forms`) as the built-in integration, you must **disable or remove the built-in Modern Forms integration** before adding this one, otherwise there will be a conflict.

## Manual installation

1. Copy the `custom_components/modern_forms` folder to your HA `config/custom_components/` directory.
2. Restart Home Assistant.
3. Add the integration via the UI as above.

## Differences from the upstream integration

- The bundled `aiomodernforms` library has been extended with a `ModernFormsDeviceG4` class and a `ModernFormsDeviceAuto` wrapper that performs generation detection transparently.
- No external PyPI package is required; the library is shipped inside the integration.
- The `manifest.json` `version` field is set so HACS can track updates.

## Supported fans

Any Modern Forms fan that uses either the legacy `/mf` API or the new G4 `/device`+`/fixture` API should work.  Confirmed working:

- All fans supported by the upstream integration (legacy API).
- Generation 4 fans with `systemType: "fan_g4"` (e.g. Radiant FR-W2006-52 56″).

## Credits

Based on the official [Home Assistant `modern_forms` integration](https://www.home-assistant.io/integrations/modern_forms/) and the [aiomodernforms](https://github.com/wonderslug/aiomodernforms) library by [@wonderslug](https://github.com/wonderslug).

G4 API reverse-engineered from PCAPDroid traffic captures documented in [HA core issue #169247](https://github.com/home-assistant/core/issues/169247).

This code was partially generated with AI.
