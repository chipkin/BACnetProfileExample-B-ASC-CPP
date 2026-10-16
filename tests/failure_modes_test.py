#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
# Public-domain example code (CC0) - see ../LICENSE.
"""B-ASC Wire Test: the actuator's Failure Modes - a disconnected actuator, and commands it must refuse.

    python3 tests/failure_modes_test.py [--exe build/BACnetExampleBASC] [--port 47821]

1. A disconnected valve actuator. ANSI/ASHRAE 135-2024 12.3.9: Reliability "provides
   an indication of whether the Present_Value or the operation of the physical output
   in question is "reliable""; 12.1 lists NO_OUTPUT, "No physical device is connected
   to the Output object"; 12.3.7: the FAULT flag of Status_Flags is "Logical TRUE (1)
   if the Reliability property is present and does not have a value of
   NO_FAULT_DETECTED". The test disconnects the Simulation's valve through its
   test-only hook (it creates the file named by CAS_EXAMPLE_TEST_ACTUATOR_FAULT_FILE):
   Analog Output 1 must read Reliability NO_OUTPUT and FAULT, still take a command
   into its Priority_Array, and the temperature must not follow it; once the file is
   deleted, NO_FAULT_DETECTED, no FAULT, and the temperature obeys the command.

2. Commands it must refuse. 15.9.1.3.1 (WriteProperty) - "The value provided is
   outside the range of values that the property can take on." PROPERTY /
   VALUE_OUT_OF_RANGE: a setpoint outside Min_Pres_Value .. Max_Pres_Value, a Binary
   Output value other than 0 / 1, a Multi-State Output state outside
   1..Number_Of_States; "The property is not writable." PROPERTY /
   WRITE_ACCESS_DENIED: Present_Value of an input. Nothing refused may move anything.
"""
import sys
import time

import basc_setup as setup
from basc_setup import (ANALOG_INPUT, ANALOG_OUTPUT, BINARY_INPUT, BINARY_OUTPUT, MULTI_STATE_INPUT,
                       MULTI_STATE_OUTPUT, acked)
import wiretest
from wiretest import PROPERTY_PRIORITY_ARRAY, application_enumerated, application_real, application_unsigned, \
    record, wait_until

# The Simulation checks the valve once a second; allow that, plus the round trip.
FAULT_NOTICED_SECONDS = 3.0
STILL_WATCH_SECONDS = 3.0   # long enough for a connected valve to move 3 C


def health(actuator):
    return actuator.value(ANALOG_OUTPUT, setup.PROPERTY_RELIABILITY), \
        actuator.value(ANALOG_OUTPUT, setup.PROPERTY_STATUS_FLAGS)


def disconnected_valve(actuator, fault_file):
    settled = wait_until(lambda: actuator.value(ANALOG_INPUT) == setup.ANALOG_OUTPUT_DEFAULT, 4.0)
    record("Control: a connected valve - Reliability NO_FAULT_DETECTED, Status_Flags all FALSE, temperature at 20.0",
           health(actuator) == (setup.NO_FAULT_DETECTED, setup.STATUS_FLAGS_NORMAL) and settled,
           f"read {health(actuator)}, temperature {actuator.value(ANALOG_INPUT)}")

    fault_file.touch()
    noticed = wait_until(lambda: actuator.value(ANALOG_OUTPUT, setup.PROPERTY_RELIABILITY) == setup.NO_OUTPUT,
                         FAULT_NOTICED_SECONDS)
    record(f"Valve disconnected: Analog Output 1 Reliability reads NO_OUTPUT within {FAULT_NOTICED_SECONDS:.0f} s",
           noticed, f"read {health(actuator)[0]}")
    record("Valve disconnected: Status_Flags FAULT is TRUE (IN_ALARM, OVERRIDDEN, OUT_OF_SERVICE FALSE)",
           health(actuator)[1] == setup.STATUS_FLAGS_FAULT, f"read {health(actuator)[1]}")
    answer = actuator.command(ANALOG_OUTPUT, application_real(26.0), priority=8)
    record("Valve disconnected: WriteProperty(26.0, priority 8) is still accepted - Present_Value 26.0",
           acked(answer) and actuator.value(ANALOG_OUTPUT) == 26.0, answer.describe())
    time.sleep(STILL_WATCH_SECONDS)
    record(f"Valve disconnected: the temperature does not follow ({STILL_WATCH_SECONDS:.0f} s later, still 20.0)",
           actuator.value(ANALOG_INPUT) == setup.ANALOG_OUTPUT_DEFAULT, f"read {actuator.value(ANALOG_INPUT)}")
    record("Valve disconnected: the other outputs are not faulted (Binary Output 1 Status_Flags all FALSE)",
           actuator.value(BINARY_OUTPUT, setup.PROPERTY_STATUS_FLAGS) == setup.STATUS_FLAGS_NORMAL)

    setup.remove(fault_file)
    repaired = wait_until(lambda: actuator.value(ANALOG_OUTPUT, setup.PROPERTY_RELIABILITY) == setup.NO_FAULT_DETECTED,
                          FAULT_NOTICED_SECONDS)
    record(f"Valve reconnected: Reliability back to NO_FAULT_DETECTED within {FAULT_NOTICED_SECONDS:.0f} s",
           repaired, f"read {health(actuator)[0]}")
    record("Valve reconnected: Status_Flags all FALSE again", health(actuator)[1] == setup.STATUS_FLAGS_NORMAL,
           f"read {health(actuator)[1]}")
    reached = wait_until(lambda: actuator.value(ANALOG_INPUT) == 26.0, 6 / setup.VALVE_RATE + 2.5)
    record("Valve reconnected: the temperature now climbs to the command it held, 26.0", reached,
           f"read {actuator.value(ANALOG_INPUT)}")
    actuator.relinquish(ANALOG_OUTPUT, priority=8)
    # Let the temperature settle back at Relinquish_Default before the refusals, which
    # check that nothing moves.
    wait_until(lambda: actuator.value(ANALOG_INPUT) == setup.ANALOG_OUTPUT_DEFAULT, 6 / setup.VALVE_RATE + 2.5)


