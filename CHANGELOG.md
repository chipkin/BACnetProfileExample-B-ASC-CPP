# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - unreleased

> Not tagged yet: `v1.0.0` is the only tag in this repository, so there is no
> 1.1.0 build. `release.yml` publishes binaries on a `v*.*.*` tag; until that tag
> exists this section describes what is on the branch, not what shipped.

### Added

- **DM-DOB-B (Who-Has / I-Have) is now advertised.** The device always answered
  Who-Has, but `Protocol_Services_Supported` is emitted verbatim from the stack's
  service bitstring, whose defaults are Who-Is + Who-Has + ReadProperty only -
  `I-Am` and `I-Have` stay false. So the device performed both and told every
  client it supported neither. Who-Is/I-Am (DM-DDB-B) and Who-Has/I-Have are now
  enabled explicitly, which is what makes the README's BIBB claims true on the
  wire.
- **`Description` on the Device object is now readable.** It was served from a
  Get callback but never enabled. `Description` is OPTIONAL on a Device, and the
  stack checks `IsPropertyEnabled` before reaching the callbacks - so the branch
  was dead code and a client got `unknown-property`.
- **`Units` on the Analog Output.** Required on an Analog Output as well as an
  Analog Input; only the input's was served. This does not error - the stack
  silently substitutes `no-units(95)` - so the setpoint reported no engineering
  units next to a degC sensor.
- `--help` / `--version` (via `common/` v1.2.0); `--version` prints the example,
  stack, and helper versions.
- A real "add a second analog input" recipe, a per-object-type checklist of what
  the application must serve, and a who-serves-what table.

### Changed

- **Links the CAS BACnet Stack through the `CASBACnetStack::Adapter` CMake
  target instead of hand-globbing the stack's `source/*.cpp`.** `main.cpp` and
  `common/CASExampleHelper.cpp` now include `CASBACnetStackAdapter.h` and call
  `LoadBACnetFunctions()` once at the top of `main()`; every `BACnetStack_*`
  call site is otherwise unchanged. `CAS_BACNET_STACK_LINK` (`SOURCE` default,
  or `STATIC`/`DLL`) picks the link mode — see the README's new "Link modes"
  section. `SOURCE` and `STATIC` mode are fully verified; `DLL` mode's failure
  paths are verified (absent DLL, DLL missing a required export — both fail
  cleanly via `CASBACnetStackAdapter_LastError()`, never a crash) but its
  success path could not be demonstrated during verification because the
  current `ReleaseDll|x64` MSVS build of the stack is missing a few exports for
  reasons not yet root-caused — tracked upstream. **TEMPORARY:** the stack
  submodule pin currently points at the `adapter-cpp-package` branch tip
  (stacked on `adapter-cpp-generate`), not `6.x-TestTool` — see cas-bacnet-stack
  PRs #267 and #268; re-pin once both merge.
  common/ bumped to v1.5.0 (see `common/CHANGELOG.md`) — this is a contract
  change every example in the series needs when it re-syncs.
- **Stack pin moved to `6.x-TestTool` @ `b681f58d` (2026-07-31).** 38 commits
  ahead of the previous pin (`92c91d74`); includes the removal of the 13
  `RegisterHookProperty*` exports, the `DecodeAsXML`/`DecodeAsJSON` →
  `DecodeAs` fold, the `SetCOVMultipleSettings` rename, the
  `SetBackupAndRestoreEnabled` signature change (absorbs
  `backupFailureTimeout`), and the removal of `SetObjectTypeSupported` — none
  of which this example calls. Known cosmetic side effect: the newly merged
  BACnet/SC datalink logs a one-time "UUID has not been set" error on the
  debug callback at start-up in applications that never configure BACnet/SC;
  it latches its error flag and goes quiet. Functionality is unaffected.
- **Stack pin moved to the series `6.x` branch (CAS BACnet Stack 6.0.0.0).**
  Which stack version this example requires is a material licensing fact.
- The commandable-setup loop carries `{type, instance}` pairs instead of a
  hardcoded instance `1`, and its comment now states the truth: those calls are
  a no-op for Analog/Binary/Multi-State Output (the stack treats those as
  commandable unconditionally) and are load-bearing only for the optionally-
  commandable Value types.
- The WriteProperty log prints the real object instance.

### Fixed

- **DeviceCommunicationControl returned `false` with `*errorCode` unset** when
  the request targeted a different device instance, putting
  `Error Code = success(84)` on the wire.

- **Default device instance is now `389003`, not `389001`.** The series
  device-instance allocation assigns each profile its own default so that several
  examples can run on one subnet (B-SS `389001`, B-SA `389002`, B-ASC `389003`,
  ...); this example shipped using `389001`, which is **B-SS's** instance. Any
  two of B-SS / B-ASC running together therefore both claimed device `389001` —
  duplicate device instances on a subnet are a BACnet conformance problem, and
  they make discovery ambiguous in exactly the way that is hardest to debug (see
  the SO_REUSEADDR note in the series runbook). `--deviceID` still overrides, as
  BACnet requires.

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

[1.1.0]: https://github.com/chipkin/BACnetProfileExample-B-ASC-CPP/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/chipkin/BACnetProfileExample-B-ASC-CPP/releases/tag/v1.0.0
