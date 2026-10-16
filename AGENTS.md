# AGENTS.md

Guidance for AI coding agents working in this repository. See
<https://agents.md/> for the format. Human contributors should read
[README.md](README.md) first, then [TUTORIAL.md](TUTORIAL.md).

## What this project is

A **tutorial** C++ example that implements the BACnet **B-ASC (Application
Specific Controller)** device profile using the CAS BACnet Stack. It is one of
a series - one git repo per BACnet profile - and adds
DeviceCommunicationControl (DM-DCC-B) and commandable outputs (DS-WP-B) on top
of the shared read-only sensor objects every example in the series carries.
The top priority is that the code reads like a tutorial a customer can learn
from and copy-paste. Favour clarity over cleverness.

## Layout

This repository is self-contained:

- `main.cpp` - the example device.
- `common/` - the shared helper (vendored).
- `README.md` - what this example is. Keep it short and about THIS example only.
- `TUTORIAL.md` - how to extend and review the example. Long-form material that
  would bloat the README belongs here.
- `docs/PICS.md` - the Protocol Implementation Conformance Statement. Its
  objects-and-properties section is GENERATED from `docs/objects.json`; do not
  hand-edit between the `OBJECTS-PROPERTIES` markers.
- `docs/objects.json` - the input to that generator. Update it in the same change
  as any `main.cpp` change that adds an object or a `GetProperty*` branch.
- `tests/` - the Wire Tests (Python, standard library only); `wiretest/` - the
  series' shared harness they use (vendored, like `common/`; do not edit here).
- `submodules/cas-bacnet-stack/` - the **CAS BACnet Stack** as a git submodule
  (private; compiled from source). After cloning, run
  `git submodule update --init --recursive`.

The `PROFILE-TABLE` block in README.md is also generated, from the example-series
repository's `docs/profile-table.md`. Edit it there, not here.

## Build

Plain CMake, identical on every platform, in the adapter's default SOURCE mode
(the stack's sources are compiled into the executable - no prebuilt library, no
DLL, no per-platform pre-step):

```bash
git submodule update --init --recursive   # once, if not cloned with --recursive
cmake -B build -S .
cmake --build build --config Release
```

The first build compiles the whole stack (~600 files) and takes a few minutes;
rebuilds after that are incremental and fast. Use `-D CAS_STACK_DIR=...` only if
your stack lives outside the bundled submodule. Do not reintroduce a link-mode
flag or a series-root build script into the documented build: a customer
downloads this repository on its own and must be able to build it with the two
commands above.

## Run

```bash
./build/BACnetExampleBASC [--port 47808] [--deviceID 389003]   # Linux/macOS
.\build\Release\BACnetExampleBASC.exe [--port 47808] [--deviceID 389003]   # Windows
```

Interactive keys while running: `h` help, `q` quit, up/down disturb the simulated temperature (Analog Input 1).

## Conventions

- Device is named "Chipkin Example B-ASC"; objects use the series' colour names; vendor id 389.
- Implement **only** the services and objects the B-ASC profile requires - but
  expose **every required property** of each object for Protocol_Revision 30.
- Outputs are **commandable**: store the 16-slot `Priority_Array` +
  `Relinquish_Default` in the app (the `Commandable` struct); let the stack
  resolve `Present_Value`. Writes land via the `SetProperty*` callbacks (value)
  and `SetPropertyNull` (relinquish).
- The outputs act through the **Simulation** in `main.cpp` section 1b
  (`ActuatorSimulationTick()`, the same as B-SA's), driven by `ResolvedCommand()`;
  it is outside the BACnet Surface and labelled so in the README. Its
  disconnected-valve hook is test-only (`CAS_EXAMPLE_TEST_ACTUATOR_FAULT_FILE`,
  an environment variable) - never a command-line option or a menu key.
- DeviceCommunicationControl (DM-DCC-B): the stack runs the enable/disable state
  machine; the `DeviceCommunicationControl` callback just validates the password
  (`g_dccPassword`, from `--dcc-password`) and logs. What it silences is the I-Am
  heartbeat (`HeartbeatTick()`, every 5 s): the stack refuses to send it while
  `disable-initiation` is in force; the example keeps no DCC state of its own.
  The deprecated plain `disable` (1) is rejected by the stack at
  Protocol_Revision >= 20 - only `enable` (0) and `disable-initiation` (2) apply.
  This callback has no fallback error code: it must set `*errorCode` on every
  `false` return.
- Every `GetProperty*` callback ends with `uint32_t* errorCode`. Leave it alone
  on a catch-all decline (the stack's decline-and-fabricate default answers
  required properties this app does not serve); set it only where this device
  knows the read is wrong (`State_Text` out of range is the one case here).
- Match the surrounding code style: `const`-correct parameters, check every stack
  return value, keep `main.cpp` linear and well-commented.
- **Never edit `common/` in this repo alone** - it is a vendored copy shared by
  every example in the series, with its own version (`COMMON_VERSION`) and
  changelog (`common/CHANGELOG.md`). To change it: edit, bump the version, add
  a changelog entry, then re-copy `common/` into every example repository.

## How to verify a change

The Wire Tests in `tests/` automate this (README "Wire Tests"): discovery,
commanding, the actuator Failure Modes, and DeviceCommunicationControl silencing
and resuming the heartbeat - `python3 tests/run_wire_tests.py --exe
build/BACnetExampleBASC`. Run them after any change. A new check must fail with
its feature removed (tests/README.md has the mutation table). Beyond them,
verification is behavioural:

1. Build, then run one instance on a clear UDP port.
2. With a BACnet client (e.g. the CAS BACnet Explorer), send **Who-Is** and
   confirm **I-Am** from the device instance.
3. **ReadProperty** every required property of every object and confirm the
   values; confirm `Protocol_Revision` is 30 and `Object_List` lists all objects.
4. **WriteProperty** a commandable output's `Present_Value` at a priority, re-read
   it (and its `Priority_Array`), then write NULL to relinquish and confirm it
   falls back to `Relinquish_Default`. Confirm a write to a read-only input is
   rejected.
5. **DeviceCommunicationControl**: confirm `disable-initiation` and `enable`
   SimpleACK, the deprecated `disable` is rejected (service-request-denied), and a
   wrong password (start with `--dcc-password <string>`) is rejected
   (password-failure).
6. If you changed the objects or their properties, regenerate `docs/PICS.md`
   (`python tools/gen-objects-properties.py BACnetProfileExample-B-ASC-CPP` from
   the series root) and confirm no row comes out flagged with ⚠.

## Releasing

Bump `APP_VERSION` in `main.cpp` and add an entry to [CHANGELOG.md](CHANGELOG.md),
then tag `vX.Y.Z`. The GitHub Actions workflow builds and publishes the release.

## License

See [LICENSE](LICENSE). The CAS BACnet Stack is a separate, commercially
licensed product and is not covered by it.
