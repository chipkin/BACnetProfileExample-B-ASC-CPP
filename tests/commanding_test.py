#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
# Public-domain example code (CC0) - see ../LICENSE.
"""B-ASC Wire Test: a commanded output does what the winning command says (DS-WP-B, cl. 19).

    python3 tests/commanding_test.py [--exe build/BACnetExampleBASC] [--port 47821]

ANSI/ASHRAE 135-2024 Annex L.4.3, Data Sharing, as for a B-SA: "Ability to allow
modification of some or all of its BACnet objects by another device". A controller
that stores the command and does nothing with it answers every WriteProperty and
still modifies nothing, so this test checks each output twice over: its BACnet side
(Present_Value, Priority_Array, Current_Command_Priority - cl. 19.2) and its feedback
input, which the actuator Simulation (main.cpp section 1b) drives from the winning
command:

    Analog Output 1 "Chartreuse" (setpoint)  ->  Analog Input 1 "Bronze" (temperature)
    Binary Output 1 "Fuchsia" (relay)        ->  Binary Input 1 "Emerald" (feedback contact)
    Multi-State Output 1 "Indigo" (speed)    ->  Multi-State Input 1 "Hot Pink" (drive speed)

Each output is commanded at a high and a low priority: the lower-priority command
must change nothing; relinquishing the higher one hands the output to the lower
one; relinquishing that returns it to Relinquish_Default (cl. 19.2.1: "a NULL value
... is written to the Priority_Array at the specified priority").

The Peer is a Python BACnet client on 127.0.0.1 - what a controller commanding the
actuator does on a real site.
"""
import sys
import time

import basc_setup as setup
from basc_setup import (ANALOG_INPUT, ANALOG_OUTPUT, BINARY_INPUT, BINARY_OUTPUT, MULTI_STATE_INPUT,
                       MULTI_STATE_OUTPUT, acked)
import wiretest
from wiretest import (PROPERTY_CURRENT_COMMAND_PRIORITY, PROPERTY_PRIORITY_ARRAY, application_enumerated,
                      application_real, application_unsigned, record, wait_until)

FEEDBACK_SECONDS = 2.5   # a binary / multi-state feedback follows within one Simulation tick


def output_state(actuator, output):
    """(Present_Value, Current_Command_Priority) of an output."""
    return actuator.value(output), actuator.value(output, PROPERTY_CURRENT_COMMAND_PRIORITY)


def follows(actuator, feedback, expected, seconds):
    """True once the feedback input reads `expected` (polled for up to `seconds`)."""
    return wait_until(lambda: actuator.value(feedback) == expected, seconds)


def temperature_reaches(actuator, setpoint):
    """Poll Analog Input 1 until it reads `setpoint`; return (reached, readings on the way)."""
    start_reading = actuator.value(ANALOG_INPUT)
    distance = abs(setpoint - start_reading) if isinstance(start_reading, float) else 10.0
    readings = [start_reading]

    def check():
        readings.append(actuator.value(ANALOG_INPUT))
        return readings[-1] == setpoint
    reached = wait_until(check, distance / setup.VALVE_RATE + 2.5, interval=0.25)
    return reached, readings


def analog_output(actuator):
    print("--- Analog Output 1 (setpoint) -> Analog Input 1 (temperature)")
    reached, readings = temperature_reaches(actuator, setup.ANALOG_OUTPUT_DEFAULT)
    record("Control: nothing commanded - Present_Value is Relinquish_Default 20.0, Current_Command_Priority NULL,"
           " and the temperature settles at 20.0",
           output_state(actuator, ANALOG_OUTPUT) == (setup.ANALOG_OUTPUT_DEFAULT, None) and reached,
           f"read {output_state(actuator, ANALOG_OUTPUT)}, temperature {readings[-1]}")

    answer = actuator.command(ANALOG_OUTPUT, application_real(24.0), priority=8)
    record("WriteProperty(24.0, priority 8) is accepted", acked(answer), answer.describe())
    record("... Present_Value 24.0, Priority_Array[8] 24.0, Current_Command_Priority 8",
           output_state(actuator, ANALOG_OUTPUT) == (24.0, 8)
           and actuator.value(ANALOG_OUTPUT, PROPERTY_PRIORITY_ARRAY, 8) == 24.0,
           f"read {output_state(actuator, ANALOG_OUTPUT)}")
    reached, readings = temperature_reaches(actuator, 24.0)
    record("... the temperature climbs to 24.0 (the valve obeys the command)", reached, f"read {readings}")
    record("... gradually - at least one reading on the way between 20.0 and 24.0 (a valve, not a copy)",
           any(isinstance(reading, float) and 20.0 < reading < 24.0 for reading in readings), f"read {readings}")

    answer = actuator.command(ANALOG_OUTPUT, application_real(19.0), priority=12)
    record("WriteProperty(19.0, priority 12) is accepted into Priority_Array[12]",
           acked(answer) and actuator.value(ANALOG_OUTPUT, PROPERTY_PRIORITY_ARRAY, 12) == 19.0, answer.describe())
    record("... but priority 8 still wins: Present_Value 24.0, Current_Command_Priority 8",
           output_state(actuator, ANALOG_OUTPUT) == (24.0, 8), f"read {output_state(actuator, ANALOG_OUTPUT)}")
    time.sleep(2.5)
    record("... and the temperature stays at 24.0 (the losing command moves nothing)",
           actuator.value(ANALOG_INPUT) == 24.0, f"read {actuator.value(ANALOG_INPUT)}")

    answer = actuator.relinquish(ANALOG_OUTPUT, priority=8)
    record("Relinquish priority 8 (NULL) is accepted; Priority_Array[8] reads NULL",
           acked(answer) and actuator.value(ANALOG_OUTPUT, PROPERTY_PRIORITY_ARRAY, 8) is None, answer.describe())
    record("... priority 12 wins now: Present_Value 19.0, Current_Command_Priority 12",
           output_state(actuator, ANALOG_OUTPUT) == (19.0, 12), f"read {output_state(actuator, ANALOG_OUTPUT)}")
    reached, readings = temperature_reaches(actuator, 19.0)
    record("... and the temperature falls to 19.0", reached, f"read {readings}")

    answer = actuator.relinquish(ANALOG_OUTPUT, priority=12)
    record("Relinquish priority 12: Present_Value back to Relinquish_Default 20.0, Current_Command_Priority NULL",
           acked(answer) and output_state(actuator, ANALOG_OUTPUT) == (setup.ANALOG_OUTPUT_DEFAULT, None),
           f"read {output_state(actuator, ANALOG_OUTPUT)}")
    reached, readings = temperature_reaches(actuator, setup.ANALOG_OUTPUT_DEFAULT)
    record("... and the temperature returns to 20.0", reached, f"read {readings}")


