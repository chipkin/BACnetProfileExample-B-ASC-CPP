# VeriBACnet results

This is the latest VeriBACnet run of this folder's project, summarised by hand
from the run's `report.json`. The run's own Results Folder (reports, packet
captures, wire logs) is not published, because it holds the testing machine's
network addresses.

| | |
|---|---|
| Date | 2026-10-27 |
| Example | BACnet B-ASC (Application Specific Controller) Example - C++ v1.5.0 (with the unreleased changes in CHANGELOG.md) |
| CAS BACnet Stack | `6.x` @ `69b6249f` (6.0.23.0) |
| Profile | B-ASC (BACnet Application Specific Controller) |
| Transport | BACnet/IP, UDP port 47827 |
| VeriBACnet | 0.20.0 (its test device uses CAS BACnet Stack 6.0.23.0) |
| Test plan | 65 BTL tests (ANSI/ASHRAE 135.1-2023) selected for the B-ASC profile |
| Result | **46 PASS · 0 FAIL · 0 ERROR · 19 SKIP** |

**Judged BTL-clean on BACnet/IP, with one profile function not yet measured.**
No test failed, and every skipped test has a stated reason. See "What BTL-clean means" in
[README.md](README.md). This is not BTL certification.

**DeviceCommunicationControl password:** the example was started with a
DeviceCommunicationControl password (`--dcc-password`, a test value), and the
project declares the same password, so the two password tests ran: a request
with a wrong password, and one with no password, are refused with SECURITY /
PASSWORD_FAILURE. Both pass. The shipped default is still no
password.

**Measured coverage:** 46 of the 65 selected tests ran; all 46 passed.
- 4 of the 20 skipped tests need an operator, and the run was unattended.
- 11 do not apply to this device: it cannot create or delete objects, its only
  renameable or renumberable object is the Device (changed by restarting it),
  it has no writable non-commandable property, writable fixed-size array or
  optional-functionality property, and, at Protocol_Revision 30, it correctly
  refuses the deprecated DeviceCommunicationControl DISABLE that three tests
  expect to succeed.
- 4 wait on a test-tool limitation (tracked): the four disable-initiation tests below.

**Not yet measured by VeriBACnet: silencing and resuming the device.** The
B-ASC Profile Function is to respond to DeviceCommunicationControl: under
`disable-initiation` the I-Am heartbeat stops, and `enable` or the end of the
time duration resumes it. The four tests that check this skipped: the test
tool listens for something the device initiates, but it cannot yet hear the
heartbeat, which is broadcast to the device's own UDP port (tracked). The
project declares the services the device initiates (I-Am, I-Have, and the
unsolicited I-Am heartbeat). Because the heartbeat is an unsolicited I-Am, the
clause's own skip ("initiates nothing but an I-Am in answer to Who-Is") does
not apply to this device, so the four tests stay as "no trigger". Of the
DeviceCommunicationControl tests, the two password tests and 9.24.1.11 (the
deprecated DISABLE is refused) ran and passed. This example's own Wire Test
`dcc_test.py` covers silencing, resuming, the time duration and the password.

Every other BIBB the example claims had tests that ran: reading properties
(including the 7.1.1 Read Support procedure, against the EPICS), writing and
commanding the outputs (including the 7.2.2 Write Support procedure, and the
wrong-datatype and out-of-range write tests), Who-Is / I-Am and Who-Has /
I-Have. The commanding tests use only Analog Output 1; Binary Output 1 and
Multi-state Output 1 are covered by this example's own Wire Tests.

This run replaces the 2026-10-26 run (65 tests, 44 PASS · 1 FAIL · 20 SKIP,
45 of 65 ran). What changed:
- The test tool now writes a value inside Analog Output 1's range, so 9.22.1.2
  (writing a commandable property without a priority) passes. It failed before
  with a fixed 42.0 against the range 10.0 to 30.0, which the device correctly
  refused.
- 9.22.2.1 (writing a non-array property with an array index) now uses the
  device's writable output and passes.
- The same 65 tests are selected, and the device is unchanged.

## Tests that did not pass

| Test | Result | Why |
|---|---|---|
| 9.24.1.6 Disable-initiation restored by enable | SKIP | The test tool cannot yet hear the I-Am heartbeat that disable-initiation silences (it is broadcast to the device's own UDP port). Tracked for a fix. |
| 9.24.1.8 DeviceCommunicationControl finite disable-initiation expiry | SKIP | Same limitation as 9.24.1.6. |
| 9.24.1.9 Disable-initiation restored by the time duration | SKIP | Same limitation as 9.24.1.6. |
| 9.24.1.10 Disable-initiation restored by enable | SKIP | Same limitation as 9.24.1.6. |
| 9.24.1.1 Indefinite Time Duration Restored by DeviceCommunicationControl | SKIP | The test applies only to devices before Protocol_Revision 20 (it uses the deprecated DISABLE); this device is at revision 30. |
| 9.24.1.3 DeviceCommunicationControl finite duration expiry | SKIP | Same reason as 9.24.1.1. 9.24.1.11 checks that the device refuses DISABLE, and passes. |
| 9.24.1.4 Finite duration restored by enable | SKIP | Same reason as 9.24.1.1. |
| 7.3.2.10.9 Ensure Device Object_Name is Configurable | SKIP | Needs an operator to restart the device with another name (`--deviceName`); the run was unattended. |
| 7.3.2.10.10 Ensure Device Object_Identifier is Configurable | SKIP | Needs an operator to restart the device with another instance (`--deviceID`); the run was unattended. |
| 9.32.1.12 Who-Has After Object_Name Changed | SKIP | The device refuses a network write to its name, so the test asks an operator to change it by a restart; the run was unattended. |
| 9.32.1.13 Who-Has After Object_Identifier Changed | SKIP | The Object_Identifier form of 9.32.1.12 (`--deviceID`), with the same reason. |
| 7.3.2.10.3 Database_Revision after creating an object | SKIP | The device cannot create objects, so the test does not apply. |
| 7.3.2.10.4 Database_Revision after deleting an object | SKIP | The device cannot delete objects by any means, so the test does not apply. |
| 7.3.2.10.5 Database_Revision after changing an Object_Name | SKIP | The only changeable Object_Name is the Device's, changed by restarting the device with a new configuration. The test plan skips the test in that case. |
| 7.3.2.10.6 Database_Revision after changing an Object_Identifier | SKIP | The only changeable Object_Identifier is the Device's. The test plan skips the test in that case. |
| 9.22.1.3 Writing a Non-Commandable Property with a Priority | SKIP | Needs a writable property that is not commandable; this device has none. |
| 9.22.1.6 Writing NULL to Non-commandable Properties | SKIP | Needs a writable Present_Value that is not commandable; every writable Present_Value here is commandable, so the test plan skips it. |
| 9.22.2.10 Resizing a writable fixed size array property | SKIP | Needs a writable fixed-size array; this device has none. |
| 9.22.2.11 Writing a Property Value Related to Non-supported Optional Functionality | SKIP | Needs a property tied to optional functionality the device does not support; this device has none. |

No public issue has been opened for any of these.
