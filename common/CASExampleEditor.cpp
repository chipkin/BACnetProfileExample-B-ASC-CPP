// SPDX-License-Identifier: CC0-1.0
// Public-domain example code (CC0) - see ../LICENSE.
// CASExampleEditor.cpp
// =============================================================================
// Implementation of the shared interactive "edit mode". See CASExampleEditor.h.
// =============================================================================

#include "CASExampleEditor.h"
#include "CASBACnetStackExampleConstants.h"

// The CAS BACnet Stack C API - the whole stack is compiled into this program
// from source, so we call BACnetStack_* directly (UpdateValue + version).
#include "CASBACnetStackDLL.h"

#include <stdio.h>

#if defined(_WIN32)
#include <conio.h>
#else
#include <termios.h>
#include <unistd.h>
#include <fcntl.h>
#endif

namespace {

// --- Raw single-key reader --------------------------------------------------
// Returns the key code, or KEY_NONE if nothing is pending. Arrow keys come back
// as KEY_UP / KEY_DOWN, a lone Escape as KEY_ESC, and every other key as its
// ASCII value. Non-blocking (called once per tick).
const int KEY_NONE = -1;
const int KEY_UP   = 1001;
const int KEY_DOWN = 1002;
const int KEY_ESC  = 27;

#if !defined(_WIN32)
// POSIX terminal raw-mode handling for non-blocking single-key reads.
struct termios g_origTermios;
bool g_rawActive = false;

void EnableRawInput() {
    if (g_rawActive) {
        return;
    }
    if (tcgetattr(STDIN_FILENO, &g_origTermios) != 0) {
        return; // not a tty (e.g. piped) - leave input alone
    }
    struct termios raw = g_origTermios;
    raw.c_lflag &= ~(unsigned)(ICANON | ECHO); // no line buffering, no echo
    raw.c_cc[VMIN] = 0;                          // non-blocking read
    raw.c_cc[VTIME] = 0;
    tcsetattr(STDIN_FILENO, TCSANOW, &raw);
    const int flags = fcntl(STDIN_FILENO, F_GETFL, 0);
    fcntl(STDIN_FILENO, F_SETFL, flags | O_NONBLOCK);
    g_rawActive = true;
}
#endif

int ReadRawKey() {
#if defined(_WIN32)
    if (!_kbhit()) {
        return KEY_NONE;
    }
    const int c = _getch();
    if (c == 0 || c == 0xE0) {            // arrow / function-key prefix
        const int c2 = _getch();
        if (c2 == 72) return KEY_UP;
        if (c2 == 80) return KEY_DOWN;
        return KEY_NONE;
    }
    return c;
#else
    EnableRawInput();
    unsigned char buf[3];
    const int n = (int)read(STDIN_FILENO, buf, sizeof(buf));
    if (n <= 0) {
        return KEY_NONE;
    }
    if (n >= 3 && buf[0] == 27 && buf[1] == '[') { // ESC [ A/B = arrow keys
        if (buf[2] == 'A') return KEY_UP;
        if (buf[2] == 'B') return KEY_DOWN;
        return KEY_NONE;
    }
    if (n == 1 && buf[0] == 27) {
        return KEY_ESC;
    }
    return buf[0];
#endif
}

// --- Registry ---------------------------------------------------------------
// One registered editable point. Only the fields relevant to its kind are used.
struct EditablePoint {
    CASExampleEditor::PointKind kind;
    uint32_t deviceInstance;
    uint16_t objectType;
    uint32_t objectInstance;
    const char* name;
    float* realValue;    // AnalogReal: the live REAL value
    float step;
    float minValue;
    float maxValue;
    uint32_t* uintValue; // Binary (0/1) and MultiState (1..numStates)
    uint32_t numStates;
};

// Capped at 9 so every point is reachable with a single digit key (1-9) in edit
// mode. Bump this AND the selection handling together if an example ever needs
// more than nine editable points.
const int MAX_EDITABLE_POINTS = 9;
EditablePoint g_points[MAX_EDITABLE_POINTS];
int g_pointCount = 0;

struct ActionKeyEntry {
    char key;
    const char* description;
    CASExampleEditor::ActionFn fn;
};
const int MAX_ACTION_KEYS = 8;
ActionKeyEntry g_actionKeys[MAX_ACTION_KEYS];
int g_actionKeyCount = 0;

bool g_editMode = false;
int g_selectedPoint = -1;

const char* g_appName = "BACnet Example";
const char* g_appVersion = "0.0.0";

// Print one point's current value in a human-friendly form.
void PrintPointValue(const EditablePoint& point) {
    switch (point.kind) {
        case CASExampleEditor::PointKind::AnalogReal:
            printf("%.1f", *point.realValue);
            break;
        case CASExampleEditor::PointKind::Binary:
            printf("%s (%u)", (*point.uintValue ? "active" : "inactive"),
                   (unsigned)*point.uintValue);
            break;
        case CASExampleEditor::PointKind::MultiState:
            printf("state %u of %u", (unsigned)*point.uintValue,
                   (unsigned)point.numStates);
            break;
    }
}

// Apply a change to a point, then tell the stack so COV / intrinsic alarms
// re-evaluate. dir is +1 (increase) or -1 (decrease); toggle flips a Binary or
// advances a Multi-State regardless of direction.
void ApplyPointChange(EditablePoint& point, const int dir, const bool toggle) {
    switch (point.kind) {
        case CASExampleEditor::PointKind::AnalogReal: {
            float v = *point.realValue + (float)dir * point.step;
            if (v < point.minValue) v = point.minValue;
            if (v > point.maxValue) v = point.maxValue;
            *point.realValue = v;
            break;
        }
        case CASExampleEditor::PointKind::Binary:
            if (toggle) {
                *point.uintValue = (*point.uintValue != 0) ? 0u : 1u;
            } else {
                *point.uintValue = (dir > 0) ? 1u : 0u;
            }
            break;
        case CASExampleEditor::PointKind::MultiState: {
            uint32_t v = *point.uintValue;
            if (toggle || dir > 0) {
                v = (v >= point.numStates) ? 1u : v + 1u;
            } else {
                v = (v <= 1u) ? point.numStates : v - 1u;
            }
            *point.uintValue = v;
            break;
        }
    }
    // Tell the stack the Present_Value changed so it issues COV notifications and
    // runs any intrinsic alarm algorithm on this object. (UpdateValue is safe to
    // call even if a clamp left the value unchanged - the stack simply finds no
    // delta and notifies no one.)
    BACnetStack_UpdateValue(point.deviceInstance, point.objectType,
                            point.objectInstance,
                            CASBACnetStackExampleConstants::PROPERTY_IDENTIFIER_PRESENT_VALUE);
}

// Print the edit-mode object menu.
void PrintEditMenu() {
    printf("\n-- EDIT MODE -- press 1-%d to select an object, then up/down to "
           "change it, space to toggle/next, esc to exit.\n", g_pointCount);
    for (int i = 0; i < g_pointCount; ++i) {
        printf("  [%d] %-26s = ", i + 1, g_points[i].name);
        PrintPointValue(g_points[i]);
        printf("\n");
    }
}

// Print the help screen: version, common commands, action keys, editable list.
void PrintHelpScreen() {
    printf("%s v%s\n", g_appName, g_appVersion);
    printf("CAS BACnet Stack version: %u.%u.%u.%u\n",
           BACnetStack_GetAPIMajorVersion(), BACnetStack_GetAPIMinorVersion(),
           BACnetStack_GetAPIPatchVersion(), BACnetStack_GetAPIBuildVersion());
    printf("Commands:\n");
    printf("  h   - show this help (version + commands)\n");
    printf("  q   - quit\n");
    if (g_pointCount > 0) {
        printf("  e   - edit object values (enter edit mode)\n");
    }
    for (int i = 0; i < g_actionKeyCount; ++i) {
        printf("  %c   - %s\n", g_actionKeys[i].key, g_actionKeys[i].description);
    }
    if (g_pointCount > 0) {
        printf("Editable objects (press 'e', then the object's number):\n");
        for (int i = 0; i < g_pointCount; ++i) {
            printf("  [%d] %-26s = ", i + 1, g_points[i].name);
            PrintPointValue(g_points[i]);
            printf("\n");
        }
    }
}

} // namespace

