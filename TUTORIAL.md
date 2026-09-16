# Tutorial - extending and reviewing the B-ASC example

[README.md](README.md) says what this example *is*. This document is the *how*:
how to extend it into your own device, what each object type needs the
application to serve, who serves what for a representative object, how to
review the result for conformance, and what goes wrong when you get it subtly
right.

Read this once before you start changing `main.cpp`. The most expensive mistake
in this example is silent, and the section it lives in is
[Add a second analog input](#add-a-second-analog-input).

- [Extending the example](#extending-the-example)
- [Add a second analog input](#add-a-second-analog-input)
- [What each object type needs you to serve](#what-each-object-type-needs-you-to-serve)
- [Who serves what: the application or the stack?](#who-serves-what-the-application-or-the-stack)
- [Reviewing your device](#reviewing-your-device)
- [Using this example as the base for a real product](#using-this-example-as-the-base-for-a-real-product)
- [Troubleshooting](#troubleshooting)

## Extending the example

The example is intentionally small so it's easy to change.

**Change a sensor's value or name** - edit the constants / callbacks in
`main.cpp` (e.g. the initial value of `g_analogInput1Value`, or the `"Bronze"`
string in `GetPropertyCharString`).

**Require a password for DeviceCommunicationControl** - set `DCC_PASSWORD` in
`main.cpp` to a non-empty string; the `DeviceCommunicationControl` callback
then rejects a mismatch with `password-failure`. The comparison is by length
first, then bytes - never `strcmp`, because a BACnet CharacterString may
legitimately contain an embedded NUL that `strcmp` would silently stop at. Do
not treat the password as a security boundary: it crosses the wire in
plaintext and is a guard against accidents, not an attacker.

**Change the device identity before you ship** - vendor ID, vendor name, model
name, description, firmware revision, device name and the DCC password are all
in the `CHANGE ALL OF THIS BEFORE YOU SHIP` block at the top of `main.cpp`,
with a per-field note on each saying what to change it to. That block is the
authoritative checklist; it is in the source rather than here so it cannot be
skipped by someone who only reads the code.

### Add a second analog input

Read this whole recipe before starting — the last step is the one that is easy
to miss and the one BTL will fail you for.

> **Why there are four edits, not three — and why skipping one is SILENT.**
> Most of the `GetProperty*` callbacks match on **both** object type *and*
> instance (`objectInstance == ANALOG_INPUT_INSTANCE`), so a new instance falls
> through every one of them. `GetPropertyBool` is the exception: it matches on
> type only, so `Out_Of_Service` works for a new instance for free.
>
> Here is the part that matters, and it is the opposite of what most people
> assume: falling through a callback does **not** reliably produce an
> error. The stack errors only for the few properties it refuses to invent —
> `Present_Value`, `Number_Of_States`, `Relinquish_Default`, `Local_Date`,
> `Local_Time`, and a Network Port's `APDU_Length`. For everything else it **silently substitutes a default**:
>
> | Property | If you forget to serve it | Loud? |
> |---|---|:--:|
> | `Present_Value` | Error (`read-access-denied`) | yes |
> | `Object_Name` | reads back as the string **`"undefined"`** | **no** |
> | `Units` | reads back as **`no-units` (95)** | **no** |
> | `Out_Of_Service` | served on type alone — works by accident | n/a |
>
> **Doesn't the `errorCode` out-parameter fix this?** Only if you use it, and
> only where it is right to. Each `GetProperty*` callback ends with a
> `uint32_t* errorCode` that the stack presets to `success` and reads only when
> you return `false`, so you *can* turn any decline into a chosen BACnet error.
> But ending every callback with `*errorCode = unknown-property` breaks the
> device: the stack's decline-and-fabricate path is what answers required
> properties an application is not expected to serve — the Device's
> `Max_APDU_Length_Accepted`, `APDU_Timeout` and `Number_Of_APDU_Retries` among
> them. Name an error on the catch-all and those start failing instead of
> answering. Set `errorCode` only where *this device* knows the read is wrong;
> `main.cpp` does it in exactly two places: `State_Text` with an out-of-range
> array index, and `DeviceCommunicationControl` (see
> [Who serves what](#who-serves-what-the-application-or-the-stack) below — that
> callback has no fallback and must set `*errorCode` on every `false` return).
> The table above is still how the fall-through behaves for `GetProperty*`, and
> the diff below is still what catches a missed step.
>
> It is worse than "wrong value": the object's `Property_List` **still advertises
> `Units` (117)**. So the object actively claims to have the property, and then
> answers with a default. Nothing on the wire says you forgot anything.
>
> So a half-added object does not look broken; it looks **healthy**. Add two of
> them and both report `Object_Name "undefined"` — duplicate object names inside
> one device, which is a spec violation and a hard BTL failure that every scan
> tool will render as a perfectly good object. **"It scanned OK" is exactly the
> failure mode, not evidence against it.**

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
//    Units is a REQUIRED property of an Analog Input. The existing check reads
//    `objectInstance == ANALOG_INPUT_INSTANCE`, which is instance 1 - so without
//    this, reading Analog Input 2's Units returns an ERROR and the object is
//    NON-CONFORMANT. It will still appear in the Object_List and its
//    Present_Value will read back perfectly, so the device looks healthy right
//    up until BTL certification.
//    GetPropertyEnumerated:  AI/2 + Units -> *value = ENGINEERING_UNITS_DEGREES_CELSIUS;
```

Then re-run the README's Verify steps **against Analog Input 2**, not just Analog
Input 1 — read every required property and **diff it against Analog Input 1**.
Any property that comes back `"undefined"`, `no-units`, or `0` where object 1
returns something real is a step you missed. Because the failure is silent (see
the table above), this diff is the only thing that catches it.

The same trap applies to a new **output**: `GetCommandable()` matches on exact
type + instance, so a new output instance falls through it and is silently
*not* commandable until you add it there and to the `outputs[]` table in
`main()`.

## What each object type needs you to serve

The application must serve every REQUIRED property the stack does not generate.
It differs per type — this is the checklist, so you do not have to infer it:

| Object type | You must serve | Plus |
|---|---|---|
| Analog Input | `Present_Value` (Real), `Object_Name`, `Units` | — |
| Binary Input | `Present_Value` (Enumerated), `Object_Name` | `Polarity` |
| Multi-State Input | `Present_Value` (Unsigned), `Object_Name` | `Number_Of_States` |
| Analog Output | `Object_Name`, `Units`, `Relinquish_Default` | commandable slots (`Priority_Array`) |
| Binary Output | `Object_Name`, `Polarity`, `Relinquish_Default` | commandable slots (`Priority_Array`) |
| Multi-State Output | `Object_Name`, `Number_Of_States`, `Relinquish_Default` | commandable slots (`Priority_Array`) |

An output's `Present_Value` is **not** served directly by a `GetProperty*`
callback - the stack computes it from the `Priority_Array` slots your typed
getters (`GetPropertyReal`/`GetPropertyEnumerated`/`GetPropertyUnsignedInteger`)
and `GetPropertyBool` (which slot is null) return. See the `Commandable` struct
and `GetCommandable()` in `main.cpp`.

## Who serves what: the application or the stack?

The single most common question when reading this file is "who answers this
property?" For Analog Input 1, the whole picture:

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

For Analog Output 1 ("Chartreuse"), the commandable object, the picture is
different - the stack, not the app, resolves `Present_Value`:

| Property | Served by | How |
|---|---|---|
| `Present_Value` | **stack** | computed from the highest-priority non-null `Priority_Array` slot, or `Relinquish_Default` if every slot is null |
| `Priority_Array` | **you**, per slot | `GetPropertyReal` (the slot's value) + `GetPropertyBool` (whether the slot is null) |
| `Relinquish_Default` | **you** | `GetPropertyReal` |
| `Current_Command_Priority` | **stack** | computed |
| `Units` | **you** | `GetPropertyEnumerated` |

And for `DeviceCommunicationControl` (not a property, but the callback this
profile adds): the stack owns the actual enable/disable state machine and the
optional re-enable timer. The `DeviceCommunicationControl` callback in
`main.cpp` only validates the password and logs what was asked - it does not
implement the communication gating itself. See the README's
[DeviceCommunicationControl section](README.md#devicecommunicationcontrol-the-b-asc-addition)
for the deprecated-`disable` rejection and the `*errorCode` contract, which is
stricter here than anywhere else in this file: unlike the `SetProperty*`
callbacks (which fall back to `writeAccessDenied`), this callback has **no**
default and must set `*errorCode` on every `false` return, or the wire carries
the nonsensical `Error Code = success(84)`.

Every object, not just these, is in [docs/PICS.md](docs/PICS.md).

Going beyond this (COV, alarms, scheduling) means implementing a richer profile
- see the series table in [README.md](README.md).

## Reviewing your device

After you have changed anything, review it against the conformance statement
rather than against "it looked fine in the explorer":

1. Regenerate [docs/PICS.md](docs/PICS.md) after editing `docs/objects.json`
   (see [Keeping the PICS honest](#keeping-the-pics-honest) below). A ⚠ row is a
   required property nothing serves.
2. Read **every** property listed for **every** object with a BACnet client, and
   compare the value against the PICS. `"undefined"`, `no-units` and `0` are the
   three shapes a missed callback takes.
3. Diff a new object of a type against the existing one of that type. Anything
   that differs and shouldn't is a callback that matched on instance.
4. **Command an output** - WriteProperty a commandable output's `Present_Value`
   at a priority, re-read `Present_Value` and `Priority_Array[priority]`, then
   write `NULL` to relinquish and confirm it falls back to
   `Relinquish_Default`. Confirm a write to a read-only *input*, or an
   out-of-range value, is rejected.
5. **Exercise DeviceCommunicationControl** - send `disable-initiation`, confirm
   the device SimpleACKs and keeps answering reads; send `enable` to resume;
   send the deprecated plain `disable` and confirm it is rejected with
   `service-request-denied`; if `DCC_PASSWORD` is set, send a wrong password and
   confirm `password-failure`.

### Keeping the PICS honest

`docs/PICS.md` is partly generated. `docs/objects.json` describes each object and
who serves which property; the series tool regenerates the object tables from it
plus the stack's own `docs/property-profile-reference.md` at the pinned commit:

```bash
python tools/gen-objects-properties.py BACnetProfileExample-B-ASC-CPP            # rewrite
python tools/gen-objects-properties.py BACnetProfileExample-B-ASC-CPP --check    # fail if stale
```

(That tool lives in the example-series repository, not in this one. If you only
have this repository, edit the generated block by hand and keep it matching the
callbacks in `main.cpp`.)

When you add an object or a property to `main.cpp`, update `docs/objects.json`
in the same change and regenerate. The `app` list is what the callbacks serve;
`accepted` is for a required property you deliberately leave to the stack's
default, and each one needs a justification. Anything required, not in `app` and
not in `accepted`, comes out as a ⚠ row - that is a defect, not a feature.

## Using this example as the base for a real product

This repository is self-contained: clone it (with the submodule) and build,
then copy what you need into your product. The example source code is
dedicated to the public domain under [CC0-1.0](LICENSE) - use it for anything,
no attribution required. The CAS BACnet Stack is a separate, commercially
licensed product and is not covered by CC0.

### What to copy, what to rewrite

`common/` is written for a **console demo**, not for a product. Copy it to get started, then
expect to replace these before you ship:

| In `common/` | Why it is not production code | What a product does instead |
|---|---|---|
| `printf` on every RX/TX in the transport callbacks (`CASExampleHelper.cpp`) | Console I/O on the BACnet hot path - slow, and noise once the device is real | Log to your own logger at debug level, or drop it |
| The keyboard loop (`h`/`q`/arrows) | There is no console on an embedded device | Delete it; drive values from your real I/O |
| `GetLocalIPv4()` picking the first non-loopback adapter | A guess; wrong on multi-homed hardware | Bind the interface your product is configured for |
| `SimpleUDP` | Minimal blocking-socket demo | Your platform's networking stack |
| `PrintVersion` / `--help` / `--port` / `--deviceID` | Demo ergonomics | Your own configuration mechanism |

What you *should* keep the shape of: the three transport/time callbacks
(`RegisterCommonCallbacks`), the deferred-restart pattern (`RequestRestart`/`RestartDue`), and
the `LoadBACnetFunctions()` call at the top of `main()`.

### Calling `BACnetStack_Tick()` in a real product

The example calls `Tick()` in a tight loop with a 1 ms sleep. What the stack actually requires:

- **Call it regularly.** Every timer the stack owns - APDU retries/timeouts, COV lifetimes,
  DCC durations, Schedule/Trend evaluation - advances only inside `Tick()`. A gap means late
  or missed BACnet behaviour, not a crash. Every ~10 ms is comfortable; do not let it drift
  into hundreds of milliseconds. This matters more in this example than in B-SS/B-SA: the
  DCC re-enable timer only advances inside `Tick()` too, so a starved loop also delays a
  device coming back out of `disable-initiation` on its own.
- **It is not free-running.** It does the work available and returns; it does not block.
- **Single-threaded contract.** The stack contains **no locking of any kind** (no mutexes, no
  atomics - grep it), and `Tick()` invokes your property callbacks on the calling thread,
  synchronously, before it returns. So: call `Tick()` from exactly one thread, never
  concurrently from two, and do not call any other `BACnetStack_*` function from a different
  thread. If your application is multi-threaded, own the stack from one task and marshal work
  to it (a queue your callbacks read from is the usual shape).
- **Never block inside a callback.** A callback that waits on slow I/O stalls `Tick()`, and
  with it every timer above. Serve cached values and do the slow work elsewhere (`main.cpp`
  says the same at each `GetProperty*` callback).

## Troubleshooting

| Symptom | Cause / fix |
|---------|-------------|
| On start-up the app prints a wall of red `Error:` lines but the device works | **Expected — this is not your bug.** Two benign sources, both from the stack's own debug logging: (1) the device receives its **own** broadcast I-Am and logs a decode cascade (*"Services is not supported service=[0]"* … *"Failed to process the incoming NPDU"*) — any BACnet/IP device that listens for broadcasts hears itself; (2) a one-time *"UUID has not been set. A UUID must be set for the BACnetSC device to start."* — the stack starts a BACnet/SC (BACnet Secure Connect, the TLS/WebSocket-based transport added in ASHRAE 135-2020) datalink these IP-only examples never configure. It appears once and does not spam. How many red lines you see depends on subnet traffic: on a quiet network it can be a single line; on a busy BACnet subnet the self-heard-broadcast decodes pile up into a wall. Either way the device is fine. |
| CMake error: *"CAS BACnet Stack adapter not found under: ..."* | Submodules not initialized. Run `git submodule update --init --recursive` (or pass `-D CAS_STACK_DIR=...`). |
| `CASBACnetStackDLL.h: No such file or directory` | Same - submodules not checked out. |
| Windows: *"No CMAKE_CXX_COMPILER could be found"* | Install Visual Studio with the "Desktop development with C++" workload, then re-run from a fresh terminal. |
| First build seems stuck for minutes | Normal - it's compiling ~600 stack files. Only the first build is slow. |
| App prints *"Failed to bind UDP port 47808"* | Another BACnet program is already using 47808. Stop it, or run with `--port <n>`. |
| The device starts and prints `TX ... (broadcast)`, but no client ever sees it | Check the IP in that `TX` line against the subnet your BACnet client is on. The example picks the **first non-loopback adapter** the OS reports, which on a laptop with Hyper-V, WSL, VirtualBox or a VPN is frequently not your Wi-Fi/Ethernet. There is no `--interface` option; disable the unwanted virtual adapters, or run on a machine without them. (Also check the firewall row above.) |
| Client sends Who-Is but sees no I-Am | Firewall is blocking UDP 47808, or the client and device are on different subnets (Who-Is is a broadcast). Allow the port; test on the same subnet first. |
| DeviceCommunicationControl `disable` returns an error | Expected. The plain `disable` value is deprecated at Protocol_Revision >= 20; use `disable-initiation` instead. |
| WriteProperty to an object is rejected | Write to the **output** objects (Chartreuse, Fuchsia, Indigo), not the inputs (inputs are read-only sensors), and keep the value in range. |
| Replies show an unexpected device instance or vendor | Another BACnet device is already answering on this host/port. On Linux/macOS two processes can share the port and both reply; on Windows the example asks for `SO_EXCLUSIVEADDRUSE` (`common/SimpleUDP.cpp`) so this shows up as a bind failure instead. Stop the other device, or use `--port`. |
