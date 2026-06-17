// SPDX-License-Identifier: CC0-1.0
// Public-domain example code (CC0) - see ../LICENSE.
#ifndef CAS_BACNET_STACK_EXAMPLE_CONSTANTS_H
#define CAS_BACNET_STACK_EXAMPLE_CONSTANTS_H

// CASBACnetStackExampleConstants.h
// =============================================================================
// A small, self-contained set of the BACnet enumeration values that the example
// projects need. The CAS BACnet Stack defines the FULL enumerations internally,
// in the stack header noted above each section below. We mirror only the handful
// of values used here so each example is easy to read and copy into a customer
// project - open the referenced stack header to see every available value.
//
// Every value matches the BACnet standard (ANSI/ASHRAE 135) and the CAS BACnet
// Stack enumerations. Add more as your own project needs them.
// =============================================================================

#include <stdint.h>

namespace CASBACnetStackExampleConstants {

// -- BACnet object types (Object_Type enumeration) -------------------------
//    Full list: submodules/cas-bacnet-stack/source/BACnetObjectType.h
static const uint16_t OBJECT_TYPE_ANALOG_INPUT = 0;
static const uint16_t OBJECT_TYPE_ANALOG_OUTPUT = 1;
static const uint16_t OBJECT_TYPE_BINARY_INPUT = 3;
static const uint16_t OBJECT_TYPE_BINARY_OUTPUT = 4;
static const uint16_t OBJECT_TYPE_DEVICE = 8;
static const uint16_t OBJECT_TYPE_MULTI_STATE_INPUT = 13;
static const uint16_t OBJECT_TYPE_MULTI_STATE_OUTPUT = 14;
static const uint16_t OBJECT_TYPE_NETWORK_PORT = 56;

// -- BACnet property identifiers (Property_Identifier enumeration) ----------
//    Full list: submodules/cas-bacnet-stack/source/BACnetPropertyIdentifier.h
static const uint32_t PROPERTY_IDENTIFIER_APPLICATION_SOFTWARE_VERSION = 12;
static const uint32_t PROPERTY_IDENTIFIER_APDU_LENGTH = 399;
static const uint32_t PROPERTY_IDENTIFIER_DESCRIPTION = 28;
static const uint32_t PROPERTY_IDENTIFIER_FIRMWARE_REVISION = 44;
static const uint32_t PROPERTY_IDENTIFIER_LOCATION = 58;
static const uint32_t PROPERTY_IDENTIFIER_MODEL_NAME = 70;
static const uint32_t PROPERTY_IDENTIFIER_IP_ADDRESS = 400;
static const uint32_t PROPERTY_IDENTIFIER_IP_DEFAULT_GATEWAY = 401;
static const uint32_t PROPERTY_IDENTIFIER_BACNET_IP_MODE = 408;
static const uint32_t PROPERTY_IDENTIFIER_IP_SUBNET_MASK = 411;
static const uint32_t PROPERTY_IDENTIFIER_BACNET_IP_UDP_PORT = 412;
static const uint32_t PROPERTY_IDENTIFIER_MAC_ADDRESS = 423;
static const uint32_t PROPERTY_IDENTIFIER_NUMBER_OF_STATES = 74;
static const uint32_t PROPERTY_IDENTIFIER_OBJECT_IDENTIFIER = 75;
static const uint32_t PROPERTY_IDENTIFIER_OBJECT_NAME = 77;
static const uint32_t PROPERTY_IDENTIFIER_OBJECT_TYPE = 79;
static const uint32_t PROPERTY_IDENTIFIER_OUT_OF_SERVICE = 81;
static const uint32_t PROPERTY_IDENTIFIER_POLARITY = 84;
static const uint32_t PROPERTY_IDENTIFIER_PRESENT_VALUE = 85;
static const uint32_t PROPERTY_IDENTIFIER_PRIORITY_ARRAY = 87;
static const uint32_t PROPERTY_IDENTIFIER_RELINQUISH_DEFAULT = 104;
static const uint32_t PROPERTY_IDENTIFIER_CURRENT_COMMAND_PRIORITY = 431;
static const uint32_t PROPERTY_IDENTIFIER_REFERENCE_PORT = 483;
static const uint32_t PROPERTY_IDENTIFIER_STATE_TEXT = 110;
static const uint32_t PROPERTY_IDENTIFIER_STATUS_FLAGS = 111;
static const uint32_t PROPERTY_IDENTIFIER_SYSTEM_STATUS = 112;
static const uint32_t PROPERTY_IDENTIFIER_UNITS = 117;
static const uint32_t PROPERTY_IDENTIFIER_VENDOR_IDENTIFIER = 120;
static const uint32_t PROPERTY_IDENTIFIER_VENDOR_NAME = 121;

// -- BACnet engineering units (Engineering_Units enumeration) ---------------
//    Full list: submodules/cas-bacnet-stack/source/BACnetEngineeringUnits.h
static const uint32_t ENGINEERING_UNITS_DEGREES_CELSIUS = 62;

// -- BACnet polarity (Polarity enumeration, for Binary objects) -------------
//    Full list: submodules/cas-bacnet-stack/source/BACnetPolarity.h
static const uint32_t POLARITY_NORMAL = 0;

// -- BACnet/IP mode (BACnetIPMode enumeration, for the Network Port) ---------
//    Full list: submodules/cas-bacnet-stack/source/BACnetIPMode.h
static const uint32_t BACNET_IP_MODE_NORMAL = 0;

// -- BACnet services (Services_Supported enumeration) -----------------------
//    Full list: submodules/cas-bacnet-stack/source/BACnetServicesSupported.h
//    Used with BACnetStack_SetServiceEnabled() to turn individual services on/off.
static const uint32_t SERVICE_READ_PROPERTY = 12;
static const uint32_t SERVICE_WRITE_PROPERTY = 15;
static const uint32_t SERVICE_DEVICE_COMMUNICATION_CONTROL = 17;

// -- BACnet error codes (Error_Code enumeration) ----------------------------
//    Full list: submodules/cas-bacnet-stack/source/BACnetErrorCode.h
//    A SetProperty* / service callback writes one of these to its errorCode
//    out-parameter and returns false to reject the request with that Error-PDU.
static const uint32_t ERROR_CODE_VALUE_OUT_OF_RANGE = 37;
static const uint32_t ERROR_CODE_PASSWORD_FAILURE = 26;

// -- DeviceCommunicationControl enable-disable argument ----------------------
//    Full list: submodules/cas-bacnet-stack/source/BACnetEnableDisable.h
static const uint8_t DCC_ENABLE = 0;             // resume all communication
static const uint8_t DCC_DISABLE = 1;            // stop initiating AND responding
static const uint8_t DCC_DISABLE_INITIATION = 2; // keep responding, stop initiating

// -- Transport network type (BACnetPacket::NetworkType, for the send/receive
//    callbacks and SendIAm).
//    Full list: submodules/cas-bacnet-stack/source/BACnetPacket.h
//    NOTE: this is a DIFFERENT enumeration from the Network Port object's
//    network type below (see the GOTCHA in CASBACnetStackDLL.h).
static const uint8_t NETWORK_TYPE_IP = 0;

// -- Network Port object network type (BACnetNetworkType enumeration, used by
//    BACnetStack_AddNetworkPortObject).
//    Full list: submodules/cas-bacnet-stack/source/BACnetNetworkType.h
static const uint8_t NETWORK_PORT_NETWORK_TYPE_IPV4 = 5;

// -- Network Port object protocol level (BACnetProtocolLevel enumeration, used
//    by BACnetStack_AddNetworkPortObject).
//    Full list: submodules/cas-bacnet-stack/source/BACnetProtocolLevel.h
static const uint8_t NETWORK_PORT_PROTOCOL_LEVEL_BACNET_APPLICATION = 2;
// The lowest protocol layer references this sentinel instead of another port.
static const uint32_t NETWORK_PORT_REFERENCE_PORT_NONE = 4194303;

// -- Character string encoding (the encoding byte returned by the character-
//    string Get callback). 0 = UTF-8. The BACnet character-set values are
//    defined by ANSI/ASHRAE 135 Clause 20.2.9; see the stack's handling in
//    submodules/cas-bacnet-stack/source/BACnetPrimitiveCharSTRING.h
static const uint8_t CHARACTER_STRING_ENCODING_UTF8 = 0;

} // namespace CASBACnetStackExampleConstants

#endif // CAS_BACNET_STACK_EXAMPLE_CONSTANTS_H
