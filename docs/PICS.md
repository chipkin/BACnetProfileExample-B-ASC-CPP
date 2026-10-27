# BACnet Protocol Implementation Conformance Statement (PICS)

For the **BACnet B-ASC (Application Specific Controller) C++ example** -
see [README.md](../README.md).

> This is the PICS **for the example as shipped**. It describes a tutorial
> device announcing itself as a Chipkin demo, not a product. When you turn this
> example into your own device, this document is one of the things you rewrite:
> the vendor, model and version rows all come from the
> `CHANGE ALL OF THIS BEFORE YOU SHIP` block at the top of `main.cpp`. The
> example has **not** been submitted for BTL certification.

## 1. Product description

| | |
|---|---|
| **Vendor Name** | Chipkin Automation Systems |
| **Vendor Identifier** | 389 |
| **Product Name** | CAS BACnet Stack Example - B-ASC |
| **Product Model Number** | CAS BACnet Stack Example - B-ASC |
| **Application Software Version** | 1.5.0 |
| **Firmware Revision** | 6.0.23.0 (the CAS BACnet Stack version) |
| **BACnet Protocol Version** | 1 |
| **BACnet Protocol Revision** | 30 |

**Product Description:** a BACnet/IP Application Specific Controller built on
the CAS BACnet Stack. It presents three read-only sensor objects (Analog
Input, Binary Input, Multi-State Input) and three commandable output objects
(Analog Output, Binary Output, Multi-State Output), answers ReadProperty for
every required property of every object, accepts WriteProperty to the
commandable outputs' `Present_Value` (refusing values out of range) and acts
on the winning command through a simulated valve, relay and drive whose
feedback the input objects report, reports a disconnected valve through Analog
Output 1's Reliability and Status_Flags FAULT, announces itself with an I-Am
heartbeat that DeviceCommunicationControl silences and resumes, and is
discoverable by Who-Is / I-Am and Who-Has / I-Have. It is a tutorial for
implementers of the B-ASC profile.

## 2. BACnet standardized device profile (Annex L)

**B-ASC - BACnet Application Specific Controller.**

This device claims exactly one profile. Because the B-ASC requirements are a
superset of B-GENERAL's, a conformant B-ASC device also satisfies
**B-GENERAL** (Annex L.8); that is subsumption, not a second claim.

## 3. BIBBs supported (Annex K)

| BIBB | Description |
|---|---|
| DS-RP-B | Data Sharing - ReadProperty - B |
| DS-WP-B | Data Sharing - WriteProperty - B |
| DM-DCC-B | Device Management - DeviceCommunicationControl - B |
| DM-DDB-B | Device Management - Dynamic Device Binding - B |
| DM-DOB-B | Device Management - Dynamic Object Binding - B |

No other BIBBs are supported. In particular this device does **not** support
DS-RPM-B (ReadPropertyMultiple), DS-WPM-B, DS-COV-B, any alarm and event
(AE-*) BIBB, scheduling (SCHED-*), or trending (T-*).

## 4. Application services supported

| Service | Initiate | Execute |
|---|:---:|:---:|
| ReadProperty | no | **yes** |
| WriteProperty | no | **yes** |
| DeviceCommunicationControl | no | **yes** |
| Who-Is | no | **yes** |
| I-Am | **yes** | - |
| Who-Has | no | **yes** |
| I-Have | **yes** | - |

An unsolicited I-Am is broadcast to the local subnet at start-up and then every
5 s (the heartbeat), as well as in response to Who-Is.

Any other confirmed service is rejected. That rejection is part of the profile
boundary, not a limitation to work around.

### DeviceCommunicationControl

The device accepts `enable` and `disable-initiation`. The deprecated plain
`disable` value is **rejected** with `service-request-denied` (135-2024 clause
16.1.2; this device is at Protocol_Revision 30). An optional password (none by
default, so any request is accepted; set with `--dcc-password <string>`) is
compared length-first-then-bytes; a missing or wrong one is rejected with
`password-failure` (Error Class = SECURITY). What `disable-initiation` stops is
the 5 s I-Am heartbeat - the stack refuses to send it (clause 16.1.2) until an
`enable`, or the end of the request's time duration; an I-Am in answer to Who-Is,
ReadProperty and WriteProperty are still served. Requests of a limited duration
are supported (K.5.6), as are indefinite ones.

