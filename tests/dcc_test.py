#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
# Public-domain example code (CC0) - see ../LICENSE.
"""B-ASC Wire Test: a management station silences the controller and lets it speak again (DM-DCC-B).

    python3 tests/dcc_test.py [--exe build/BACnetExampleBASC] [--port 47821]

ANSI/ASHRAE 135-2024 Annex L.4.3, the B-ASC addition to a B-SA: "Ability to respond
to communication control messages". Cl. 16.1.2: with DISABLE_INITIATION "the
responding BACnet-user shall discontinue the initiation of messages except for I-Am
requests issued in accordance with the Who-Is service procedure ... Communication
shall be disabled in this manner until either the 'Time Duration' has expired or a
valid DeviceCommunicationControl (with 'Enable/Disable' = ENABLE) ... is received."

What the controller initiates is its I-Am heartbeat (main.cpp section 2d), one every
5 s. The test is a management station (a Python BACnet client) that:

    1. watches the heartbeat run (the control);
    2. sends DeviceCommunicationControl with a wrong password, with none, and with the
       deprecated DISABLE: each refused (cl. 16.1.1.3.1 - SECURITY / PASSWORD_FAILURE,
       SERVICES / SERVICE_REQUEST_DENIED), and the heartbeat keeps running;
    3. sends DISABLE_INITIATION: the heartbeat stops, but a ReadProperty, a
       WriteProperty and a Who-Is are still answered - "disable initiation", not
       "disable";
    4. sends ENABLE: the heartbeat comes back;
    5. sends DISABLE_INITIATION for 1 minute and sends nothing more: the heartbeat
       stops and comes back by itself when the minute is up (K.5.6: "Support for
       requests of a limited duration is required").

The example is started with --dcc-password, so every accepted request carries it.

The heartbeat is a subnet broadcast. On Linux/macOS the test hears it on the wire
(wiretest.broadcast_listener). Windows cannot share the example's port to listen
(common/ binds it SO_EXCLUSIVEADDRUSE), so there - and on every platform as a second
witness - the test counts the example's own "TX ... (broadcast) ... I-Am" console
lines, which common/ prints for each datagram it actually sends and never for one the
stack refused.
"""
import os
import re
import sys
import time

import basc_setup as setup
from basc_setup import ANALOG_INPUT, ANALOG_OUTPUT, acked
import wiretest
from wiretest import alarm, record

PASSWORD = "letmein"
HEARTBEAT_SECONDS = 5
RUNNING_WATCH = 11.0       # long enough for at least two heartbeats
SILENT_WATCH = 11.0        # two heartbeat periods with none
ERROR_CLASS_SECURITY, ERROR_CODE_PASSWORD_FAILURE = 4, 26
ERROR_CLASS_SERVICES, ERROR_CODE_SERVICE_REQUEST_DENIED = 5, 29
DCC_DISABLE = 1            # deprecated (cl. 16.1.1.1.2); refused at Protocol_Revision >= 20


class Heartbeats:
    """Counts the controller's unsolicited I-Am broadcasts from a mark onwards: on the wire
    (Linux/macOS) and in its console's TX lines (every platform)."""

    def __init__(self, example, port):
        self.example = example
        self.console_line = re.compile(rf"TX \d+ bytes to [\d.]+:{port} \(broadcast\)[^\n]*I-Am")
        broadcast_ip = wiretest.broadcast_address(example.output(), port)
        self.listener = wiretest.broadcast_listener(broadcast_ip, port) if os.name != "nt" and broadcast_ip else None
        self.mark()

    def mark(self):
        self.console_offset = len(self.example.output())
        if self.listener is not None:
            self.listener.clear()

    def counts(self):
        """(on the wire or None on Windows, in the console) since the mark."""
        console = len(self.console_line.findall(self.example.output()[self.console_offset:]))
        if self.listener is None:
            return None, console
        self.listener.collect(0.05)
        wire = sum(1 for frame in self.listener.frames
                   if wiretest.i_am_device_instance(frame.payload) == setup.DEVICE_INSTANCE)
        return wire, console

    def watch(self, seconds):
        self.mark()
        time.sleep(seconds)
        return self.counts()

    def close(self):
        if self.listener is not None:
            self.listener.close()


def running(counts, at_least):
    wire, console = counts
    return console >= at_least and (wire is None or wire >= at_least)


def silent(counts):
    wire, console = counts
    return console == 0 and (wire is None or wire == 0)


def text(counts):
    wire, console = counts
    return f"{console} in the console" + ("" if wire is None else f", {wire} on the wire")


def dcc(client, port, enable_disable, password=None, minutes=None):
    return client.request(lambda invoke_id: alarm.device_communication_control_request(
        invoke_id, enable_disable, password, minutes), port, timeout=setup.REQUEST_TIMEOUT)


