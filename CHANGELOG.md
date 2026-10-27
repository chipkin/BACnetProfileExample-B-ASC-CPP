# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

_No changes yet._

## [1.5.0] - 2026-10-27

Built on CAS BACnet Stack 6.x (`69b6249f`).

### Added

- **`--deviceName <text>`** sets the Device's Object_Name at start-up, like
  `--deviceID` sets its instance, so two units can be installed together (BACnet
  requires both to be configurable, cl. 12.1.1.3 and 12.1.1.4). The default is
  unchanged (`Chipkin Example B-ASC`). A name must be 1 to 255 bytes with no control
  characters, otherwise the example warns and keeps the default. The name is not
  writable over the network.

### Changed

- **`--xml` works.** The help listed it but the example never read it; each received
  and sent frame now prints as an XML block.
- Vendored `common/` updated to 3.5.0 (adds an optional `--deviceName` help line).
- The self-tests' default `--port` is 47827, this example's own port in the series.
- The PICS objects-and-properties block cites the CAS BACnet Stack's property
  profiles; no row changed.

### Fixed

- **Requests no longer go unanswered on Windows**: a request arriving just as the UDP
  receive timed out was silently dropped.
- **PICS: `Database_Revision` is 8**, not a stack default of 0. The stack counts the
  objects added at start-up (cl. 12.11).

## [1.4.0] - 2026-10-16

Built on CAS BACnet Stack 6.x (`64b2cfac5`, 6.0.23), Protocol_Revision 30. Includes
the changes first developed as 1.2.1 to 1.3.0.

The example now performs the B-ASC Profile Function (ANSI/ASHRAE 135-2024 Annex L.4.3):
it allows other devices to modify its objects and responds to communication control
messages, with something for communication control to silence. The BACnet Surface is
unchanged (DS-RP-B, DS-WP-B, DM-DDB-B, DM-DOB-B, DM-DCC-B; the same eight objects).

### Added

- **I-Am heartbeat**: an unsolicited I-Am broadcast every 5 s. DeviceCommunicationControl
  `disable-initiation` stops it (cl. 16.1.2); `enable`, or the end of the time duration,
  resumes it.
- **Actuator simulation**: the outputs act on the winning command and the inputs report
  it back. Analog Output 1 has `Min_Pres_Value` 10.0 and `Max_Pres_Value` 30.0 (out of
  range setpoints get `value-out-of-range`) and `Reliability` (`no-output` while the
  simulated valve actuator is disconnected).
- **Segmentation is supported** (`segmented-both`, `Max_Segments_Accepted` 16).
- Automated self-tests under `tests/` (`run_wire_tests.py`), which also run in CI.
- New documents: `TUTORIAL.md` (extending and reviewing the example) and
  `docs/PICS.md` (the conformance statement).

### Changed

- **The Device is now named "Chipkin Example B-ASC"** (was "Rainbow") so examples on one
  network can be told apart.
- **Protocol_Revision is 30** (was 24).
- The up/down keys disturb the simulated temperature; the valve brings it back.
- Build documentation uses the adapter's default source mode: `cmake -B build -S .`
  then `cmake --build build --config Release`, on every platform. If you have an older
  build tree, run `cmake -B build` again.
- README and PICS describe what can be observed, the simulation and the self-tests.
- `common/` updated to 3.4.0: a broadcast addressed to the socket's own address is sent
  to the subnet broadcast.

### Fixed

- **`--dcc-password` was advertised but ignored.** It is now read, and a start-up line
  says a password is required (never the password itself). With a password set, a wrong
  or missing one gets `password-failure`; the deprecated `disable` gets
  `service-request-denied`.
- **README overclaimed `disable-initiation`.** Per cl. 16.1.2 a device may still answer
  Who-Is and Who-Has, so README and PICS now say what is observable.
- **`Application_Software_Version` and `Firmware_Revision` were hardcoded** to "1.0.0";
  they now report the build's version and the CAS BACnet Stack version.

## [1.2.0] - 2026-09-15

Built on CAS BACnet Stack 6.x (`abd4cee1`, 6.0.21). Includes the changes first developed
as 1.1.0.

### Added

- **Who-Has / I-Have (DM-DOB-B) is advertised.** The device always answered Who-Has but
  `Protocol_Services_Supported` said it did not. Who-Is/I-Am and Who-Has/I-Have are now
  reported.
- **`Description` on the Device is readable** (was `unknown-property`).
- **`Units` on the Analog Output** is served (the stack was substituting `no-units`).
- `--help` and `--version`.
- A recipe for adding a second analog input, a per-object-type checklist and a table of
  what the application must serve.
- README sections for the objects and properties, the example series and the footprint;
  releases publish `metrics-windows.json` and `metrics-linux.json` (binary size,
  start-up time, stack commit).

### Changed

- **The stack is linked through the `CASBACnetStack::Adapter` CMake target** instead of
  globbing the stack sources. `CAS_BACNET_STACK_LINK` selects `SOURCE`, `STATIC` or `DLL`
  mode.
- **Every `GetProperty*` callback gained a trailing `uint32_t* errorCode`**, so a
  callback that declines can name the BACnet error. `State_Text` with an out of range
  array index now returns `invalid-array-index`.
- `BACnetStack_AddNetworkPortObjectWithNetworkNumber()` is folded into
  `BACnetStack_AddNetworkPortObject()`; links are identified by Network Port object
  instance. `common/` is updated to 2.1.0.
- Documentation corrections: version banner and sample output match the shipped
  `common/`, terms defined at first use, and new sections on demo-only code in `common/`
  and the `BACnetStack_Tick()` contract.

### Fixed

- **The default device instance is now 389003**, not 389001, which belongs to B-SS.
  Two examples on one subnet no longer claim the same instance. `--deviceID` still
  overrides.
- DeviceCommunicationControl returned an unset error code when the request targeted a
  different device instance.

## [1.0.0] - 2026-06-16

### Added

- Initial **B-ASC (BACnet Application Specific Controller)** profile example for the CAS
  BACnet Stack in C++.
- **Device** object with its full identity, and Network Port 1 with BACnet/IP addressing.
- Read-only sensor objects: Analog Input 1, Binary Input 1, Multi-State Input 1.
- Commandable outputs: Analog Output 1, Binary Output 1, Multi-State Output 1, each with
  a 16-slot `Priority_Array` and `Relinquish_Default`.
- DS-RP-B, DS-WP-B, DM-DCC-B (with optional password; the deprecated plain `disable`
  returns `service-request-denied`), and Who-Is / I-Am discovery.
- All required properties for Protocol_Revision 24 on every object.
- Interactive keys (`h`, `q`, up/down) and the options `--port` and `--deviceID`.
- Cross-platform CMake build, with the CAS BACnet Stack as a git submodule (clone with
  `--recursive`), and a GitHub Actions workflow that builds Windows and Linux and
  publishes a release on a `vX.Y.Z` tag.