## 5. Segmentation capability

Segmentation is **supported in both directions**
(`Segmentation_Supported` = `segmented-both`), by the stack: at `6.x` @
`69b6249f` the customer build compiles `STACK_OPTION_SEGMENTATION` in (stack
#2992), and this example keeps the stack's defaults - `Max_Segments_Accepted`
16 and `APDU_Segment_Timeout` 5000 ms. Table 12-13 footnote 1: "These
properties are required if, and shall be present only if, segmentation of any
kind is supported" - they are not rows in section 11 because its generator lists
only unconditionally required properties. `Max_APDU_Length_Accepted` is 1476
octets, the BACnet/IP maximum. (At the previous pin, `abd4cee1`, this example
answered `no-segmentation`.)

## 6. Standard object types supported

No object is dynamically creatable or deletable. The three input objects and
the Network Port are read-only; the three output objects' `Present_Value` is
writable (commandable, 16-slot Priority_Array).

| Object type | Instance | Object_Name | Optional properties supported |
|---|:---:|---|---|
| Device | 389003 | Chipkin Example B-ASC | Description |
| Analog Input | 1 | Bronze | - |
| Binary Input | 1 | Emerald | - |
| Multi-State Input | 1 | Hot Pink | State_Text |
| Analog Output | 1 | Chartreuse | Min_Pres_Value, Max_Pres_Value, Reliability |
| Binary Output | 1 | Fuchsia | - |
| Multi-State Output | 1 | Indigo | - |
| Network Port | 1 | Vermilion | - |

The device instance is configurable at start-up with `--deviceID`, and the
Device's Object_Name with `--deviceName` (BACnet requires both to be
configurable, cl. 12.1.1.3 and 12.1.1.4). Changing either means restarting
the device; neither is writable over the network. The table shows the
defaults.

## 7. Data link layer options

**BACnet/IP (Annex J)**, UDP port 47808 (0xBAC0) by default, configurable at run
time with `--port`.

BBMD is not supported, Foreign Device registration is not supported, and
BACnet/SC, MS/TP, Ethernet (Annex H) and PTP are not supported.

The stack's Network Port object still lists its BACnet/IP properties in
`Property_List` - including `IP_DNS_Server`, `FD_BBMD_Address` and
`FD_Subscription_Lifetime` - and every one of them reads as a value
(`FD_BBMD_Address` is a Null host, port 0: no BBMD configured). The Wire Tests
read every listed property of every object.

## 8. Device address binding

Static device binding is **not supported**. The device answers Who-Is/Who-Has
and does not initiate any confirmed request, so it never needs to bind a peer.

## 9. Networking options

None. The device is not a router, not a BBMD, and does not register as a foreign
device.

## 10. Character sets supported

UTF-8 (ANSI X3.4). Supporting a character set does not imply the device can
handle data in all character sets.

## 11. Objects and properties

