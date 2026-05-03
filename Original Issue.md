This is the original issue from https://github.com/home-assistant/core/issues/169247 this custom integration was made to solve titled "[Integration: Modern Forms] Radiant (Generation 4) Fan does not connect"

### The problem

The Radiant 56" fan does not work with this integration. When setting up the integration with the UI, it says "Unknown error occurred" during setup.

### What version of Home Assistant Core has the issue?

core-2026.4.4

### What type of installation are you running?

Home Assistant OS

### Integration causing the issue

Modern Forms

### Link to integration documentation on our website

https://www.home-assistant.io/integrations/modern_forms/

### Anything in the logs that might be useful for us?

```txt
Logger: aiohttp.server
Source: /usr/local/lib/python3.14/site-packages/aiohttp/web_protocol.py:488
First occurred: 10:53:27 PM (1 occurrence)
Last logged: 10:53:27 PM

Error handling request from 192.168.88.189
Traceback (most recent call last):
  File "/usr/local/lib/python3.14/site-packages/aiohttp/web_protocol.py", line 517, in _handle_request
    resp = await request_handler(request)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.14/site-packages/aiohttp/web_app.py", line 569, in _handle
    return await handler(request)
           ^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.14/site-packages/aiohttp/web_middlewares.py", line 117, in impl
    return await handler(request)
           ^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/components/http/security_filter.py", line 92, in security_filter_middleware
    return await handler(request)
           ^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/components/http/forwarded.py", line 87, in forwarded_middleware
    return await handler(request)
           ^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/components/http/request_context.py", line 26, in request_context_middleware
    return await handler(request)
           ^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/components/http/ban.py", line 90, in ban_middleware
    return await handler(request)
           ^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/components/http/auth.py", line 263, in auth_middleware
    return await handler(request)
           ^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/components/http/headers.py", line 41, in headers_middleware
    response = await handler(request)
               ^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/helpers/http.py", line 89, in handle
    result = await handler(request, **request.match_info)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/components/http/decorators.py", line 83, in with_admin
    return await func(self, request, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/components/config/config_entries.py", line 234, in post
    return await super().post(request, flow_id)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/components/http/data_validator.py", line 74, in wrapper
    return await method(view, request, data, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/helpers/data_entry_flow.py", line 121, in post
    result = await self._flow_mgr.async_configure(flow_id, data)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/data_entry_flow.py", line 336, in async_configure
    result = await self._async_configure(flow_id, user_input)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/config_entries.py", line 1536, in _async_configure
    return await super()._async_configure(flow_id, user_input)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/data_entry_flow.py", line 383, in _async_configure
    result = await self._async_handle_step(
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        flow, cur_step["step_id"], user_input
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/usr/src/homeassistant/homeassistant/data_entry_flow.py", line 483, in _async_handle_step
    result: _FlowResultT = await getattr(flow, method)(user_input)
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/components/modern_forms/config_flow.py", line 39, in async_step_user
    return await self._handle_config_flow()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/components/modern_forms/config_flow.py", line 74, in _handle_config_flow
    device = await device.update()
             ^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.14/site-packages/backoff/_async.py", line 151, in retry
    ret = await target(*args, **kwargs)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.14/site-packages/aiomodernforms/modernforms.py", line 96, in update
    info_data = await self._request({COMMAND_QUERY_STATIC_DATA: True})
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.14/site-packages/backoff/_async.py", line 151, in retry
    ret = await target(*args, **kwargs)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.14/site-packages/aiomodernforms/modernforms.py", line 168, in _request
    raise ModernFormsError(
        response.status, {"message": contents.decode("utf8")}
    )
aiomodernforms.exceptions.ModernFormsError: (404, {'message': 'This URI does not exist'})
```

### Additional information