def refused(actuator, label, output, value_octets, expected_error, unchanged):
    """Write `value_octets` to `output` at priority 8; expect `expected_error` and nothing to change."""
    before = [actuator.value(*read) for read in unchanged]
    answer = actuator.command(output, value_octets, priority=8)
    record(f"{label} -> Error PROPERTY / {'VALUE_OUT_OF_RANGE' if expected_error == setup.ERROR_CODE_VALUE_OUT_OF_RANGE else 'WRITE_ACCESS_DENIED'}",
           answer.error == (setup.ERROR_CLASS_PROPERTY, expected_error), answer.describe())
    time.sleep(1.5)
    after = [actuator.value(*read) for read in unchanged]
    record(f"... and nothing moved ({', '.join(described(read) for read in unchanged)} as before)",
           before == after, f"before {before}, after {after}")


def described(read):
    """'Present_Value' / 'Priority_Array[8]' of an output, or the feedback input, for a check's name."""
    if read[0][0] in (setup.OBJECT_TYPE_ANALOG_OUTPUT, setup.OBJECT_TYPE_BINARY_OUTPUT,
                      setup.OBJECT_TYPE_MULTI_STATE_OUTPUT):
        return "Present_Value" if len(read) == 1 else f"Priority_Array[{read[2]}]"
    return "the input"


def refusals(actuator):
    record("Analog Output 1 serves its setpoint range: Min_Pres_Value 10.0, Max_Pres_Value 30.0",
           (actuator.value(ANALOG_OUTPUT, setup.PROPERTY_MIN_PRES_VALUE),
            actuator.value(ANALOG_OUTPUT, setup.PROPERTY_MAX_PRES_VALUE)) == (setup.MIN_PRES_VALUE, setup.MAX_PRES_VALUE))
    analog = [(ANALOG_OUTPUT,), (ANALOG_OUTPUT, PROPERTY_PRIORITY_ARRAY, 8), (ANALOG_INPUT,)]
    refused(actuator, "Analog Output 1 setpoint 35.0 (above Max_Pres_Value)", ANALOG_OUTPUT, application_real(35.0),
            setup.ERROR_CODE_VALUE_OUT_OF_RANGE, analog)
    refused(actuator, "Analog Output 1 setpoint 5.0 (below Min_Pres_Value)", ANALOG_OUTPUT, application_real(5.0),
            setup.ERROR_CODE_VALUE_OUT_OF_RANGE, analog)
    refused(actuator, "Binary Output 1 value 2 (a BACnetBinaryPV is 0 or 1)", BINARY_OUTPUT, application_enumerated(2),
            setup.ERROR_CODE_VALUE_OUT_OF_RANGE,
            [(BINARY_OUTPUT,), (BINARY_OUTPUT, PROPERTY_PRIORITY_ARRAY, 8), (BINARY_INPUT,)])
    multi_state = [(MULTI_STATE_OUTPUT,), (MULTI_STATE_OUTPUT, PROPERTY_PRIORITY_ARRAY, 8), (MULTI_STATE_INPUT,)]
    refused(actuator, "Multi-State Output 1 state 4 (it has 3)", MULTI_STATE_OUTPUT, application_unsigned(4),
            setup.ERROR_CODE_VALUE_OUT_OF_RANGE, multi_state)
    refused(actuator, "Multi-State Output 1 state 0 (states start at 1)", MULTI_STATE_OUTPUT, application_unsigned(0),
            setup.ERROR_CODE_VALUE_OUT_OF_RANGE, multi_state)
    refused(actuator, "Analog Input 1 Present_Value 50.0 (an input is not commandable)", ANALOG_INPUT,
            application_real(50.0), setup.ERROR_CODE_WRITE_ACCESS_DENIED, [(ANALOG_INPUT,)])


def main():
    args = setup.parser(__doc__).parse_args()
    fault_file = setup.fault_file_path(args.port)
    setup.remove(fault_file)
    example = setup.start_actuator(args, fault_file)
    actuator = setup.Actuator(args)
    try:
        disconnected_valve(actuator, fault_file)
        refusals(actuator)
    finally:
        setup.remove(fault_file)
        actuator.close()
        example.stop()
        if not all(wiretest.results.RESULTS):
            example.keep_log()
    return wiretest.summary()


if __name__ == "__main__":
    sys.exit(main())
