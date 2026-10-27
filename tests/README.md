# B-ASC Wire Tests

Tests that drive the running application specific controller over BACnet/IP
from outside it. A B-ASC's Profile Function is a B-SA's - to be commanded - plus
ANSI/ASHRAE 135-2024 Annex L.4.3's "Ability to respond to communication control
messages". So the tests read everything the device lists, the way a client
discovering it does; command each output and watch it obey the winner; break the
actuator; and silence and un-silence the controller's I-Am heartbeat with
DeviceCommunicationControl.
They are written against the series' shared harness in
[`../wiretest/`](../wiretest/README.md) (vendored, like `common/`); everything
specific to this example is here. Python 3 standard library only - nothing to
`pip install`.

## Running

Build the example (README "Build"), then from the repository root:

```bash
python3 tests/run_wire_tests.py --exe build/BACnetExampleBASC
```

On Windows, `--exe build\Release\BACnetExampleBASC.exe`. It ends with
`ALL WIRE TESTS PASSED` (exit 0) or the scripts that failed. `--port` (default
47827) is the UDP port the test starts the example on. It takes about 4 minutes (`dcc_test.py` waits out a 1-minute DeviceCommunicationControl).
CI (`.github/workflows/release.yml`) runs it on Linux after the smoke test.

## The setup

```
test client (127.0.0.1, ephemeral UDP port)  - the Peer
    |  BACnet/IP, unicast
BACnetExampleBASC            UDP --port   - Device 389003
```

The Peer is a Python BACnet client (`wiretest.Client`), never another example's
binary. It plays a BACnet client such as Chipkin BACnet Explorer.

## `discovery_test.py` - every listed property reads as a value

1. **Who-Is** (for 389003, unicast) -> the device's I-Am.
2. **Device `Object_List`** names exactly the Device, Analog Input 1, Binary Input 1, Multi-state Input 1, Analog Output 1, Binary Output 1, Multi-state Output 1 and Network Port 1. This is the control: a walk
   over nothing would pass.
3. For each object, **`Property_List`** reads, and a ReadProperty of every
   property it lists - plus `Object_Identifier`, `Object_Name`, `Object_Type`
   and `Property_List`, which cl. 12.1.1.4.1 leaves out of the list - returns a
   ComplexACK. An Error, Reject, Abort or no answer prints an `[UNREADABLE]` line
   and fails the check. 135-2024 cl. 12.1.1.4.1: Property_List holds "one
   property identifier for each property that exists within the object".
