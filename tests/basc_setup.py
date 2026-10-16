# SPDX-License-Identifier: CC0-1.0
# Public-domain example code (CC0) - see ../LICENSE.
"""What B-ASC's Wire Tests share: this application specific controller's numbers, and starting it.

The setup, all on one host:

    test client (127.0.0.1, ephemeral UDP port) - the Peer: a Python BACnet client
        |  BACnet/IP, unicast
    BACnetExampleBASC   UDP --port   Analog / Binary / Multi-State Output 1 (commanded),
                                    Analog / Binary / Multi-State Input 1 (their feedback)

The Peer plays the part of whatever commands and manages a controller on a real site - a
controller, an operator workstation, a commissioning tool. It writes and reads the
actuator over the wire exactly as those would; nothing reaches into the example any
other way, except the Simulation's one test-only hook: the file named by
CAS_EXAMPLE_TEST_ACTUATOR_FAULT_FILE, whose existence disconnects the simulated valve.
"""
import argparse
import os
import sys
import tempfile
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY))

import wiretest  # noqa: E402  (the vendored harness at the repository root)

# Match main.cpp.
DEVICE_INSTANCE = 389003
OBJECT_TYPE_ANALOG_OUTPUT, OBJECT_TYPE_BINARY_OUTPUT, OBJECT_TYPE_MULTI_STATE_OUTPUT = 1, 4, 14
ANALOG_INPUT = (wiretest.OBJECT_TYPE_ANALOG_INPUT, 1)             # "Bronze"     - the temperature
BINARY_INPUT = (wiretest.OBJECT_TYPE_BINARY_INPUT, 1)             # "Emerald"    - the relay's feedback
MULTI_STATE_INPUT = (wiretest.OBJECT_TYPE_MULTI_STATE_INPUT, 1)   # "Hot Pink"   - the drive's speed
ANALOG_OUTPUT = (OBJECT_TYPE_ANALOG_OUTPUT, 1)                    # "Chartreuse" - the setpoint
BINARY_OUTPUT = (OBJECT_TYPE_BINARY_OUTPUT, 1)                    # "Fuchsia"    - the relay
MULTI_STATE_OUTPUT = (OBJECT_TYPE_MULTI_STATE_OUTPUT, 1)          # "Indigo"     - the speed

# The outputs' Relinquish_Default and the setpoint range (main.cpp); the Simulation
# (main.cpp section 1b) moves the temperature up to 1.0 C a second toward the setpoint.
ANALOG_OUTPUT_DEFAULT, BINARY_OUTPUT_DEFAULT, MULTI_STATE_OUTPUT_DEFAULT = 20.0, 0, 1
MIN_PRES_VALUE, MAX_PRES_VALUE = 10.0, 30.0
VALVE_RATE = 1.0
ACTUATOR_FAULT_FILE_VARIABLE = "CAS_EXAMPLE_TEST_ACTUATOR_FAULT_FILE"

# Every request: 0.6 s for an answer, then up to 3 resends (Actuator below).
REQUEST_TIMEOUT = 0.6
RETRIES = 3

# Properties (cl. 12; numbers from cl. 21 BACnetPropertyIdentifier).
PROPERTY_MAX_PRES_VALUE = 65
PROPERTY_MIN_PRES_VALUE = 69
PROPERTY_RELIABILITY = 103
PROPERTY_RELINQUISH_DEFAULT = 104
PROPERTY_STATUS_FLAGS = 111

# BACnetReliability (cl. 21), BACnetStatusFlags bit order {IN_ALARM, FAULT, OVERRIDDEN,
# OUT_OF_SERVICE} (cl. 12.3.7), Error classes / codes (cl. 18).
NO_FAULT_DETECTED, NO_OUTPUT = 0, 6
STATUS_FLAGS_NORMAL = [False, False, False, False]
STATUS_FLAGS_FAULT = [False, True, False, False]
ERROR_CLASS_PROPERTY = 2
ERROR_CODE_VALUE_OUT_OF_RANGE, ERROR_CODE_WRITE_ACCESS_DENIED = 37, 40


def parser(description):
    arguments = argparse.ArgumentParser(description=description, formatter_class=argparse.RawDescriptionHelpFormatter)
    arguments.add_argument("--exe", default=str(wiretest.default_exe(REPOSITORY, "BACnetExampleBASC")),
                           help="path to BACnetExampleBASC (default: build/BACnetExampleBASC)")
    arguments.add_argument("--port", type=int, default=47821,
                           help="the controller's UDP port (default 47821)")
    return arguments


def fault_file_path(port):
    """Where this run's disconnected-valve file lives (one per port, so parallel runs do not share it)."""
    return Path(tempfile.gettempdir()) / f"basc-actuator-fault-{port}"


def start_actuator(args, fault_file=None):
    """Start the example; with `fault_file`, its disconnected-valve hook watches that path."""
    environment = {ACTUATOR_FAULT_FILE_VARIABLE: str(fault_file)} if fault_file else None
    return wiretest.start(args.exe, ["--port", args.port], "controller", environment)


class Actuator:
    """The smart actuator as the Peer sees it: a wiretest.Client aimed at its port. A request
    unanswered after REQUEST_TIMEOUT is sent again, up to RETRIES times, as a BACnet client
    does (Number_Of_APDU_Retries); each resend prints [RETRY], so a lost request is visible,
    not hidden. A busy Windows host loses the odd UDP datagram even on loopback, where an
    answer takes milliseconds - so the timeout is short and a loss costs well under a second."""

    def __init__(self, args):
        self.client = wiretest.Client(retries=RETRIES)
        self.port = args.port

    def read(self, object_identifier, property_identifier, array_index=None):
        return self.client.read_property(self.port, *object_identifier, property_identifier, array_index,
                                        timeout=REQUEST_TIMEOUT)

    def value(self, object_identifier, property_identifier=wiretest.PROPERTY_PRESENT_VALUE, array_index=None):
        """The decoded value (NULL -> None), or 'no answer' / 'error' so a comparison fails readably."""
        answer = self.read(object_identifier, property_identifier, array_index)
        if not answer.answered:
            return "no answer"
        return answer.value if answer.ok else "error"

    def command(self, object_identifier, value_octets, priority):
        """WriteProperty(Present_Value, value, priority)."""
        return self.client.write_property(self.port, *object_identifier, wiretest.PROPERTY_PRESENT_VALUE,
                                          value_octets, priority, timeout=REQUEST_TIMEOUT)

    def relinquish(self, object_identifier, priority):
        """WriteProperty(Present_Value, NULL, priority) - cl. 19.2.1."""
        return self.command(object_identifier, wiretest.application_null(), priority)

    def write(self, object_identifier, property_identifier, value_octets):
        return self.client.write_property(self.port, *object_identifier, property_identifier, value_octets,
                                          timeout=REQUEST_TIMEOUT)

    def close(self):
        self.client.close()


def acked(answer):
    return answer.answered and answer.frame.pdu_type == wiretest.PDU_SIMPLE_ACK


def remove(path):
    try:
        os.remove(path)
    except FileNotFoundError:
        pass
