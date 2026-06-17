# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-06-16

### Added

- Initial **B-ASC (BACnet Application Specific Controller)** profile example for
  the CAS BACnet Stack in C++.
- **Device** object "Rainbow" - default instance `389001`, vendor `389` (Chipkin
  Automation Systems) - with its full identity (name, description, vendor, model,
  firmware, application software version).
- Read-only sensor objects (the shared minimum across the example series):
  **Analog Input 1** "Bronze" (REAL, degrees Celsius, starts at 21.5), **Binary
  Input 1** "Emerald" (active/inactive), **Multi-State Input 1** "Hot Pink"
  (state 1..3, with `State_Text` "On"/"Off"/"Auto").
- Commandable **output** objects: **Analog Output 1** "Chartreuse" (REAL setpoint),
  **Binary Output 1** "Fuchsia" (active/inactive), **Multi-State Output 1**
  "Indigo" (state 1..3). Each is driven through a 16-slot `Priority_Array` +
  `Relinquish_Default`; the stack resolves `Present_Value`. Writes to read-only
  inputs, and out-of-range values, are rejected.
- **DeviceCommunicationControl** (DM-DCC-B): a management station can stop or
  resume the device's communication, optionally for a time duration and optionally
  behind a password. The callback validates the password (`DCC_PASSWORD`, empty by
  default = accept any) and the stack runs the enable/disable state machine. Notes
  that the deprecated plain `disable` value returns `service-request-denied` at
  Protocol_Revision >= 20 (use `disable-initiation`).
- **Network Port 1** "Vermilion" with full BACnet/IP addressing - `IP_Address`,
  `IP_Subnet_Mask`, `IP_Default_Gateway`, `BACnet_IP_UDP_Port`, `BACnet_IP_Mode`;
  `MAC_Address` is computed by the stack from the IP address and UDP port.
- **DS-RP-B** (ReadProperty) + **DS-WP-B** (WriteProperty) + **DM-DCC-B**
  (DeviceCommunicationControl), plus automatic **Who-Is / I-Am** discovery; an
  unsolicited I-Am is broadcast to the local subnet on start-up.
- All **required properties for Protocol_Revision 24** across every object.
- Interactive keys: `h` help, `q` quit, up/down nudge Analog Input 1 by +/-1.1.
- Command-line options: `--port <n>` and `--deviceID <n>`.
- Cross-platform CMake build that compiles the CAS BACnet Stack from source, with
  strict warnings (`-Wall -Wextra` / `/W4`) on the example's own sources only.
- Self-contained repository: the shared helper is vendored in `common/`, and the
  CAS BACnet Stack is included as a git submodule at
  `submodules/cas-bacnet-stack` - clone with `--recursive` and build.
- GitHub Actions workflow that builds Windows + Linux and publishes a release on
  a `vX.Y.Z` tag, with a smoke-test step before packaging.

[Unreleased]: https://github.com/chipkin/BACnetProfileExample-B-ASC-CPP/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/chipkin/BACnetProfileExample-B-ASC-CPP/releases/tag/v1.0.0