def two_priorities(actuator, label, output, feedback, encode, default, high, low, high_priority, low_priority):
    """Command `output` at a high and a low priority and check the feedback input follows the winner."""
    print(f"--- {label}")
    record(f"Control: nothing commanded - Present_Value is Relinquish_Default {default}, feedback {default}",
           output_state(actuator, output) == (default, None) and follows(actuator, feedback, default, FEEDBACK_SECONDS),
           f"read {output_state(actuator, output)}, feedback {actuator.value(feedback)}")
    answer = actuator.command(output, encode(low), priority=low_priority)
    record(f"WriteProperty({low}, priority {low_priority}): Present_Value {low}, Current_Command_Priority {low_priority}",
           acked(answer) and output_state(actuator, output) == (low, low_priority), answer.describe())
    record(f"... the feedback follows to {low}", follows(actuator, feedback, low, FEEDBACK_SECONDS),
           f"read {actuator.value(feedback)}")
    answer = actuator.command(output, encode(high), priority=high_priority)
    record(f"WriteProperty({high}, priority {high_priority}) wins over priority {low_priority}: Present_Value {high}",
           acked(answer) and output_state(actuator, output) == (high, high_priority), answer.describe())
    record(f"... the feedback follows to {high}", follows(actuator, feedback, high, FEEDBACK_SECONDS),
           f"read {actuator.value(feedback)}")
    answer = actuator.relinquish(output, priority=high_priority)
    record(f"Relinquish priority {high_priority}: priority {low_priority} wins again - Present_Value {low}",
           acked(answer) and output_state(actuator, output) == (low, low_priority),
           f"read {output_state(actuator, output)}")
    record(f"... the feedback follows back to {low}", follows(actuator, feedback, low, FEEDBACK_SECONDS),
           f"read {actuator.value(feedback)}")
    answer = actuator.relinquish(output, priority=low_priority)
    record(f"Relinquish priority {low_priority}: Present_Value back to Relinquish_Default {default}",
           acked(answer) and output_state(actuator, output) == (default, None),
           f"read {output_state(actuator, output)}")
    record(f"... the feedback follows back to {default}", follows(actuator, feedback, default, FEEDBACK_SECONDS),
           f"read {actuator.value(feedback)}")


def main():
    args = setup.parser(__doc__).parse_args()
    example = setup.start_actuator(args)
    actuator = setup.Actuator(args)
    try:
        analog_output(actuator)
        two_priorities(actuator, "Binary Output 1 (relay) -> Binary Input 1 (feedback contact)",
                       BINARY_OUTPUT, BINARY_INPUT, application_enumerated, setup.BINARY_OUTPUT_DEFAULT,
                       high=0, low=1, high_priority=4, low_priority=8)
        two_priorities(actuator, "Multi-State Output 1 (speed) -> Multi-State Input 1 (drive speed)",
                       MULTI_STATE_OUTPUT, MULTI_STATE_INPUT, application_unsigned,
                       setup.MULTI_STATE_OUTPUT_DEFAULT, high=2, low=3, high_priority=10, low_priority=16)
    finally:
        actuator.close()
        example.stop()
        if not all(wiretest.results.RESULTS):
            example.keep_log()
    return wiretest.summary()


if __name__ == "__main__":
    sys.exit(main())