### My hypothesis
The new G4 fans (including mine) do not seem to use the `/mf` endpoint anymore. Instead using a `/device` and `/fixture` endpoint based on the PCAPDroid data from my phone
### `/device`
Used to query device info and state of all components of the fan. Here's an example query used with my fan to demonstrate what this endpoint does.
```bash
curl -s -X POST http://<FAN_IP>/device \
  -H "Content-Type: application/json" \
  -d '{"query":true}'
```
```json
{
  "owner": "<REDACTED>",
  "deviceName": "<REDACTED>",
  "apMac": "<REDACTED>",
  "bleMac": "<REDACTED>",
  "discoverStatus": 1,
  "factoryResetReason": "xxxxxxxxxxxxxxx",
  "dateCode": "",
  "iotmVer": "01.00.0082",
  "restVer": "1.40",
  "scmVer": "01.47",
  "plcInfo": {},
  "panelVer": "00.00",
  "systemMode": 1,
  "systemModeChangeable": false,
  "bootCount": 3,
  "uptimeSeconds": 3640,
  "locationId": "<REDACTED>",
  "esp-idf-version": "4.4.8",
  "TotalSendTimesm": 9,
  "SendFailTimes": 0,
  "TotalReceiveTimes": 9,
  "systemType": "fan_g4",
  "deviceModel": "FR-W2006-52",
  "builtFor": "strutHw",
  "time": "Sun Apr 26 23:14:26 2026",
  "timeZone": "EST5EDT",
  "tzoffset": "-04:00",
  "latitude": "<REDACTED>",
  "longitude": "<REDACTED>",
  "cdebug": false,
  "accessoryType": 0,
  "RGBPreset": [
    { "index": 1, "type": 2, "red": 255, "green": 0, "blue": 0 },
    { "index": 2, "type": 2, "red": 0, "green": 255, "blue": 0 },
    { "index": 3, "type": 2, "red": 0, "green": 0, "blue": 255 },
    { "index": 4, "type": 2, "red": 255, "green": 255, "blue": 0 },
    { "index": 5, "type": 2, "red": 0, "green": 255, "blue": 255 },
    { "index": 6, "type": 2, "red": 255, "green": 0, "blue": 255 },
    { "index": 7, "type": 2, "red": 128, "green": 0, "blue": 0 },
    { "index": 8, "type": 2, "red": 128, "green": 128, "blue": 0 },
    { "index": 9, "type": 2, "red": 0, "green": 128, "blue": 0 },
    { "index": 10, "type": 2, "red": 128, "green": 0, "blue": 128 },
    { "index": 11, "type": 2, "red": 0, "green": 128, "blue": 128 },
    { "index": 12, "type": 2, "red": 0, "green": 0, "blue": 128 },
    { "index": 13, "type": 1, "level": 10000, "mixColorTemp": 1800 },
    { "index": 14, "type": 1, "level": 10000, "mixColorTemp": 3000 },
    { "index": 15, "type": 1, "level": 10000, "mixColorTemp": 4500 },
    { "index": 16, "type": 1, "level": 10000, "mixColorTemp": 6500 }
  ],
  "features": [
    "localGrps",
    "localAutm",
    "wsMcast",
    "cloudLocationTopics",
    "scheduleOverrides"
  ],
  "networkState": 0,
  "awayModeEnabled": false,
  "multicastState": 0,
  "multicastRx": 0,
  "lastMcastPayload": "",
  "nwkState": {
    "provisioned": true,
    "commissioned": false,
    "ssid": "<REDACTED>",
    "ipAddr": "<REDACTED>",
    "netmask": "255.255.255.0",
    "connectMethod": "wifi",
    "ethIpAddr": "0.0.0.0",
    "staIpAddr": "<REDACTED>",
    "bssid": "<REDACTED>",
    "rssi": "-49",
    "auth": "WPA2_PSK",
    "channel": 1,
    "awsState": "up",
    "awsCloudConnection": "up",
    "awsConnected": 1,
    "certificateID": "<REDACTED>",
    "currFreeHeap": 3987871,
    "lg_free_block": 3932160
  },
  "remoteCTRInfo": {
    "numRemotes": 1,
    "mac": [
      "<REDACTED>"
    ],
    "firmwareVersion": [
      "01.04"
    ],
    "hardwareVersion": [
      "4.00"
    ],
    "brand": [
      "MF"
    ],
    "type": [
      "Remote"
    ],
    "packetCnt": [
      136
    ],
    "batteryLvl": [
      75
    ]
  },
  "protocolType": 1,
  "staMac": "<REDACTED>",
  "result": "0"
}
```
### `/fixture`
Used to control "fixtures" (including the fan itself, uplight, and downlight) of the fan using their integer ids. Here's an example request using this endpoint:
```
curl -s -X POST http://<FAN_IP>/fixture \
  -H "Content-Type: application/json" \
  -d '{
        "action": 4,
        "addr": 231416285,
        "state": {"status": true, "fanSpeed": 4}
      }'
```
I'm not exactly sure what the "action" means, or what all of the possible actions are. An action 3 requests seems to be pulling data, looking like this:
```bash
curl -s -X POST http://<FAN_IP>/fixture \
  -H "Content-Type: application/json" \
  -d '{"action":3, "addr":231416285}'
```
```bash
curl -s -X POST http://192.168.88.65/fixture   -H "Content-Type: application/json"   -d '{"action":3, "addr":231416285}'
```
```json
{"action":3,"addr":231416285,"name":"New Fan 231416285","type":13,"detail":{"dateCode":"2026-66-07","factory":1,"model":"2603-56","motorType":"ADDC153X20","pcbVer":"R.0","fwVer":"03.00.0000","busVer":"00.00"},"state":{"status":true,"fanSpeed":4,"wind":true,"windSpeed":1,"fanDirection":false,"online":true},"tune":{},"staMac":"<REDACTED>","result":"0"}
```

I'm not familar with how the API works already in the integration, so it might be the same format here as it is there. You may notice the integer id for each fixture isn't provided in the original query response, I believe it is calculated with something like this:
First, it seems each of the fixtures has a static hexadecimal identifier or prefix of some kind. I don't know where it got these from, they may be hardcoded in the fan somewhere:
Light identifier: `0x05'
Motor/fan identifier: `0x0D`
Then, the last 3 bytes of the `apMac` address provided in the `/device` response is added to the end. Mine are `CB 21 DD`.
So, therefore the downlight has the hex id `05 CB 21 DD` which converted to decimal is `97198557`, matching my PCAPdroid logs.
The Uplight has the id 97198558, which could just be adding one to the downlight's ID or it could be using the `bleMac` as a base instead of `apMac` since for me those are just one apart.
Then, the fan has the hex id `0D CB 21 DD` which is `231416285` in decimal, which also matches my logs.

