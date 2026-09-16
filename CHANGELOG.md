# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed — documentation restructure, SOURCE link

- **README.md cut down to this example only.** Removed the series "start
  here" framing, the generic device-profile explainer, the "What the profile
  requires" prose (the BIBBs table already said this), "Before you ship" (its
  per-field guidance moved into code comments in `main.cpp`, see below), "Get
  the code", "Link mode", "Troubleshooting", "Extending the example", and
  "Objects and properties" (now generated into `docs/PICS.md` instead).
  Added a prebuilt-binary release link and pointers to the two new documents
  near the top.
- **`TUTORIAL.md` added** - the extending/reviewing material that used to
  bloat the README: the "Add a second analog input" silent-failure walk-through,
  what each object type (including the three commandable outputs) needs the
  app to serve, a Served-by breakdown for both a plain object (Analog Input 1)
  and a commandable one (Analog Output 1), the DeviceCommunicationControl
  `*errorCode` contract, "Reviewing your device", "Using this example as the
  base for a real product" (what to copy out of `common/`, calling
  `BACnetStack_Tick()` correctly), and Troubleshooting.
- **`docs/PICS.md` added** - an ANSI/ASHRAE 135 Annex A format Protocol
  Implementation Conformance Statement, with the objects-and-properties table
  generated from `docs/objects.json` (`tools/gen-objects-properties.py`,
  zero ⚠ rows).
- **`docs/objects.json`'s Device entry gained a `stack` list** separate from
  `accepted`, matching the shape the rest of the series uses: `Object_List`,
  `Protocol_Version`, `Protocol_Revision`, `Protocol_Services_Supported`,
  `Protocol_Object_Types_Supported` and `Device_Address_Binding` are
  device-wide facts the stack computes (rendered as plain `stack`, not `stack
  default, accepted`); `accepted` now holds only the stack's configured
  defaults this example does not override (`System_Status`,
  `Max_APDU_Length_Accepted`, `Segmentation_Supported`, `APDU_Timeout`,
  `Number_Of_APDU_Retries`, `Database_Revision`).
- **Build switched from a prebuilt STATIC library to the adapter's default
  SOURCE mode**: `cmake -B build -S .` / `cmake --build build --config
  Release` compiles the stack straight into the executable, with no
  `tools/build-stack-static.sh` pre-step and no `-DCAS_BACNET_STACK_LINK=...`
  flag. `CMakeLists.txt`'s header comment, `AGENTS.md`, and
  `.github/workflows/release.yml` (drops the static-library cache/build steps
  and the matrix `lib:` entries, asserts `CAS_BACNET_STACK_LINK=SOURCE`, sets
  `"link_mode": "SOURCE"` in the published metrics JSON, and packages
  `TUTORIAL.md` / `docs/PICS.md` alongside the binaries) now match.
- **`main.cpp`'s `CHANGE ALL OF THIS BEFORE YOU SHIP` block absorbed the
  README's "Before you ship" table** as per-field comments, including the
  `DEVICE_NAME` internetwork-uniqueness warning and the DCC password
  plaintext-on-the-wire note.
- **Footprint table left as-is with a refresh note added**: the published
  v1.2.0 numbers were measured from a STATIC-linked binary; the next release
  refreshes them from the SOURCE-mode build now documented.
- Corrected the README's "Expected output" sample, which had dropped the
  `(Network Port 1)` suffix the binary actually prints on the `Listening for
  BACnet/IP` and start-up `TX` lines.

## [1.2.0] - 2026-09-15

### Changed — STATIC link, generated README blocks

- **Stack re-pinned to `6.x` @ `abd4cee1` (reports itself as 6.0.21), tracking the
  `6.x` branch** (`.gitmodules` `branch = 6.x`), up from `6.x-TestTool` @
  `756371c1`.
