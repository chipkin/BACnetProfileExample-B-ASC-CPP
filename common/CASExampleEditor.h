// SPDX-License-Identifier: CC0-1.0
// Public-domain example code (CC0) - see ../LICENSE.
#ifndef CAS_EXAMPLE_EDITOR_H
#define CAS_EXAMPLE_EDITOR_H

// CASExampleEditor.h
// =============================================================================
// The shared interactive "edit mode" for the CAS BACnet Stack example series.
//
// It lets a user change live object values from the keyboard WHILE the example
// runs, so ReadProperty / COV / intrinsic alarms can be exercised without a
// separate BACnet client. All the complexity - per-OS raw key reading, the
// object menu, selection, and value editing - lives in this one file, so each
// example's main.cpp just registers its editable points and calls
// ProcessConsoleInput() once per tick. After every change the editor calls
// BACnetStack_UpdateValue(...) for that object, so the stack re-evaluates COV
// subscriptions and intrinsic event algorithms (this is how a keystroke can
// drive an Analog Value past its alarm limit, or change a lighting level).
//
// main.cpp usage (the whole interactive surface):
//     CASExampleEditor::SetAppInfo(APP_NAME, APP_VERSION);
//     CASExampleEditor::RegisterEditableReal(dev, OBJECT_TYPE_ANALOG_INPUT, 1,
//         "Analog Input 1 (Bronze)", &g_analogInput1Value, 1.1f, -50.0f, 150.0f);
//     ... register the other points ...
//     while (running) {
//         BACnetStack_Tick();
//         if (!CASExampleEditor::ProcessConsoleInput()) running = false;
//     }
//     CASExampleEditor::RestoreInput();   // once, before exit (POSIX terminal)
//
// This file is generic and is copied verbatim into each example's common/ folder
// alongside CASExampleHelper. Keep it identical across examples.
// =============================================================================

#include <stdint.h>

namespace CASExampleEditor {

// How a registered point is edited and displayed. Add a kind here when a new
// object type needs editing (e.g. a commandable Lighting Output ramp).
enum class PointKind {
    AnalogReal,   // REAL Present_Value; up/down add/subtract `step` (Analog Input/Value, Lighting %)
    Binary,       // 0/1 Present_Value; up/down/space turn it on/off (Binary Input/Value)
    MultiState    // 1..numStates Present_Value; up/down step through states (Multi-State Input/Value)
};

// Tell the editor the example's name + version (shown by the 'h' help key).
// Call once before the run loop.
void SetAppInfo(const char* appName, const char* appVersion);

// Register a REAL point. `value` is the example's own live variable - the one its
// Get callback already returns - which the editor edits in place, clamped to
// [minValue, maxValue], in `step` increments.
void RegisterEditableReal(uint32_t deviceInstance, uint16_t objectType,
                          uint32_t objectInstance, const char* name,
                          float* value, float step, float minValue, float maxValue);

// Register a binary (0/1) point. The editor turns it on/off.
void RegisterEditableBinary(uint32_t deviceInstance, uint16_t objectType,
                            uint32_t objectInstance, const char* name, uint32_t* value);

// Register a multi-state point whose value runs 1..numStates. The editor steps
// through the states (wrapping at the ends).
void RegisterEditableMultiState(uint32_t deviceInstance, uint16_t objectType,
                                uint32_t objectInstance, const char* name,
                                uint32_t* value, uint32_t numStates);

// Register an example-specific one-key action (e.g. "fire an alarm", "send a
// write"). Shown in help and invoked from normal mode. Keep these rare - most
// interaction should be object editing through edit mode. A client example
// (which hosts no editable objects) uses these instead of editable points.
typedef void (*ActionFn)();
void RegisterActionKey(char key, const char* description, ActionFn action);

// Call once per tick from the run loop. Handles ALL keyboard input; returns
// false only when the user asks to quit:
//   normal mode: h help . q quit . e enter edit mode . <action keys>
//   edit mode:   1-9 select object . up/down change . space toggle/next . esc exit
bool ProcessConsoleInput();

// Restore the terminal to its normal mode (POSIX); no-op on Windows. Call once
// before the program exits (the editor switches the terminal to raw mode the
// first time it reads a key).
void RestoreInput();

} // namespace CASExampleEditor

#endif // CAS_EXAMPLE_EDITOR_H
