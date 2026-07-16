# BACnet B-ASC (Application Specific Controller) - C++ example

A minimal, copy-paste-friendly example showing how to implement the BACnet
**B-ASC (BACnet Application Specific Controller)** device profile in C++ using the
[CAS BACnet Stack](https://store.chipkin.com/services/stacks/bacnet-stack).
It listens on **BACnet/IP (UDP 47808)**, answers **ReadProperty**, accepts
**WriteProperty** to its commandable outputs, responds to
**DeviceCommunicationControl**, and is discoverable via **Who-Is / I-Am**.

Part of the CAS BACnet Stack **BACnet profile example series** - one repository
per BACnet device profile. This example claims **only** B-ASC.

Reading order: [B-SS (Smart Sensor)](https://github.com/chipkin/BACnetProfileExample-B-SS-CPP) is the **first** example and the one to
start with, then [B-SA (Smart Actuator)](https://github.com/chipkin/BACnetProfileExample-B-SA-CPP); this is the **third**.

> **Versions:** this document describes **example v1.1.0**, built and verified
> against **CAS BACnet Stack 6.0.0.0** at **Protocol_Revision 24**, with the
> vendored `common/` helper at **v1.2.0**. Running the example prints all three.

## Quickstart

You need a CAS BACnet Stack licence and access to its private submodule (see
[Requires the CAS BACnet Stack](#requires-the-cas-bacnet-stack-licensed-product)).
Then:

```bash
git clone --recursive https://github.com/chipkin/BACnetProfileExample-B-ASC-CPP.git
cd BACnetProfileExample-B-ASC-CPP
cmake -B build -S .
cmake --build build --config Release
./build/Release/BACnetExampleBASC.exe        # Windows; drop Release/ on Linux
```

The device announces itself, answers Who-Is, and prints `Press 'h' for help`.
The first build compiles the whole stack (~460 files) and takes a few minutes.

> **You will see a wall of red `Error:` lines at start-up. The device is fine** —
> it hears its own broadcast I-Am and the stack logs a benign decode cascade. See
> [Troubleshooting](#troubleshooting).

The rest of this document explains *what a B-ASC is* and *why the code is shaped
the way it is*. If you just want it running, you are already done.

This is the third example in the series. It builds directly on the
[B-SA (Smart Actuator)](https://github.com/chipkin/BACnetProfileExample-B-SA-CPP)
example: same objects (three read-only inputs + three commandable outputs), plus
one device-management capability - it answers **DeviceCommunicationControl**, so a
management station can quiet or resume the device.

## What is a B-ASC (BACnet Application Specific Controller) profile?

A **device profile** is a standard "template" defined in Annex L of ANSI/ASHRAE
135. It lists the capabilities a class of device must support so that any
compliant client knows what to expect, and the BACnet Testing Laboratories (BTL)
certify devices against it. (New to BACnet in general? See Chipkin's
[What is BACnet?](https://docs.chipkin.com/protocols/bacnet/) guide.)

**B-ASC (BACnet Application Specific Controller)** is a controller with limited
resources, intended for a specific application. Compared to a Smart Actuator, it
adds the requirement to respond to communication-control messages.

**What the profile requires:**

- **Data Sharing - ReadProperty - B side (DS-RP-B):** answer **ReadProperty**.
- **Data Sharing - WriteProperty - B side (DS-WP-B):** accept **WriteProperty** so
  a controller can drive its outputs.
- **Device Management - DeviceCommunicationControl - B side (DM-DCC-B):** respond
  to **DeviceCommunicationControl** - a management station can tell the device to
  stop or resume communicating (optionally for a time period, optionally behind a
  password). This is what distinguishes a B-ASC from a B-SA.
- **Discovery:** the device must be findable, so it answers **Who-Is** with
  **I-Am**, and announces itself with an unsolicited I-Am at start-up.

**What the profile does NOT require** - and this example therefore omits on
purpose: **alarming / event reporting**, **scheduling**, and **trending**.

**But it is still a full BACnet device.** Even a simple profile must present the
standard object model - a **Device** object, a **Network Port** object (every
device needs one), and its objects - and each object must expose all of its
**required properties**. The CAS BACnet Stack generates most of those
automatically (Object_Identifier, Object_Type, Status_Flags, Event_State,
Object_List, Protocol_*, ...); this example supplies the handful that are
application-specific. The result is conformant for **Protocol_Revision 24**.

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

> **Protocol_Revision >= 20 note:** the plain **`disable`** value (stop initiating
> *and* responding) is **deprecated**. At Protocol_Revision 24 the stack rejects it
> with `service-request-denied`; the modern choice is **`disable-initiation`** (the
> device keeps answering reads but stops initiating). So in practice only
> `enable` and `disable-initiation` take effect - the example demonstrates exactly
> this.

The example ships with **no password** (`DCC_PASSWORD = ""`, accept any request).
Set it to your device's secret to require one; a mismatch is rejected with
`password-failure`.

## The device this example creates

```
Device 389003  "Rainbow"   (Vendor 389 - Chipkin Automation Systems)
    │
    ├── Analog Input  1       "Bronze"      Present_Value  21.5    (REAL, degrees Celsius; read-only)
    ├── Binary Input  1       "Emerald"     Present_Value  inactive  (0 = inactive / 1 = active; read-only)
    ├── Multi-State Input 1   "Hot Pink"    Present_Value  1       (state, 1..3; read-only)
    ├── Analog Output 1       "Chartreuse"  Present_Value  20.0    (REAL setpoint; WRITABLE, commandable)
    ├── Binary Output 1       "Fuchsia"     Present_Value  inactive(0/1; WRITABLE, commandable)
    ├── Multi-State Output 1  "Indigo"      Present_Value  1       (state, 1..3; WRITABLE, commandable)
    └── Network Port 1        "Vermilion"   the BACnet/IP port     (required on every device)
```

The three **input** objects (Bronze, Emerald, Hot Pink) are the shared minimum
every example in this series carries; the three **output** objects (Chartreuse,
Fuchsia, Indigo) are commandable via a `Priority_Array`. Object names follow this
series' colour-naming convention (Device is always "Rainbow").

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
| Device | 389003 | Rainbow | - |
| Analog Input | 1 | Bronze | read-only |
| Binary Input | 1 | Emerald | read-only |
| Multi-State Input | 1 | Hot Pink | read-only |
| Analog Output | 1 | Chartreuse | writable (commandable) |
| Binary Output | 1 | Fuchsia | writable (commandable) |
| Multi-State Output | 1 | Indigo | writable (commandable) |
| Network Port | 1 | Vermilion | - |

## Before you ship

This example is a tutorial, and it identifies itself as one. Everything in this
table is read by clients and shown to the operator in **every discovery tool on
the network**. Left as-is, your product appears on a real site announcing itself
as a Chipkin demo. None of it is cosmetic.

| Constant (`main.cpp`) | Ships as | Change it to |
|---|---|---|
| `VENDOR_IDENTIFIER` | `389` (Chipkin) | **Your** company's vendor ID. Assigned by ASHRAE, free: <https://bacnet.org/assigned-vendor-ids/> |
| `VENDOR_NAME` | `Chipkin Automation Systems` | Your company name — must match the vendor ID above. |
| `DEVICE_NAME` | `"Rainbow"` | Your device's `Object_Name`. **Must be unique across the BACnet internetwork** — see the note below. |
| `MODEL_NAME` | `CAS BACnet Stack Example - B-ASC` | Your model designation. This is what a building operator reads to identify your device. |
| `DEVICE_DESCRIPTION` | a description of *this example* | What your device actually is. |
| `FIRMWARE_REVISION` / `APPLICATION_SOFTWARE_VERSION` | `1.0.0` | Your real versions — wire them to your build. |
| `DCC_PASSWORD` | `""` (no password) | Set your device's secret, or leave empty to accept any DeviceCommunicationControl. It crosses the wire in **plaintext** — it is a guard against accidents, not a security boundary. |
| Device instance | `389003` (`--deviceID` overrides) | Must be unique on the internetwork. BACnet requires this to be configurable; keep it so. |

> **`Object_Name` uniqueness is the one that will bite you.** The device instance
> is runtime-configurable via `--deviceID`, but `DEVICE_NAME` is a compile-time
> constant. Ship two units and configure their instances correctly, and **both
> still announce `Object_Name "Rainbow"`** — a spec violation, and exactly the
> uniqueness problem the code comments warn about. In a real product,
> `Object_Name` must be per-unit configurable too (serial number, DIP switches,
> a config file, or a `--deviceName` argument).

`main.cpp` marks this block with a `CHANGE ALL OF THIS BEFORE YOU SHIP` banner.

## Requires the CAS BACnet Stack (licensed product)

This example **builds against the CAS BACnet Stack, which is a commercial Chipkin
product** - it is not free or open source, and there is no public/trial build.
The stack is referenced here as the **private** git submodule
`submodules/cas-bacnet-stack`; you can only fetch and build it once you have a CAS
BACnet Stack license and access to that repository.

**To get the CAS BACnet Stack (and access to build this example), contact
Chipkin:** <https://store.chipkin.com/services/stacks/bacnet-stack> or
sales@chipkin.com.

You do not need a stack licence to *read* this example. Every file outside
submodules/ is CC0 public domain, so once you have access to this repository you
can review the approach and the amount of code involved before you buy. The licence
is what lets you *build* it - that is the part the stack submodule gates.

## What's in this repository

This is a **self-contained** project. It ships:

- `main.cpp` - the example device.
- `common/` - the shared helper (UDP, callbacks, CLI, keyboard) vendored in.
- `submodules/cas-bacnet-stack/` - the **CAS BACnet Stack as a git submodule**
  (private; requires a license - see above). Compiled from source; no prebuilt
  library or DLL is shipped.

## Footprint & performance

This example statically compiles the **entire** CAS BACnet Stack into one
executable (no external runtime/DLL). Release-build sizes of the whole
application (stack + example):

| Platform | Binary | Size |
|----------|--------|------|
| Windows x64 (MSVC, Release) | `BACnetExampleBASC.exe` | ~2.6 MB |
| Linux x64 (GCC, Release) | `BACnetExampleBASC` | ~6 MB unstripped (`strip` cuts it substantially) |

These are whole-application sizes. The stack's flash/RAM footprint on a
constrained MCU, CPU cost per `BACnetStack_Tick()`, request latency, and the
maximum number of objects depend on your target and configuration. For
embedded-sizing and benchmark figures, contact Chipkin -
<https://store.chipkin.com/services/stacks/bacnet-stack>.

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

## Get the code

Clone this repository **and its submodule** (the CAS BACnet Stack):

```bash
git clone --recursive https://github.com/chipkin/BACnetProfileExample-B-ASC-CPP.git
cd BACnetProfileExample-B-ASC-CPP

# already cloned without --recursive? fetch the submodule:
git submodule update --init --recursive
```

## Build

```bash
cmake -B build -S .
cmake --build build --config Release
```

> **First build takes a few minutes** - it compiles the entire CAS BACnet Stack
> (~460 source files) once. Incremental rebuilds after that are fast.

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
BACnet B-ASC (Application Specific Controller) Example - C++ v1.1.0
CAS BACnet Stack version: 6.0.0.0
Common helper (common/) version: 1.2.0
FYI: Listening for BACnet/IP on UDP port 47808.
TX 21 bytes to 192.168.3.255:47808 (broadcast)
FYI: Device 389003 ("Rainbow") ready. Vendor ID 389. Press 'h' for help.
```

Those first three lines are worth reading: they tell you the **example** version,
the **stack** version you actually linked, and the version of the vendored
`common/` helper — which is how you tell whether this repo's copy has drifted from
the rest of the series.

The `TX` line is the start-up I-Am the device broadcasts to announce itself. It
goes to the **local subnet broadcast** address (here `192.168.3.255`, computed
from the Network Port's interface), not the global `255.255.255.255`. As clients
talk to the device you'll see `RX`/`TX` lines; a WriteProperty to an output prints
a line such as `WriteProperty: Analog Output 1 (Chartreuse) <- 42.50 @ priority 8`,
and a DeviceCommunicationControl prints e.g. `DeviceCommunicationControl:
disable-initiation (keep responding) (indefinitely)`.

The device listens on UDP **47808** (BACnet/IP). Allow that port through your
firewall. To use a different port, pass `--port` (see below).

### Command-line options

| Option | Default | Meaning |
|--------|---------|---------|
| `--port <n>` | `47808` | UDP port to listen on (BACnet/IP). |
| `--deviceID <n>` | `389003` | The device's BACnet instance number (BACnet requires this to be configurable). |
| `--help`, `-h` | - | Show usage and exit. |
| `--version` | - | Print the example, stack, and `common/` helper versions, then exit. |

### Interactive commands

While the example runs, these keys are available (shared across all examples in
the series):

| Key | Action |
|-----|--------|
| `h` | Show the version information and this command list. |
| `q` | Quit. |
| up arrow | Increase Analog Input 1 (`Bronze`) by 1.1. |
| down arrow | Decrease Analog Input 1 (`Bronze`) by 1.1. |

## Verify

Use a BACnet client such as the
[**CAS BACnet Explorer**](https://store.chipkin.com/products/tools/cas-bacnet-explorer):

1. **Discover** - send a **Who-Is**. The device replies with **I-Am** from
   instance **389003** (vendor **389**). It also broadcasts an I-Am at start-up.
2. **Browse the object model** - the device shows seven objects: the Device
   (`Rainbow`), three inputs, three outputs, and the Network Port (`Vermilion`).
3. **Read the Device** - ReadProperty `389003` -> `Object_Name` = `"Rainbow"`;
   `Protocol_Revision` = `24`; `Description` = the profile description string.
4. **Command an output** - WriteProperty Analog Output `1` `Present_Value` = `42.5`
   at priority `8`; re-read `Present_Value` (`42.5`) and `Priority_Array[8]`
   (`42.5`); write `NULL` at priority `8` to relinquish; `Present_Value` returns to
   `20.0` (its `Relinquish_Default`). Repeat for Binary/Multi-State Output. A write
   to a read-only *input*, or an out-of-range value, is rejected.
5. **Communication control (the B-ASC test)** - send a **DeviceCommunicationControl**
   with `disable-initiation`: the device SimpleACKs and keeps answering reads but
   stops initiating. Send `enable` to resume. (Sending the deprecated plain
   `disable` returns `service-request-denied` at Protocol_Revision 24 - that is
   correct.) If you set `DCC_PASSWORD`, a request with the wrong password is
   rejected with `password-failure`.

## Troubleshooting

| Symptom | Cause / fix |
|---------|-------------|
| On start-up the app prints a wall of red `Error:` lines but the device works | **Expected — this is not your bug.** Two benign sources, both from the stack's own debug logging: (1) the device receives its **own** broadcast I-Am and logs a decode cascade (*"Services is not supported service=[0]"* … *"Failed to process the incoming NPDU"*) — any BACnet/IP device that listens for broadcasts hears itself; (2) a one-time *"UUID has not been set. A UUID must be set for the BACnetSC device to start."* — the stack starts a BACnet/SC datalink these IP-only examples never configure. It appears once and does not spam. On a healthy start-up roughly half the output is these lines. |
| CMake error: *"CAS BACnet Stack source not found"* | Submodules not initialized. Run `git submodule update --init --recursive` (or pass `-D CAS_STACK_DIR=...`). |
| `CASBACnetStackDLL.h: No such file or directory` | Same - submodules not checked out. |
| Windows: *"No CMAKE_CXX_COMPILER could be found"* | Install Visual Studio with the "Desktop development with C++" workload, then re-run from a fresh terminal. |
| First build seems stuck for minutes | Normal - it's compiling ~460 stack files. Only the first build is slow. |
| `git submodule update` fails with *Permission denied* / *repository not found* | The CAS BACnet Stack submodule is a **private** repo. You need a stack licence and access granted to your GitHub account, plus working SSH keys or a credential helper. See [Requires the CAS BACnet Stack](#requires-the-cas-bacnet-stack-licensed-product). |
| App prints *"Failed to bind UDP port 47808"* | Another BACnet program is already using 47808. Stop it, or run with `--port <n>`. |
| DeviceCommunicationControl `disable` returns an error | Expected. The plain `disable` value is deprecated at Protocol_Revision >= 20; use `disable-initiation` instead. |
| WriteProperty to an output is rejected | Write to the **output** objects, not the inputs (inputs are read-only sensors), and keep the value in range. |
| Client sends Who-Is but sees no I-Am | Firewall is blocking UDP 47808, or the client and device are on different subnets. Allow the port; test on the same subnet first. |
| Replies show an unexpected device instance or vendor | Another BACnet device is already running on this host/port (the socket uses `SO_REUSEADDR`). Stop the other device, or run this example on its own machine/IP. |

## Extending the example

The example is intentionally small so it's easy to change.

**Require a password for DeviceCommunicationControl** - set `DCC_PASSWORD` in
`main.cpp` to a non-empty string; the callback then rejects mismatches with
`password-failure`.

**Add a second analog input.** Read this whole recipe before starting — the step
that is easiest to miss is the one BTL will fail you for, and it fails SILENTLY.

> **Why skipping a step is silent.** Most of the `GetProperty*` callbacks match
> on **both** object type *and* instance (`objectInstance ==
> ANALOG_INPUT_INSTANCE`), so a new instance falls through every one of them.
> `GetPropertyBool` is the exception: it matches on type only, so
> `Out_Of_Service` works for a new instance for free.
>
> Falling through a callback does **not** reliably produce an error. The stack
> errors only for the few properties it refuses to invent — `Present_Value`,
> `Number_Of_States`, `Relinquish_Default`, `Local_Date`, `Local_Time`, and a
> Network Port's `APDU_Length`.
> For everything else it **silently substitutes a default**:
>
> | Property | If you forget to serve it | Loud? |
> |---|---|:--:|
> | `Present_Value` | Error (`value-not-initialized`) | yes |
> | `Object_Name` | reads back as the string **`"undefined"`** | **no** |
> | `Units` | reads back as **`no-units` (95)** | **no** |
>
>
> It is worse than "wrong value": the object's `Property_List` **still advertises
> `Units` (117)**. So the object actively claims to have the property, and then
> answers with a default. Nothing on the wire says you forgot anything.
>
> So a half-added object looks **healthy**. Add two and both report
> `Object_Name "undefined"` — duplicate object names inside one device, a spec
> violation and a hard BTL failure that every scan tool renders as fine.
> **"It scanned OK" is the failure mode, not evidence against it.**

```cpp
// 1) a new instance number (in section 1).
//    Naming: a second object of a type is "<Colour> 2" - so Analog Input 2 is
//    "Bronze 2", NOT a new colour. Each object TYPE owns one colour series-wide.
static const uint32_t ANALOG_INPUT_2_INSTANCE = 2;   // "Bronze 2"
static float g_analogInput2Value = 23.1f;            // its live value

// 2) add the object (in main, next to the other BACnetStack_AddObject calls).
//    Check the return, like every other stack call in this file.
if (!BACnetStack_AddObject(g_deviceInstance, OBJECT_TYPE_ANALOG_INPUT, ANALOG_INPUT_2_INSTANCE)) {
    printf("Error: Failed to add Analog Input 2 (Bronze 2).\n");
    return 1;
}

// 3) serve its Present_Value + Object_Name:
//    GetPropertyReal:        AI/2 + Present_Value -> *value = g_analogInput2Value;
//    GetPropertyCharString:  AI/2 + Object_Name   -> "Bronze 2"

// 4) DO NOT SKIP: serve its Units, in GetPropertyEnumerated.
//    Units is REQUIRED on an Analog Input. The existing check reads
//    objectInstance == ANALOG_INPUT_INSTANCE, which is instance 1 - so without
//    this, Analog Input 2's Units silently reads back no-units and the object is
//    NON-CONFORMANT while looking perfectly healthy.
//    GetPropertyEnumerated:  AI/2 + Units -> *value = ENGINEERING_UNITS_DEGREES_CELSIUS;
```

Then read back every required property of Analog Input 2 and **diff it against
Analog Input 1**. Anything returning `"undefined"`, `no-units`, or `0` where
object 1 returns something real is a step you missed.

### What each object type needs you to serve

| Object type | You must serve | Plus |
|---|---|---|
| Analog Input | `Present_Value` (Real), `Object_Name`, `Units` | — |
| Binary Input | `Present_Value` (Enumerated), `Object_Name` | `Polarity` |
| Multi-State Input | `Present_Value` (Unsigned), `Object_Name` | `Number_Of_States` |
| Analog Output | `Object_Name`, `Units`, + the `Commandable` slots | `Priority_Array`, `Relinquish_Default` |
| Binary Output | `Object_Name`, + the `Commandable` slots | `Polarity`, `Priority_Array`, `Relinquish_Default` |
| Multi-State Output | `Object_Name`, + the `Commandable` slots | `Number_Of_States`, `Priority_Array`, `Relinquish_Default` |

An **output**'s `Present_Value` is *not* served directly — the stack computes it
from the `Priority_Array` slots your `GetPropertyBool`/typed getters return
(see the `Commandable` struct). Add a new output instance to the `outputs[]`
table in `main` and to `GetCommandable()`, or it will not be commandable.

### Who serves what: the application or the stack?

For Analog Input 1, the whole picture:

| Property | Served by | How |
|---|---|---|
| `Object_Identifier` | **stack** | generated from the object you added |
| `Object_Type` | **stack** | generated |
| `Object_List` | **stack** | generated (Device object) |
| `Property_List` | **stack** | generated |
| `Status_Flags` | **stack** | generated |
| `Event_State` | **stack**, sort of | no intrinsic alarming here, so nothing serves it — it reads `normal` only because `normal` is the enumeration's zero value and the stack substitutes a datatype default. Correct by coincidence, not design. |
| `Out_Of_Service` | **you** | `GetPropertyBool` — matched on object **type only** |
| `Present_Value` | **you** | `GetPropertyReal` |
| `Object_Name` | **you** | `GetPropertyCharString` |
| `Units` | **you** | `GetPropertyEnumerated` |

Going beyond this (COV, alarms, scheduling) means implementing a richer profile -
a later example in this series.

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
- **B-SA (Smart Actuator) example** - the sibling this builds on:
  <https://github.com/chipkin/BACnetProfileExample-B-SA-CPP>.
- **Shared helper used by this example** - [`common/README.md`](common/README.md).

## Use this in your own project

This repository is self-contained: clone it (with the submodule) and build, then
copy what you need into your product. The example source code is dedicated to the
public domain under [CC0-1.0](LICENSE) - use it for anything, no attribution
required. The CAS BACnet Stack is a separate, commercially licensed product and
is not covered by CC0.

See also [CHANGELOG.md](CHANGELOG.md) and [AGENTS.md](AGENTS.md).
