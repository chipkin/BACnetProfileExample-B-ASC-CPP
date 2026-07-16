// SPDX-License-Identifier: CC0-1.0
// Public-domain example code (CC0) - see ../LICENSE.
#ifndef CAS_EXAMPLE_HELPER_H
#define CAS_EXAMPLE_HELPER_H

// CASExampleHelper.h
// =============================================================================
// Shared boilerplate for every CAS BACnet Stack example project.
//
// The goal of these examples is that each profile's main.cpp reads like a
// tutorial: device setup, the objects it exposes, and the property callbacks -
// nothing else. All the "plumbing" that is identical for every example lives
// here:
//
//   * The UDP socket on the BACnet/IP port and the three transport/time
//     callbacks the stack always needs (receive, send, get-system-time).
//   * Printing version information (the example's version + the stack's).
//   * Parsing the common command-line options (e.g. --port).
//   * Reading the common keyboard commands (h / q / arrow up / arrow down).
//   * Sending an unsolicited I-Am on start-up.
//
// This folder is generic and is copied verbatim into each example repository.
// It carries its own version (COMMON_VERSION below) and its own changelog
// (common/CHANGELOG.md) so an example can tell whether its copy is stale.
// To change it: edit it, bump COMMON_VERSION, record the change in
// common/CHANGELOG.md, then re-copy common/ into EVERY example in the series.
//
// The CAS BACnet Stack itself is compiled into the program from source, so its
// C API (CASBACnetStackDLL.h) is linked directly - there is no "load" step.
// =============================================================================

#include <stdint.h>

namespace CASExampleHelper {

// --- Version / help --------------------------------------------------------
// The version of the vendored common/ helper itself (NOT the example's
// version). Bump it whenever anything in common/ changes, and record the
// change in common/CHANGELOG.md - every example in the series must then be
// re-synced to the same common/ version.
static const char* COMMON_VERSION = "1.3.0";

// Print the example's name + version, the linked CAS BACnet Stack version,
// and the common/ helper version.
void PrintVersion(const char* appName, const char* appVersion);

// Print the version information plus the list of interactive key commands.
// (This is what the 'h' key shows.)
void PrintHelp(const char* appName, const char* appVersion);

// --- Command line ----------------------------------------------------------
// Handle the two options that exit instead of running: --help and --version.
// Call this FIRST in main(), before binding a socket or touching the stack:
//
//     if (CASExampleHelper::HandleHelpAndVersionArgs(argc, argv, APP_NAME, APP_VERSION)) {
//         return 0;
//     }
//
// Returns true if it printed something and the caller should exit(0); false to
// carry on starting up. Every example in the series supports --help/--version,
// so this lives here rather than in each main.cpp.
bool HandleHelpAndVersionArgs(int argc, char** argv, const char* appName, const char* appVersion);

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

// --- Keyboard input (common to every example) ------------------------------
enum class KeyCommand {
    None,       // nothing pressed
    Help,       // 'h' - show version + commands
    Quit,       // 'q' - exit
    ArrowUp,    // up arrow
    ArrowDown   // down arrow
};

// Non-blocking: returns a pending key command, or None if nothing was pressed.
// Call once per tick of the main loop.
KeyCommand PollKey();

// Restore the terminal to its normal mode (POSIX); no-op on Windows. Call once
// before the program exits.
void RestoreInput();

} // namespace CASExampleHelper

#endif // CAS_EXAMPLE_HELPER_H