- **Links the CAS BACnet Stack as a prebuilt STATIC library**
  (`CAS_BACNET_STACK_LINK=STATIC`, built by `tools/build-stack-static.sh` from the
  stack's own project files) instead of compiling the stack from `source/` into
  this project. `CMakeLists.txt`, the README "Link mode" section and
  `AGENTS.md` now describe STATIC only; the adapter's SOURCE mode gets one
  line noting it exists. No DLL mode is documented or shipped.
- **`.github/workflows/release.yml` rewritten**: builds the STATIC library (cached
  on the submodule SHA), asserts `CAS_BACNET_STACK_LINK=STATIC` from
  `CMakeCache.txt`, and publishes `metrics-windows.json` / `metrics-linux.json`
  (binary size, SHA-256 prefix, start-up time to `ready`, stack commit, link
  mode, compiler) as release assets alongside the binaries.
- **README gained three generated/filled sections**: `## Objects and properties`
  (from `docs/objects.json` via `tools/gen-objects-properties.py`), `## The
  BACnet profile example series` (the series profile table, via
  `tools/sync-profile-table.sh`), and `## Footprint` (filled from
  `metrics-*.json` at release; currently the placeholder row).

### Changed — updated to the current CAS BACnet Stack interface

Three interface changes reach this example versus the prior `6.x-TestTool` pin
`756371c1`; the full list, with before/after signatures, is on cas-bacnet-stack
issue #1641.

- **Every `GetProperty*` callback gained a trailing `uint32_t* errorCode`**
  (stack issue #974). The stack presets it to `success` and reads it only on a
  `false` return, so a declining callback can now name the BACnet error the
  client receives. `main.cpp` uses it in exactly one place — `State_Text` with an
  out-of-range array index now answers `Error(property, invalid-array-index)`
  instead of an empty string — and deliberately leaves it alone on every
  catch-all `return false`, because the stack's decline-and-fabricate fallback is
  what answers required properties this application does not serve (the Device's
  `Max_APDU_Length_Accepted`, `APDU_Timeout` and `Number_Of_APDU_Retries`). The
  `DeviceCommunicationControl` callback is the one place in this file where
  `*errorCode` has no fallback and must be set on every `false` return, as its
  commentary explains.
- **`BACnetStack_AddNetworkPortObjectWithNetworkNumber()` is gone**, folded into
  `BACnetStack_AddNetworkPortObject()`, which now always takes the network number
  and its quality. Same arguments, one function.
- **Links are identified by Network Port object instance, not network type**
  (stack issues #822/#556) — the transport callbacks and `SendIAm` all changed.
  Handled in `common/`; `main.cpp` calls the new
  `CASExampleHelper::SetNetworkPortInstance()` before
  `RegisterCommonCallbacks()`.

`common/` is replaced wholesale with the series-wide vendored copy at **2.1.0**
(up from `1.5.1`; see `common/CHANGELOG.md` for its full history) — identical
byte-for-byte across every example in the series.

### Verified

Built on Windows/MSVC (STATIC link) and exercised against a BACnet client:
Who-Is → I-Am (device 389003, vendor 389); ReadProperty of every required
property of all eight objects returns the expected value, `Protocol_Revision`
is 24 and `Object_List` lists all eight; WriteProperty to each commandable
output at two priorities followed by a NULL relinquish falls back correctly to
`Relinquish_Default`; DeviceCommunicationControl accepts `enable` and
`disable-initiation`, rejects the deprecated plain `disable` with
`service-request-denied`, and (with `DCC_PASSWORD` set) rejects a wrong
password with `password-failure`.

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
  section. **All three modes are verified**: `SOURCE` and `STATIC` build and run
  against a live client, and `DLL` mode now loads the stack, binds all 213
  exports, passes the version handshake and runs — plus both of its failure
  paths (library absent; library present but missing an export) report a
  readable error and exit cleanly rather than crashing.
  The stack submodule is pinned to `6.x-TestTool` @ `756371c1`, which carries the
  adapter work merged as cas-bacnet-stack PRs #267 and #268.
  common/ bumped to v1.5.1 (see `common/CHANGELOG.md`) — this is a contract
  change every example in the series needs when it re-syncs.
- **Documentation corrections from a five-persona review** (lead developer,
  educator, junior developer, BACnet newcomer, staff architect): the version
  banner and sample output now match the shipped `common/` version (they claimed
  v1.3.0 against a v1.5.0 tree — in a project whose own docs teach "the printed
  versions are how you detect drift"); the BIBB `-A`/`-B` suffix convention,
  `Protocol_Revision`, BACnet/SC and "BACnet internetwork" are now defined at
  first use; the Verify section names free clients (YABE, Wireshark) alongside
  the commercial one; and two new sections cover what in `common/` is demo-only
  versus production-worthy, and the `BACnetStack_Tick()` cadence and
  single-threading contract.
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

[1.2.0]: https://github.com/chipkin/BACnetProfileExample-B-ASC-CPP/compare/v1.0.0...HEAD
[1.1.0]: https://github.com/chipkin/BACnetProfileExample-B-ASC-CPP/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/chipkin/BACnetProfileExample-B-ASC-CPP/releases/tag/v1.0.0
