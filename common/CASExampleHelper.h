// SPDX-License-Identifier: CC0-1.0
// Public-domain example code (CC0) - see ../LICENSE.
#ifndef CAS_EXAMPLE_HELPER_H
#define CAS_EXAMPLE_HELPER_H

// CASExampleHelper.h
// =============================================================================
// Shared BACnet/IP + CLI boilerplate for every CAS BACnet Stack example project.
//
// The goal of these examples is that each profile's main.cpp reads like a
// tutorial: device setup, the objects it exposes, and the property callbacks.
// All the "plumbing" that is identical for every example lives here:
//
//   * The UDP socket on the BACnet/IP port and the three transport/time
//     callbacks the stack always needs (receive, send, get-system-time).
//   * Printing version information (the example's version + the stack's).
//   * Parsing the common command-line options (e.g. --port, --deviceID).
//   * Sending an unsolicited I-Am on start-up.
//
// The interactive keyboard "edit mode" (changing object values while running)
// lives in its own file, common/CASExampleEditor - see CASExampleEditor.h.
//
// This file is generic and is copied verbatim into each example folder. The CAS
// BACnet Stack itself is compiled into the program from source, so its C API
// (CASBACnetStackDLL.h) is linked directly - there is no "load" step.
// =============================================================================

#include <stdint.h>

namespace CASExampleHelper {

// --- Version ---------------------------------------------------------------
// Print the example's name + version and the linked CAS BACnet Stack version.
void PrintVersion(const char* appName, const char* appVersion);

// --- Command line ----------------------------------------------------------
// Return the UDP port to use: the value after "--port" if present, else
// defaultPort. Common to every example.
uint16_t ParsePortArg(int argc, char** argv, uint16_t defaultPort);

// Return the device instance to use: the value after "--deviceID" if present,
// else defaultDeviceId. BACnet requires a device's instance to be configurable.
// Common to every example.
uint32_t ParseDeviceIdArg(int argc, char** argv, uint32_t defaultDeviceId);

// --- Networking ------------------------------------------------------------
// Bind the shared UDP socket to the BACnet/IP port (default 47808 / 0xBAC0).
bool SetupUDP(uint16_t port);

// Close the shared UDP socket.
void ShutdownUDP();

// Register the transport + system-time callbacks (backed by the UDP socket
// created in SetupUDP, so call SetupUDP first).
void RegisterCommonCallbacks();

// Broadcast an unsolicited I-Am for the given device. ANSI/ASHRAE 135 requires
// a device to announce itself with I-Am on start-up.
void SendIAm(uint32_t deviceInstance);

// Get the primary IPv4 interface's address and subnet mask (each as 4 octets).
// These are the values a BACnet/IP Network Port object reports (IP_Address,
// IP_Subnet_Mask), and the broadcast (ip | ~mask) is the I-Am target. Returns
// true on success; on failure the buffers are left untouched.
bool GetLocalIPv4(uint8_t ipAddress[4], uint8_t subnetMask[4]);

} // namespace CASExampleHelper

#endif // CAS_EXAMPLE_HELPER_H
