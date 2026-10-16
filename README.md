# BACnet B-ASC (Application Specific Controller) - C++ example

A minimal, copy-paste-friendly example showing how to implement the BACnet
**B-ASC (BACnet Application Specific Controller)** device profile in C++ using the
[CAS BACnet Stack](https://store.chipkin.com/services/stacks/bacnet-stack).
It listens on **BACnet/IP (UDP 47808)**, answers **ReadProperty**, accepts
**WriteProperty** to its commandable outputs, responds to
**DeviceCommunicationControl**, and is discoverable via **Who-Is / I-Am**.

**[Download a prebuilt binary](https://github.com/chipkin/BACnetProfileExample-B-ASC-CPP/releases)**
(Windows and Linux x64) - or build it yourself, see [Build](#build) below.

- **[TUTORIAL.md](TUTORIAL.md)** - how to extend this example and how to review
  it for conformance. Read it when you start turning this into your own device.
- **[docs/PICS.md](docs/PICS.md)** - the Protocol Implementation Conformance
  Statement: every object, every property, and who answers it.

> **Versions:** this document describes **example v1.3.0**, built and verified
> against **CAS BACnet Stack 6.0.23** (`6.x` @ `64b2cfac5`), at
> **Protocol_Revision 30**, with the vendored `common/` helper at **v3.4.0**.
> Running the example prints all three - if what it prints disagrees with this
> line, trust the program and check `CHANGELOG.md`.
>
> **Protocol_Revision** is the revision of the ASHRAE 135 standard a device claims to conform
> to. It is a number every BACnet device advertises, and it changes real behaviour: at revision
> 20 and above, for example, the deprecated plain `disable` form of
> DeviceCommunicationControl must be rejected (see [DeviceCommunicationControl](#devicecommunicationcontrol-the-b-asc-addition) below).

## DeviceCommunicationControl (the B-ASC addition)

`DeviceCommunicationControl` lets a management station tell a device to go quiet -
useful to silence a misbehaving or noisy device during commissioning - and later
to resume. The request carries:

- an **enable/disable** choice,
- an optional **time duration** (minutes) after which the device re-enables on its
  own, and
- an optional **password**.

The CAS BACnet Stack runs the actual enable/disable state machine and the
re-enable timer; this example's callback (`DeviceCommunicationControl` in
`main.cpp`) just **validates the password** and logs what was asked.

Concretely, the callback:

1. Rejects a request for any device instance other than this one, naming
   `optional-functionality-not-supported` on the wire.
2. Compares the supplied password to the configured one (`g_dccPassword`, set
   with `--dcc-password`) by **length first, then bytes** - never `strcmp`,
   because a BACnet CharacterString may legitimately contain an embedded NUL
   that `strcmp` would silently stop at. A device with no configured password
   (the shipped default) accepts any request. A mismatch is rejected with `*errorCode =
   ERROR_CODE_PASSWORD_FAILURE`, which the stack pairs with `Error Class =
   SECURITY` (clause 16.1.1.3.1).
3. On a correct (or absent) password, accepts and logs the requested action -
   `enable`, the deprecated `disable`, or `disable-initiation` - and the
   optional time duration.
4. **Sets `*errorCode` on every `false` return, with no exception.** Unlike the
   `SetProperty*` callbacks (which have a sensible `writeAccessDenied`
   fallback), DeviceCommunicationControl has no default: the stack presets
   `*errorCode` to `success` (84) and, on `false`, answers `Error Class =
   SECURITY` when the code is `password-failure` or `Error Class = SERVICES`
   otherwise. Returning `false` without setting `*errorCode` puts the literal
   nonsense "Error Code = success(84)" on the wire - `main.cpp` never does
   that.

> **Protocol_Revision >= 20 note:** the plain **`disable`** value (stop initiating
> *and* responding) is **deprecated**. At Protocol_Revision 30 the stack rejects it
> with `service-request-denied`, as 135-2024 clause 16.1.2 requires ("If the
> request is valid and the 'Enable/Disable' parameter is the deprecated value
> DISABLE, the request shall be ignored..."). The modern choice is
> **`disable-initiation`**. So only `enable` and `disable-initiation` take
> effect. The callback still logs what the client asked for on the deprecated
> path, because the rejection happens in the stack after the callback returns.

**What you can observe today, and what you cannot.** The password check and the
SimpleACK / Error answers are on the wire. The *effect* of `disable-initiation`
is not: clause 16.1.2 stops a device initiating messages *other than* I-Am and
I-Have sent in answer to Who-Is and Who-Has, and this example initiates nothing
after its start-up I-Am. So after a `disable-initiation` it behaves exactly as
before. The stack holds the communication state; the example has no periodic
request of its own that you could watch stop.

The example ships with **no password** (accept any request). Start it with
`--dcc-password <string>` to require one; a missing or wrong password is then
rejected with `Error Class = SECURITY`, `Error Code = password-failure`. In your
product, set the password from your own configuration.

## The device this example creates

```
Device 389003  "Chipkin Example B-ASC"   (Vendor 389 - Chipkin Automation Systems)
    │
    ├── Analog Input  1       "Bronze"      Present_Value  21.5    (REAL, degrees Celsius; read-only)
    ├── Binary Input  1       "Emerald"     Present_Value  inactive  (0 = inactive / 1 = active; read-only)
    ├── Multi-State Input 1   "Hot Pink"    Present_Value  1       (state, 1..3; read-only)
    ├── Analog Output 1       "Chartreuse"  Present_Value  20.0    (REAL setpoint; WRITABLE, commandable)
    ├── Binary Output 1       "Fuchsia"     Present_Value  inactive  (0/1; WRITABLE, commandable)
    ├── Multi-State Output 1  "Indigo"      Present_Value  1       (state, 1..3; WRITABLE, commandable)
    └── Network Port 1        "Vermilion"   the BACnet/IP port     (required on every device)
```

The three **input** objects (Bronze, Emerald, Hot Pink) are the shared minimum
every example in this series carries; the three **output** objects (Chartreuse,
Fuchsia, Indigo) are commandable via a `Priority_Array`. Object names follow this
series' colour-naming convention (Device is always "Chipkin Example B-ASC").

## What this example supports

The example implements exactly the capabilities below - and nothing more, which
is the point of a profile example. These capabilities satisfy the **B-ASC
(Application Specific Controller)** profile; because B-ASC's BIBBs are a superset of the
**B-GENERAL** baseline, a conformant B-ASC device necessarily satisfies
**B-GENERAL** too. That is subsumption, not a second claim: this repository still
claims exactly one profile.

### BIBBs (BACnet Interoperability Building Blocks)

| BIBB | Description | Supported |
|------|-------------|:---------:|
| DS-RP-B | Data Sharing - ReadProperty - B | ✅ |
| DS-WP-B | Data Sharing - WriteProperty - B | ✅ |
| DM-DCC-B | Device Management - DeviceCommunicationControl - B | ✅ |
| DM-DDB-B | Device Management - Dynamic Device Binding - B | ✅ |
| DM-DOB-B | Device Management - Dynamic Object Binding - B | ✅ |

### Services (executed / B-side)

| Service | Notes |
|---------|-------|
| ReadProperty | Responds to property reads (DS-RP-B). |
| WriteProperty | Accepts writes to the commandable outputs' Present_Value (DS-WP-B). |
| DeviceCommunicationControl | Stops/resumes communication, optionally timed/passworded (DM-DCC-B). |
| Who-Is / I-Am | Answers Who-Is with I-Am, and broadcasts an I-Am on start-up (DM-DDB-B). |
| Who-Has / I-Have | Answers Who-Has with I-Have (DM-DOB-B). |

### Object types

| Object type | Instance | Name | Access |
|-------------|:--------:|------|--------|
| Device | 389003 | Chipkin Example B-ASC | - |
| Analog Input | 1 | Bronze | read-only |
| Binary Input | 1 | Emerald | read-only |
| Multi-State Input | 1 | Hot Pink | read-only |
| Analog Output | 1 | Chartreuse | writable (commandable) |
| Binary Output | 1 | Fuchsia | writable (commandable) |
| Multi-State Output | 1 | Indigo | writable (commandable) |
| Network Port | 1 | Vermilion | - |

Every required property of every object, and who answers it, is in
[docs/PICS.md](docs/PICS.md).

## Requires the CAS BACnet Stack (licensed product)

This example **builds against the CAS BACnet Stack, which is a commercial Chipkin
product** - it is not free or open source, and there is no public/trial build.
The stack is referenced here as the **private** git submodule
`submodules/cas-bacnet-stack`; you can only fetch and build it once you have a CAS
BACnet Stack license and access to that repository.

**To get the CAS BACnet Stack (and access to build this example), contact
Chipkin:** <https://store.chipkin.com/services/stacks/bacnet-stack> or
sales@chipkin.com.

You do not need a stack licence to *read* this example, or to run a
[prebuilt release binary](https://github.com/chipkin/BACnetProfileExample-B-ASC-CPP/releases).
The licence is what lets you *build* it - that is the part the stack submodule
gates.

## What's in this repository

This is a **self-contained** project. It ships:

- `main.cpp` - the example device.
- `common/` - the shared helper (UDP, callbacks, CLI, keyboard) vendored in.
- `CMakeLists.txt` - the build, the same on Windows, Linux, and macOS.
- `docs/PICS.md` - the conformance statement.
- `tests/` - the Wire Tests (see [Wire Tests](#wire-tests)), and `wiretest/`, the
  series' shared Python harness they are written against (vendored, like `common/`).
- `submodules/cas-bacnet-stack/` - the **CAS BACnet Stack as a git submodule**
  (private; requires a license - see above). Its sources are compiled into the
  executable, so there is no library or DLL to build, ship, or install.

## Prerequisites

- A C++17 compiler (MSVC, GCC, or Clang).
- CMake >= 3.15.
- Git (to fetch the stack submodule).

### Windows

- **C++ compiler** - install
  [Visual Studio Community](https://visualstudio.microsoft.com/downloads/)
  (free) and select the **"Desktop development with C++"** workload.
- **CMake** - from <https://cmake.org/download/>, or `winget install Kitware.CMake`.

### Linux / macOS

- Debian/Ubuntu: `sudo apt install build-essential cmake git`
- macOS: `xcode-select --install` and `brew install cmake`

## Build

CMake only, and the same two commands on every platform:

```bash
git clone --recursive https://github.com/chipkin/BACnetProfileExample-B-ASC-CPP.git
cd BACnetProfileExample-B-ASC-CPP

cmake -B build -S .
cmake --build build --config Release
```

Already cloned without `--recursive`? Run `git submodule update --init --recursive`
first - the build needs the stack submodule.

> **The first build takes a few minutes** - it compiles the entire CAS BACnet
> Stack (~600 source files) into the executable. Rebuilds after that are
> incremental and take seconds.

If your CAS BACnet Stack lives somewhere other than the bundled submodule, point
CMake at it: `cmake -B build -S . -D CAS_STACK_DIR=/path/to/cas-bacnet-stack`.

## Run

```bash
# Linux / macOS
./build/BACnetExampleBASC

# Windows
.\build\Release\BACnetExampleBASC.exe
```

Expected output:

```
BACnet B-ASC (Application Specific Controller) Example - C++ v1.3.0
CAS BACnet Stack version: 6.0.23.0
Common helper (common/) version: 3.4.0
FYI: Listening for BACnet/IP on UDP port 47808 (Network Port 1).
TX 21 bytes to 192.168.3.255:47808 (broadcast) (Network Port 1) - Unconfirmed: I-Am
FYI: Device 389003 ("Chipkin Example B-ASC") ready. Vendor ID 389. Press 'h' for help.
```

The `TX` line is the start-up I-Am the device broadcasts to announce itself. It
goes to the **local subnet broadcast** address (here `192.168.3.255`, computed
from the Network Port's interface), not the global `255.255.255.255`. As clients
talk to the device you'll see `RX ... bytes from ...` and `TX ... bytes to ...`
lines; a WriteProperty to an output prints a line such as `WriteProperty:
Analog Output 1 (Chartreuse) <- 42.50 @ priority 8`, and a
DeviceCommunicationControl prints e.g. `DeviceCommunicationControl:
disable-initiation (keep responding) (indefinitely)`.

The device listens on UDP **47808** (BACnet/IP). Allow that port through your
firewall. To use a different port, pass `--port` (see below).

> **A wall of red `Error:` lines at start-up is expected and is not your bug** -
> it is the stack's own debug logging (the device hearing its own broadcast I-Am,
> and a one-time BACnet/SC UUID notice). [TUTORIAL.md](TUTORIAL.md#troubleshooting)
> explains both.

### Command-line options

| Option | Default | Meaning |
|--------|---------|---------|
| `--port <n>` | `47808` | UDP port to listen on (BACnet/IP). |
| `--deviceID <n>` | `389003` | The device's BACnet instance number (BACnet requires this to be configurable). |
| `--dcc-password <string>` | none | Require this password on DeviceCommunicationControl. Prints `FYI: DeviceCommunicationControl requires a password` at start-up (never the password). |
| `--help`, `-h` | - | Show usage and exit. |
| `--version` | - | Print the example, stack, and `common/` helper versions, then exit. |

### Interactive commands

While the example runs, these keys are available:

| Key | Action |
|-----|--------|
| `h` | Show the version information and this command list. |
| `q` | Quit. |
| up arrow | Increase Analog Input 1 (`Bronze`) by 1.1. |
| down arrow | Decrease Analog Input 1 (`Bronze`) by 1.1. |

The up/down keys change the live `Present_Value` of the analog input, so a client
re-reading it sees the new value.

## Verify

Use a BACnet client such as the
[**CAS BACnet Explorer**](https://store.chipkin.com/products/tools/cas-bacnet-explorer):

1. **Discover** - send a **Who-Is**. The device replies with **I-Am** from
   instance **389003** (vendor **389**). It also broadcasts an I-Am at start-up.
2. **Browse the object model** - the device shows eight objects: the Device
   (`Chipkin Example B-ASC`), three inputs, three outputs, and the Network Port
   (`Vermilion`). Reading the Device's `Object_List` returns all eight.
3. **Read the Device** - ReadProperty `389003` -> `Object_Name` returns
   `"Chipkin Example B-ASC"`; `Protocol_Revision` returns `30`; `Description` returns the
   profile description string.
4. **Read a sensor** - ReadProperty Analog Input `1` -> `Present_Value` returns
   `21.5`; `Units` returns `degrees-Celsius`. Repeat for Binary Input `1`
   (`"Emerald"`) and Multi-State Input `1` (`"Hot Pink"`).
5. **Command an output** - WriteProperty Analog Output `1` `Present_Value` = `42.5`
   at priority `8`; re-read `Present_Value` (`42.5`) and `Priority_Array[8]`
   (`42.5`); write `NULL` at priority `8` to relinquish; `Present_Value` returns to
   `20.0` (its `Relinquish_Default`). Repeat for Binary/Multi-State Output. A write
   to a read-only *input*, or an out-of-range value, is rejected.
6. **Communication control (the B-ASC test)** - send a **DeviceCommunicationControl**
   with `disable-initiation`: the device SimpleACKs and keeps answering reads.
   (It initiates nothing after start-up, so there is nothing visible to stop -
   see [DeviceCommunicationControl](#devicecommunicationcontrol-the-b-asc-addition).)
   Send `enable` to resume. Sending the deprecated plain `disable` returns
   `service-request-denied` at Protocol_Revision 30 - that is correct. Restart
   the example with `--dcc-password s3cret`: a request with no password or the
   wrong one is rejected with `security` / `password-failure`, and one with
   `s3cret` is SimpleACKed.

For a property-by-property review against the conformance statement, see
[TUTORIAL.md](TUTORIAL.md).

## Wire Tests

The discovery half of the checks above, automated: a Python BACnet client drives
the running example over BACnet/IP from outside it, the way a client discovers a
device - Who-Is, the Device's `Object_List`, then for every object its
`Property_List` and a ReadProperty of every property it lists. Every read must
come back as a value; an Error, Reject or Abort fails the run. Python 3 standard
library only:

```bash
python3 tests/run_wire_tests.py --exe build/BACnetExampleBASC          # Linux/macOS
python tests\run_wire_tests.py --exe build\Release\BACnetExampleBASC.exe   # Windows
```

It ends with `ALL WIRE TESTS PASSED` (exit 0). CI runs it on Linux after the
smoke test. [tests/README.md](tests/README.md) says what each check proves. It
does not yet test commanding the outputs (step 5) or DeviceCommunicationControl
(step 6).


## The BACnet profile example series

<!-- PROFILE-TABLE:BEGIN (generated from cas-bacnet-stack-examples/docs/profile-table.md - do not edit here) -->
There is one example repository per standardized device profile in ASHRAE 135-2024 Annex L. An example marked ⛔ is blocked: the stack cannot yet perform that profile's function through its customer interface, and the example's README says what it does today. Pick the profile your device claims, then the language you build in. "Ask" means the example hasn't been built yet for that language - [contact Chipkin](https://store.chipkin.com/contact-us) if you need one.

### Controllers (Annex L.4)

| Profile | C++ | Node.js | C# | Rust | Python | Go |
|---|---|---|---|---|---|---|
| **B-SS** Smart Sensor | [B-SS-CPP](https://github.com/chipkin/BACnetProfileExample-B-SS-CPP) | [B-SS-Node](https://github.com/chipkin/BACnetProfileExample-B-SS-Node) | [B-SS-CS](https://github.com/chipkin/BACnetProfileExample-B-SS-CS) | [B-SS-Rust](https://github.com/chipkin/BACnetProfileExample-B-SS-Rust) | [B-SS-Python](https://github.com/chipkin/BACnetProfileExample-B-SS-Python) | [B-SS-Go](https://github.com/chipkin/BACnetProfileExample-B-SS-Go) |
| **B-SA** Smart Actuator | [B-SA-CPP](https://github.com/chipkin/BACnetProfileExample-B-SA-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-ASC** Application Specific Controller | [B-ASC-CPP](https://github.com/chipkin/BACnetProfileExample-B-ASC-CPP) | [B-ASC-Node](https://github.com/chipkin/BACnetProfileExample-B-ASC-Node) | Ask | Ask | Ask | Ask |
| **B-AAC** Advanced Application Controller | [B-AAC-CPP](https://github.com/chipkin/BACnetProfileExample-B-AAC-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-BC** Building Controller | [B-BC-CPP](https://github.com/chipkin/BACnetProfileExample-B-BC-CPP) | Ask | Ask | Ask | Ask | Ask |

### Life safety controllers (Annex L.5)

| Profile | C++ | Node.js | C# | Rust | Python | Go |
|---|---|---|---|---|---|---|
| **B-LSC** Life Safety Controller | [B-LSC-CPP](https://github.com/chipkin/BACnetProfileExample-B-LSC-CPP) 🚧 | Ask | Ask | Ask | Ask | Ask |
| **B-ALSC** Advanced Life Safety Controller | [B-ALSC-CPP](https://github.com/chipkin/BACnetProfileExample-B-ALSC-CPP) | Ask | Ask | Ask | Ask | Ask |

### Access control controllers (Annex L.6)

| Profile | C++ | Node.js | C# | Rust | Python | Go |
|---|---|---|---|---|---|---|
| **B-ACC** Access Control Controller | [B-ACC-CPP](https://github.com/chipkin/BACnetProfileExample-B-ACC-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-AACC** Advanced Access Control Controller | [B-AACC-CPP](https://github.com/chipkin/BACnetProfileExample-B-AACC-CPP) | Ask | Ask | Ask | Ask | Ask |

### Lighting controllers (Annex L.11)

| Profile | C++ | Node.js | C# | Rust | Python | Go |
|---|---|---|---|---|---|---|
| **B-LD** Lighting Device | [B-LD-CPP](https://github.com/chipkin/BACnetProfileExample-B-LD-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-LS** Lighting Supervisor | [B-LS-CPP](https://github.com/chipkin/BACnetProfileExample-B-LS-CPP) | Ask | Ask | Ask | Ask | Ask |

### Elevator controllers (Annex L.13)

| Profile | C++ | Node.js | C# | Rust | Python | Go |
|---|---|---|---|---|---|---|
| **B-EM** Elevator Monitor | [B-EM-CPP](https://github.com/chipkin/BACnetProfileExample-B-EM-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-EC** Elevator Controller | [B-EC-CPP](https://github.com/chipkin/BACnetProfileExample-B-EC-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-AEC** Advanced Elevator Controller | [B-AEC-CPP](https://github.com/chipkin/BACnetProfileExample-B-AEC-CPP) | Ask | Ask | Ask | Ask | Ask |

### Authentication and authorization (Annex L.14)

| Profile | C++ | Node.js | C# | Rust | Python | Go |
|---|---|---|---|---|---|---|
| **B-AS** Authorization Server | [B-AS-CPP](https://github.com/chipkin/BACnetProfileExample-B-AS-CPP) ⛔ blocked on [stack #2043](https://github.com/chipkin/cas-bacnet-stack/issues/2043) | Ask | Ask | Ask | Ask | Ask |

### Miscellaneous (Annex L.7, combinable with any one family)

| Profile | C++ | Node.js | C# | Rust | Python | Go |
|---|---|---|---|---|---|---|
| **B-BBMD** Broadcast Management Device | [B-BBMD-CPP](https://github.com/chipkin/BACnetProfileExample-B-BBMD-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-ACDC** Access Control Door Controller | [B-ACDC-CPP](https://github.com/chipkin/BACnetProfileExample-B-ACDC-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-ACCR** Access Control Credential Reader | [B-ACCR-CPP](https://github.com/chipkin/BACnetProfileExample-B-ACCR-CPP) ⛔ blocked on [stack #3934](https://github.com/chipkin/cas-bacnet-stack/issues/3934) | Ask | Ask | Ask | Ask | Ask |
| **B-RTR** Router | [B-RTR-CPP](https://github.com/chipkin/BACnetProfileExample-B-RTR-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-GW** Gateway | [B-GW-CPP](https://github.com/chipkin/BACnetProfileExample-B-GW-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-DAP** Device Address Proxy | [B-DAP-CPP](https://github.com/chipkin/BACnetProfileExample-B-DAP-CPP) ⛔ blocked on [stack #2032](https://github.com/chipkin/cas-bacnet-stack/issues/2032) | Ask | Ask | Ask | Ask | Ask |
| **B-SCHUB** BACnet/SC Hub | [B-SCHUB-CPP](https://github.com/chipkin/BACnetProfileExample-B-SCHUB-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-GENERAL** General device (Annex L.8) | *(satisfied by every example above)* | — | — | — | — | — |

### Operator interfaces and workstations (Annex L.1–L.3, L.9–L.10, L.12)

Client-side profiles.

| Profile | C++ | Node.js | C# | Rust | Python | Go |
|---|---|---|---|---|---|---|
| **B-OD** Operator Display | [B-OD-CPP](https://github.com/chipkin/BACnetProfileExample-B-OD-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-OWS** Operator Workstation | planned | — | — | — | — | — |
| **B-AWS** Advanced Operator Workstation | planned | — | — | — | — | — |
| **B-XAWS** Extended Advanced Operator Workstation | planned | — | — | — | — | — |
| **B-LSAP** Life Safety Annunciator Panel | planned | — | — | — | — | — |
| **B-LSWS** Life Safety Workstation | planned | — | — | — | — | — |
| **B-ALSWS** Advanced Life Safety Workstation | planned | — | — | — | — | — |
| **B-ACSD** Access Control Security Display | planned | — | — | — | — | — |
| **B-ACWS** Access Control Workstation | planned | — | — | — | — | — |
| **B-AACWS** Advanced Access Control Workstation | planned | — | — | — | — | — |
| **B-LOD** Lighting Operator Display | planned | — | — | — | — | — |
| **B-ALWS** Advanced Lighting Workstation | planned | — | — | — | — | — |
| **B-LCS** Lighting Control Station | planned | — | — | — | — | — |
| **B-ALCS** Advanced Lighting Control Station | planned | — | — | — | — | — |
| **B-ED** Elevator Display | planned | — | — | — | — | — |
| **B-EWS** Elevator Workstation | planned | — | — | — | — | — |
| **B-AEWS** Advanced Elevator Workstation | planned | — | — | — | — | — |

🚧 = in progress. ⛔ = Blocked Example (blocked on the named stack gap). "Ask" = not yet built for that language; contact Chipkin if you need it. Profile definitions: ANSI/ASHRAE 135-2024 Annex L. BIBB definitions: Annex K. Get the stack: <https://store.chipkin.com/services/stacks/bacnet-stack>.
<!-- PROFILE-TABLE:END -->

## References

- **ANSI/ASHRAE Standard 135** (BACnet) - the protocol standard. Object model
  (Clause 12), services (Clause 16 - DeviceCommunicationControl is 16.1),
  BACnet/IP (Annex J), device profiles (Annex L). Purchase / preview via the
  [ASHRAE store](https://www.ashrae.org/technical-resources/standards-and-guidelines).
- **What is BACnet?** - Chipkin's introduction:
  <https://docs.chipkin.com/protocols/bacnet/>.
- **CAS BACnet Stack** - product page and documentation:
  <https://store.chipkin.com/services/stacks/bacnet-stack>.
- **CAS BACnet Explorer** - client for testing this device:
  <https://store.chipkin.com/products/tools/cas-bacnet-explorer>.
- **Shared helper used by this example** - [`common/README.md`](common/README.md).

See also [TUTORIAL.md](TUTORIAL.md), [docs/PICS.md](docs/PICS.md),
[CHANGELOG.md](CHANGELOG.md), and [AGENTS.md](AGENTS.md).