namespace CASExampleEditor {

void SetAppInfo(const char* appName, const char* appVersion) {
    g_appName = appName;
    g_appVersion = appVersion;
}

void RegisterEditableReal(uint32_t deviceInstance, uint16_t objectType,
                          uint32_t objectInstance, const char* name,
                          float* value, float step, float minValue, float maxValue) {
    if (g_pointCount >= MAX_EDITABLE_POINTS || value == NULL) {
        printf("FYI: editor full or null value; '%s' not registered.\n",
               name ? name : "(null)");
        return;
    }
    EditablePoint& p = g_points[g_pointCount++];
    p.kind = PointKind::AnalogReal;
    p.deviceInstance = deviceInstance;
    p.objectType = objectType;
    p.objectInstance = objectInstance;
    p.name = name;
    p.realValue = value;
    p.step = step;
    p.minValue = minValue;
    p.maxValue = maxValue;
    p.uintValue = NULL;
    p.numStates = 0;
}

void RegisterEditableBinary(uint32_t deviceInstance, uint16_t objectType,
                            uint32_t objectInstance, const char* name, uint32_t* value) {
    if (g_pointCount >= MAX_EDITABLE_POINTS || value == NULL) {
        printf("FYI: editor full or null value; '%s' not registered.\n",
               name ? name : "(null)");
        return;
    }
    EditablePoint& p = g_points[g_pointCount++];
    p.kind = PointKind::Binary;
    p.deviceInstance = deviceInstance;
    p.objectType = objectType;
    p.objectInstance = objectInstance;
    p.name = name;
    p.realValue = NULL;
    p.step = 0.0f;
    p.minValue = 0.0f;
    p.maxValue = 0.0f;
    p.uintValue = value;
    p.numStates = 0;
}

void RegisterEditableMultiState(uint32_t deviceInstance, uint16_t objectType,
                                uint32_t objectInstance, const char* name,
                                uint32_t* value, uint32_t numStates) {
    if (g_pointCount >= MAX_EDITABLE_POINTS || value == NULL || numStates == 0) {
        printf("FYI: editor full or invalid; '%s' not registered.\n",
               name ? name : "(null)");
        return;
    }
    EditablePoint& p = g_points[g_pointCount++];
    p.kind = PointKind::MultiState;
    p.deviceInstance = deviceInstance;
    p.objectType = objectType;
    p.objectInstance = objectInstance;
    p.name = name;
    p.realValue = NULL;
    p.step = 0.0f;
    p.minValue = 0.0f;
    p.maxValue = 0.0f;
    p.uintValue = value;
    p.numStates = numStates;
}

void RegisterActionKey(char key, const char* description, ActionFn action) {
    if (g_actionKeyCount >= MAX_ACTION_KEYS || action == NULL) {
        return;
    }
    ActionKeyEntry& a = g_actionKeys[g_actionKeyCount++];
    a.key = key;
    a.description = description;
    a.fn = action;
}

bool ProcessConsoleInput() {
    const int key = ReadRawKey();
    if (key == KEY_NONE) {
        return true;
    }

    if (!g_editMode) {
        // -- normal mode --
        if (key == 'h' || key == 'H') {
            PrintHelpScreen();
            return true;
        }
        if (key == 'q' || key == 'Q') {
            return false; // ask the run loop to quit
        }
        if (key == 'e' || key == 'E') {
            if (g_pointCount == 0) {
                printf("FYI: this example has no editable objects.\n");
                return true;
            }
            g_editMode = true;
            g_selectedPoint = -1;
            PrintEditMenu();
            return true;
        }
        for (int i = 0; i < g_actionKeyCount; ++i) {
            if (key == g_actionKeys[i].key) {
                g_actionKeys[i].fn();
                return true;
            }
        }
        return true;
    }

    // -- edit mode --
    if (key == KEY_ESC || key == 'e' || key == 'E' || key == 'q' || key == 'Q') {
        g_editMode = false;
        g_selectedPoint = -1;
        printf("-- left edit mode --\n");
        return true;
    }
    if (key == 'h' || key == 'H') {
        PrintEditMenu();
        return true;
    }
    if (key >= '1' && key <= '9') {
        const int index = key - '1';
        if (index < g_pointCount) {
            g_selectedPoint = index;
            printf("Selected [%d] %s = ", index + 1, g_points[index].name);
            PrintPointValue(g_points[index]);
            printf("\n");
        }
        return true;
    }
    if (g_selectedPoint < 0) {
        printf("FYI: pick an object first (press 1-%d).\n", g_pointCount);
        return true;
    }
    EditablePoint& point = g_points[g_selectedPoint];
    if (key == KEY_UP || key == '+' || key == '=') {
        ApplyPointChange(point, +1, false);
    } else if (key == KEY_DOWN || key == '-' || key == '_') {
        ApplyPointChange(point, -1, false);
    } else if (key == ' ') {
        ApplyPointChange(point, +1, true);
    } else {
        return true; // ignore any other key while in edit mode
    }
    printf("  %s = ", point.name);
    PrintPointValue(point);
    printf("\n");
    return true;
}

void RestoreInput() {
#if !defined(_WIN32)
    if (g_rawActive) {
        tcsetattr(STDIN_FILENO, TCSANOW, &g_origTermios);
        g_rawActive = false;
    }
#endif
}

} // namespace CASExampleEditor