def who_is_answered(client, port):
    """A unicast Who-Is for this device gets its I-Am back (sent up to 3 times, visibly)."""
    for attempt in range(3):
        if attempt:
            print("[RETRY] Who-Is got no I-Am in 1.0 s - sent again", flush=True)
        client.frames.clear()
        client.send(wiretest.bvlc(wiretest.npdu(wiretest.who_is(setup.DEVICE_INSTANCE, setup.DEVICE_INSTANCE))), port)
        if client.wait_for(lambda frame: wiretest.i_am_device_instance(frame.payload) == setup.DEVICE_INSTANCE, 1.0):
            return True
    return False


def main():
    args = setup.parser(__doc__).parse_args()
    example = wiretest.start(args.exe, ["--port", args.port, "--dcc-password", PASSWORD], "controller")
    controller = setup.Actuator(args)
    client = controller.client
    heartbeats = Heartbeats(example, args.port)
    print(f"(heartbeat witnessed {'on the wire and ' if heartbeats.listener else ''}in the console)", flush=True)
    try:
        counts = heartbeats.watch(RUNNING_WATCH)
        record(f"Control: the I-Am heartbeat runs - at least 2 in {RUNNING_WATCH:.0f} s", running(counts, 2),
               text(counts))

        # Refused requests: nothing changes.
        answer = dcc(client, args.port, alarm.DCC_DISABLE_INITIATION, "wrong")
        record("DISABLE_INITIATION with a wrong password -> Error SECURITY / PASSWORD_FAILURE",
               answer.error == (ERROR_CLASS_SECURITY, ERROR_CODE_PASSWORD_FAILURE), answer.describe())
        answer = dcc(client, args.port, alarm.DCC_DISABLE_INITIATION)
        record("DISABLE_INITIATION with no password -> Error SECURITY / PASSWORD_FAILURE",
               answer.error == (ERROR_CLASS_SECURITY, ERROR_CODE_PASSWORD_FAILURE), answer.describe())
        answer = dcc(client, args.port, DCC_DISABLE, PASSWORD)
        record("DISABLE (deprecated) with the right password -> Error SERVICES / SERVICE_REQUEST_DENIED",
               answer.error == (ERROR_CLASS_SERVICES, ERROR_CODE_SERVICE_REQUEST_DENIED), answer.describe())
        counts = heartbeats.watch(RUNNING_WATCH)
        record("... and after all three refusals the heartbeat still runs", running(counts, 2), text(counts))

        # DISABLE_INITIATION: silent, but still answering.
        answer = dcc(client, args.port, alarm.DCC_DISABLE_INITIATION, PASSWORD)
        record("DISABLE_INITIATION (indefinite) with the right password -> SimpleACK", acked(answer), answer.describe())
        record("... a ReadProperty is still answered (Analog Input 1 Present_Value)",
               isinstance(controller.value(ANALOG_INPUT), float), f"read {controller.value(ANALOG_INPUT)}")
        answer = controller.command(ANALOG_OUTPUT, wiretest.application_real(22.0), priority=8)
        record("... a WriteProperty is still answered and obeyed (Analog Output 1 = 22.0 @ 8)",
               acked(answer) and controller.value(ANALOG_OUTPUT) == 22.0, answer.describe())
        controller.relinquish(ANALOG_OUTPUT, priority=8)
        record("... a Who-Is is still answered with an I-Am (cl. 16.1.2 exempts it)", who_is_answered(client, args.port))
        # Watch from here: the Who-Is answer above is an I-Am too, and must not count.
        counts = heartbeats.watch(SILENT_WATCH)
        record(f"... and the heartbeat stops: no unsolicited I-Am in {SILENT_WATCH:.0f} s", silent(counts), text(counts))

        # ENABLE: back.
        answer = dcc(client, args.port, alarm.DCC_ENABLE, PASSWORD)
        record("ENABLE with the right password -> SimpleACK", acked(answer), answer.describe())
        counts = heartbeats.watch(RUNNING_WATCH)
        record(f"... and the heartbeat is back - at least 2 in {RUNNING_WATCH:.0f} s", running(counts, 2), text(counts))

        # A time-limited DISABLE_INITIATION ends by itself.
        answer = dcc(client, args.port, alarm.DCC_DISABLE_INITIATION, PASSWORD, minutes=1)
        disabled_at = time.monotonic()
        record("DISABLE_INITIATION for 1 minute -> SimpleACK", acked(answer), answer.describe())
        counts = heartbeats.watch(50.0)
        record("... no unsolicited I-Am for the first 50 s", silent(counts), text(counts))
        heartbeats.mark()
        wiretest.wait_until(lambda: running(heartbeats.counts(), 1), 60 + 2 * HEARTBEAT_SECONDS + 2 - 50, interval=0.5)
        counts = heartbeats.counts()
        record("... and the heartbeat comes back by itself once the minute is up (no ENABLE sent)",
               running(counts, 1), f"{text(counts)}, {time.monotonic() - disabled_at:.0f} s after the request")
        record("... not before it is up", time.monotonic() - disabled_at >= 59.0,
               f"first heartbeat seen {time.monotonic() - disabled_at:.0f} s after the request")
    finally:
        heartbeats.close()
        controller.close()
        example.stop()
        if not all(wiretest.results.RESULTS):
            example.keep_log()
    return wiretest.summary()


if __name__ == "__main__":
    sys.exit(main())