<!-- OBJECTS-PROPERTIES:BEGIN (generated by tools/gen-objects-properties.py from docs/objects.json - do not edit here) -->
Every object this example creates, and every REQUIRED property of each (per ANSI/ASHRAE 135-2024 clause 12 and the CAS BACnet Stack's property profiles), plus the optional properties the example turns on. **Served by** says who answers a ReadProperty: the **stack** generates it, or the **app** serves it from a `GetProperty*` callback in `main.cpp`. A ⚠ row is a required property the app does not serve and the stack would fill with a default - that is a defect, not a feature.

### Device 389003 "Chipkin Example B-ASC" - vendor 389 (Chipkin Automation Systems); instance configurable with --deviceID and the Object_Name with --deviceName (both at start-up; the heading shows the defaults). The stack rows are device-wide facts only the stack knows - the protocol version and revision it implements, the services and object types it was configured with, the live object list and address-binding table, and Database_Revision, which the stack starts at 0 and increments for each object added at start-up: it reads 8 (the Device and its seven objects) and stays 8, because nothing creates, deletes or renames an object afterwards (a command or a DeviceCommunicationControl changes no object). The accepted rows are the stack's configured defaults for APDU limits, segmentation and system status; an application that answered them from its own constants could contradict the stack, so this example does not

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| System_Status | BACnetDeviceStatus | stack default, accepted (Generic Enumerated default: `0`) | no |
| Vendor_Name | CharacterString | app | no |
| Vendor_Identifier | Unsigned16 | app | no |
| Model_Name | CharacterString | app | no |
| Firmware_Revision | CharacterString | app | no |
| Application_Software_Version | CharacterString | app | no |
| Description *(optional, enabled)* | CharacterString | app | no |
| Protocol_Version | Unsigned | stack | no |
| Protocol_Revision | Unsigned | stack | no |
| Protocol_Services_Supported | BACnetServicesSupported | stack | no |
| Protocol_Object_Types_Supported | BACnetObjectTypesSupported | stack | no |
| Object_List | BACnetARRAY[N] of BACnetObjectIdentifier | stack | no |
| Max_APDU_Length_Accepted | Unsigned | stack default, accepted (`CAS_BACNET_DEVICE_DEFAULT_MAX_APDU_LENGTH_ACCEPTED`) | no |
| Segmentation_Supported | BACnetSegmentation | stack default, accepted (`BACnetSegmentation::segmentedBoth` with `STACK_OPTION_SEGME) | no |
| APDU_Timeout | Unsigned | stack default, accepted (`CAS_BACNET_DEVICE_DEFAULT_APDU_TIMEOUT`) | no |
| Number_Of_APDU_Retries | Unsigned | stack default, accepted (`CAS_BACNET_DEVICE_DEFAULT_NUMBER_OF_APDU_RETRIES`) | no |
| Device_Address_Binding | BACnetLIST of BACnetAddressBinding | stack | no |
| Database_Revision | Unsigned | stack | no |
| Property_List | BACnetARRAY[N] of BACnetPropertyIdentifier | stack | no |

### Analog Input 1 "Bronze" - REAL, degrees Celsius; read-only; the temperature the simulated heating valve produces - it moves up to 1.0 C a second toward the winning Analog Output 1 setpoint (starts at 21.5)

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| Present_Value | Real | app | no |
| Status_Flags | BACnetStatusFlags | stack | no |
| Event_State | BACnetEventState | stack default, accepted (Generic Enumerated default: `0`) | no |
| Out_Of_Service | Boolean | app | no |
| Units | BACnetEngineeringUnits | app | no |
| Property_List | BACnetARRAY[N] of BACnetPropertyIdentifier | stack | no |

### Binary Input 1 "Emerald" - read-only; the simulated relay's feedback contact - takes the winning Binary Output 1 command within a second (starts inactive)

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| Present_Value | BACnetBinaryPV | app | no |
| Status_Flags | BACnetStatusFlags | stack | no |
| Event_State | BACnetEventState | stack default, accepted (Generic Enumerated default: `0`) | no |
| Out_Of_Service | Boolean | app | no |
| Polarity | BACnetPolarity | app | no |
| Property_List | BACnetARRAY[N] of BACnetPropertyIdentifier | stack | no |

### Multi-state Input 1 "Hot Pink" - 3 states: On, Off, Auto; read-only; the simulated drive's speed - takes the winning Multi-State Output 1 command within a second

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| Present_Value | Unsigned | app | no |
| Status_Flags | BACnetStatusFlags | stack | no |
| Event_State | BACnetEventState | stack default, accepted (Generic Enumerated default: `0`) | no |
| Out_Of_Service | Boolean | app | no |
| Number_Of_States | Unsigned | app | no |
| State_Text *(optional, enabled)* | BACnetARRAY[N] of CharacterString | app | no |
| Property_List | BACnetARRAY[N] of BACnetPropertyIdentifier | stack | no |

### Analog Output 1 "Chartreuse" - REAL setpoint, default 20.0 C, accepts 10.0 .. 30.0 (Min_Pres_Value / Max_Pres_Value, else value-out-of-range); Reliability no-fault-detected, or no-output while the simulated valve actuator is disconnected (the stack derives Status_Flags FAULT from it); commandable via a 16-slot Priority_Array (WriteProperty, DS-WP-B) - Present_Value/Priority_Array/Current_Command_Priority are resolved by the stack from the slots the app serves through GetPropertyReal/GetPropertyBool

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| Present_Value | Real | stack | yes |
| Status_Flags | BACnetStatusFlags | stack | no |
| Event_State | BACnetEventState | stack default, accepted (Generic Enumerated default: `0`) | no |
| Reliability *(optional, enabled)* | BACnetReliability | app | no |
| Out_Of_Service | Boolean | app | no |
| Units | BACnetEngineeringUnits | app | no |
| Min_Pres_Value *(optional, enabled)* | Real | app | no |
| Max_Pres_Value *(optional, enabled)* | Real | app | no |
| Priority_Array | BACnetARRAY[16] of BACnetOptionalReal | stack | no |
| Relinquish_Default | Real | app | no |
| Property_List | BACnetARRAY[N] of BACnetPropertyIdentifier | stack | no |
| Current_Command_Priority | BACnetOptionalUnsigned | stack | no |

### Binary Output 1 "Fuchsia" - active/inactive, default inactive; commandable via a 16-slot Priority_Array (WriteProperty, DS-WP-B) - Present_Value/Priority_Array/Current_Command_Priority are resolved by the stack from the slots the app serves through GetPropertyEnumerated/GetPropertyBool

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| Present_Value | BACnetBinaryPV | stack | yes |
| Status_Flags | BACnetStatusFlags | stack | no |
| Event_State | BACnetEventState | stack default, accepted (Generic Enumerated default: `0`) | no |
| Out_Of_Service | Boolean | app | no |
| Polarity | BACnetPolarity | app | no |
| Priority_Array | BACnetARRAY[16] of BACnetOptionalBinaryPV | stack | no |
| Relinquish_Default | BACnetBinaryPV | app | no |
| Property_List | BACnetARRAY[N] of BACnetPropertyIdentifier | stack | no |
| Current_Command_Priority | BACnetOptionalUnsigned | stack | no |

### Multi-state Output 1 "Indigo" - state 1 of 3, default state 1; commandable via a 16-slot Priority_Array (WriteProperty, DS-WP-B) - Present_Value/Priority_Array/Current_Command_Priority are resolved by the stack from the slots the app serves through GetPropertyUnsignedInteger/GetPropertyBool

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| Present_Value | Unsigned | stack | yes |
| Status_Flags | BACnetStatusFlags | stack | no |
| Event_State | BACnetEventState | stack default, accepted (Generic Enumerated default: `0`) | no |
| Out_Of_Service | Boolean | app | no |
| Number_Of_States | Unsigned | app | no |
| Priority_Array | BACnetARRAY[16] of BACnetOptionalUnsigned | stack | no |
| Relinquish_Default | Unsigned | app | no |
| Property_List | BACnetARRAY[N] of BACnetPropertyIdentifier | stack | no |
| Current_Command_Priority | BACnetOptionalUnsigned | stack | no |

### Network Port 1 "Vermilion" - BACnet/IP; Network_Type and Protocol_Level are set from BACnetStack_AddNetworkPortObject()'s arguments (IPv4, BACnet Application) at start-up, not a GetProperty callback like the object's other app-served rows; Changes_Pending is likewise computed and answered natively by the stack's Network Port object. Reliability has no fault condition this example detects, so it is accepted at the generic default (normal)

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| Status_Flags | BACnetStatusFlags | stack | no |
| Reliability | BACnetReliability | stack default, accepted (Generic Enumerated default: `0`) | no |
| Out_Of_Service | Boolean | app | no |
| Network_Type | BACnetNetworkType | app | no |
| Protocol_Level | BACnetProtocolLevel | app | no |
| Changes_Pending | Boolean | app | no |
| Property_List | BACnetARRAY[N] of BACnetPropertyIdentifier | stack | no |

<!-- OBJECTS-PROPERTIES:END -->

## 12. References

- ANSI/ASHRAE Standard 135-2024, Annex A (PICS template), Annex K (BIBBs),
  Annex L (device profiles), Clause 12 (object types), Clause 16
  (DeviceCommunicationControl is 16.1).
- [README.md](../README.md) - what this example is and how to build it.
- [TUTORIAL.md](../TUTORIAL.md) - how to extend it, and how to keep this
  document honest when you do.
