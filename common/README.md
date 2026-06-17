# `common/` — shared example helper

This folder holds the boilerplate that is identical for every example in the
BACnet profile example series, vendored into this repository so the example
builds on its own. It lets the profile's `main.cpp` stay short and read like a
tutorial, focused only on what makes the B-SS profile different.

## What's here

| File | Purpose |
|------|---------|
| `CASExampleHelper.h` / `.cpp` | UDP socket on the BACnet/IP port + the transport/time callbacks; version/help printing; `--port` / `--deviceID` parsing; keyboard commands (h/q/up/down); local-IPv4 / broadcast helpers; broadcast I-Am on start-up. |
| `SimpleUDP.h` / `.cpp` | A tiny cross-platform UDP socket wrapper (Winsock on Windows, BSD sockets on Linux/macOS). |
| `CASBACnetStackExampleConstants.h` | A self-contained copy of the handful of BACnet enumeration values the example uses (each section names the CAS BACnet Stack header that defines the full enumeration). |

## How `main.cpp` uses it

```cpp
const uint16_t port = CASExampleHelper::ParsePortArg(argc, argv, 47808);
g_deviceInstance    = CASExampleHelper::ParseDeviceIdArg(argc, argv, g_deviceInstance);
CASExampleHelper::PrintVersion(APP_NAME, APP_VERSION);  // app + stack version
CASExampleHelper::SetupUDP(port);
CASExampleHelper::RegisterCommonCallbacks();            // receive / send / time
// ... register the example's own GetProperty callbacks, add device + objects ...
CASExampleHelper::SendIAm(g_deviceInstance);            // announce on start-up

while (running) {
    BACnetStack_Tick();
    switch (CASExampleHelper::PollKey()) { /* h / q / up / down */ }
}
CASExampleHelper::RestoreInput();
```

The CAS BACnet Stack (a git submodule of this repository) is compiled from
source, so its C API (`CASBACnetStackDLL.h`) is called directly as
`BACnetStack_*` — there is no DLL to load at runtime.
