# B-ASC Wire Tests

Tests that drive the running application specific controller over BACnet/IP from outside it. A client that discovers a B-ASC reads everything it lists, so the first test does exactly that.
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
47821) is the UDP port the test starts the example on. It takes a few seconds.
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

## What it does not test

Discovery is not this example's Profile Function. Being modified by another device and answering communication control are: no Wire Test yet commands an output, or sends DeviceCommunicationControl (enable, disable-initiation, the deprecated disable, a wrong password with --dcc-password). The example initiates nothing after its start-up I-Am, so a test cannot yet show disable-initiation stopping anything (README "DeviceCommunicationControl"). Those tests come with the Profile-functional rework.