4. Network Port 1's **`IP_DNS_Server` (406)**, **`FD_BBMD_Address` (418)** and
   **`FD_Subscription_Lifetime` (419)** are each listed and read as a value -
   the three reads Explorer 4.23.2.0 found failing at stack 6.0.21, reported
   against B-SS-CPP (#20, #21, #22). The Network Port object is the stack's, the
   same in every example; this test is copied from B-SS-CPP.
5. Device **`Database_Revision`** reads 8: the stack starts it at 0 and adds one
   for each object added at start-up (the Device and its seven objects), and
   nothing changes the object database afterwards (cl. 12.11; docs/PICS.md).

## `configuration_test.py` - the Device's identity is configurable

BACnet requires the Device's Object_Identifier and Object_Name to be
configurable (135-2024 cl. 12.1.1.3, 12.1.1.4); Object_Name must be unique
across the internetwork, so two units cannot share a compile-time name. The
controller is started three ways, and its help is checked:

1. **No options (control):** Device 389003 answers Who-Is, and its
   `Object_Name` is the default `Chipkin Example B-ASC`.
2. **`--deviceID 389903 --deviceName "Chipkin Example B-ASC Unit 2"`:** the
   device answers Who-Is as 389903; `Object_Name` reads the configured name;
   a read of Device 389003 gets Error OBJECT / UNKNOWN_OBJECT (1/31); the
   ready line names the configured device; a Who-Has by the configured name
   gets an I-Have from Device 389903 with that name (DM-DOB-B).
3. **Boundaries:** an empty name and a 256-byte name each print a warning and
   keep the default; a 255-byte name (the limit) reads back whole.
4. **The command line:** `--help` lists `--port`, `--deviceID`, `--deviceName`,
   `--dcc-password` (a B-ASC executes DeviceCommunicationControl) and `--xml`;
   with `--xml` the console shows each frame as an XML block.

Against the binary from before `--deviceName` (2026-10-23, Windows) it fails 6
of 12 checks (the configured name, the ready line, the Who-Has, both warnings,
the 255-byte name); against the binary before `--xml`, 1 of 18 (no XML).

## `commanding_test.py` and `failure_modes_test.py`

The B-SA example's tests, for device 389003: each output commanded at two
priorities with its feedback input following the winner; a disconnected valve
actuator (`no-output`, FAULT, a command accepted but not obeyed, recovery); and
the refusals (`value-out-of-range` on all three outputs, `write-access-denied` on
an input). See the B-SA-CPP `tests/README.md` for the step-by-step; the
`main.cpp` code they test is the same. `basc_setup.py` holds the numbers.

Requests use a 0.6 s timeout and up to 3 resends (`basc_setup.REQUEST_TIMEOUT` /
`RETRIES`); each resend prints `[RETRY]`, so a lost request is visible.

## `dcc_test.py` - silenced and resumed (the B-ASC Profile Function)

The example is started with `--dcc-password letmein`. What it initiates is its
I-Am heartbeat, every 5 s. The test counts heartbeats two ways: on the wire with
`wiretest.broadcast_listener` (Linux/macOS - Windows cannot share the example's
port), and in the example's console, where `common/` prints a `TX ...
(broadcast) ... I-Am` line for every datagram it really sends and none for one
the stack refused. On Linux both counts must agree with the check.

1. **Control:** at least 2 heartbeats in 11 s.
2. **Refusals** (cl. 16.1.1.3.1): `disable-initiation` with a wrong password and
   with none -> Error SECURITY / PASSWORD_FAILURE (4/26); the deprecated
   `disable` (1) with the right password -> Error SERVICES /
   SERVICE_REQUEST_DENIED (5/29). The heartbeat still runs (at least 2 in 11 s).
3. **`disable-initiation`** (indefinite, right password) -> SimpleACK. A
   ReadProperty is answered, a WriteProperty is acknowledged and obeyed, a
   unicast Who-Is gets its I-Am (cl. 16.1.2 exempts it); then no heartbeat for
   11 s.
4. **`enable`** -> SimpleACK; at least 2 heartbeats in 11 s.
5. **`disable-initiation` for 1 minute** -> SimpleACK; no heartbeat for 50 s;
   then, with nothing more sent, a heartbeat comes back - and not before 59 s
   (K.5.6: "Support for requests of a limited duration is required").

## Each check fails without its feature

Run 2026-10-16 on Windows (STATIC build, relinked each time - the binary's
mtime checked): one feature removed from `main.cpp`, rebuilt, the named script
run, the source restored. Every one is caught:

| # | Feature removed (`main.cpp`) | Script | Fails with |
|---|---|---|---|
| H1 | `HeartbeatTick()` not called | dcc | `Control: the I-Am heartbeat runs - at least 2 in 11 s - 0 in the console`; `... and the heartbeat is back ... - 0`; `... comes back by itself once the minute is up ... - 0` |
| H2 | one heartbeat only, then none | dcc | `Control: the I-Am heartbeat runs - at least 2 in 11 s - 1 in the console`; `... the heartbeat is back ... - 0` |
| P1 | the password not compared | dcc | `DISABLE_INITIATION with a wrong password -> Error SECURITY / PASSWORD_FAILURE - SimpleACK`; `... with no password ... - SimpleACK`; `... after all three refusals the heartbeat still runs - 0` |
| P2 | `--dcc-password` not parsed | dcc | the same three lines as P1 |
| P3 | the callback refuses ENABLE | dcc | `ENABLE with the right password -> SimpleACK - Error class=5 code=45`; `... and the heartbeat is back ... - 0` |
| P4 | the callback refuses DISABLE_INITIATION | dcc | `DISABLE_INITIATION (indefinite) ... -> SimpleACK - Error class=5 code=45`; `... the heartbeat stops: no unsolicited I-Am in 11 s - 2`; `... no unsolicited I-Am for the first 50 s - 10`; `... not before it is up - first heartbeat seen 51 s after the request` |
| A1 | `ActuatorSimulationTick()` not called | commanding, failure_modes | `... the temperature climbs to 24.0 ... - read [21.5, 21.5, ...]`; `... the feedback follows to 1 - read 0` |
| A3 | the LOWEST priority wins | commanding | `... and the temperature stays at 24.0 (the losing command moves nothing) - read 22.0`; `... the feedback follows to 0 - read 1` |
| A7 | the valve never disconnects | failure_modes | `Valve disconnected: Analog Output 1 Reliability reads NO_OUTPUT within 3 s - read 0`; `... the temperature does not follow ... - read 23.0` |
| A11 | the setpoint range not checked | failure_modes | `Analog Output 1 setpoint 35.0 (above Max_Pres_Value) -> Error PROPERTY / VALUE_OUT_OF_RANGE - SimpleACK` |

H1 was also run on Linux (WSL Ubuntu 22.04, SOURCE build), where the wire
witness is live: `Control: the I-Am heartbeat runs - at least 2 in 11 s - 0 in
the console, 0 on the wire` (and the other three heartbeat checks likewise).

The remaining actuator checks are the B-SA example's and are mutation-verified
there (B-SA-CPP `tests/README.md`, A1-A15): `main.cpp` sections 1b and 2b are the
same code. H1 shows why each "silent" check has a running control before it: with
no heartbeat at all, "the heartbeat stops" passes - and the controls fail.

What `dcc_test.py` cannot remove from the example: the suppression itself, the
deprecated-DISABLE refusal and the duration timer are the stack's (cl. 16.1.2 is
implemented in `BACnetPacket::IsRefusedWhenInitiationDisabled`). The test pins
that the stack does them for this device.

