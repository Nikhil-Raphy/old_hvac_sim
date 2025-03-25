import json
import time

from service_logging import log

from sense_module_events import SenseModuleEvents
import smbus2 as smbus


class SenseModule:
    wires = [
        "PEK",
        "ACC",
        "OB",
        "W2/G3",
        "Y2/G2",
        "W1",
        "Y1",
        "G",
        "EXT1",
        "EXT2",
        "EXT3",
        "EXT4",
        "PEK_ALT",
        "TP62",
        "TP63",
        "TP64",
    ]
    # used_wires = ['ACC', 'O/B', 'W2/G3', 'Y2/G2', 'W1', 'Y1', 'G','PEK_ALT']

    # IC address for Sense module on HVAC Sims V2
    IC = 0x22

    # IO Direction
    IODIRA = 0x00
    IODIRB = 0x01

    # Input polarity for port A
    IPOLA = 0x02
    IPOLB = 0x03

    # General Purpose Input/Output
    GPIOA = 0x12
    GPIOB = 0x13

    # Output Latch
    OLATA = 0x14
    OLATB = 0x15

    # Terminals actually connected
    ENABLED_TERMINALS = 0b1111111100001000

    # Input pin to terminal mapping
    # schematic can be found here:<TBD>
    IN_NONE = 0b0000000000000000
    IN_PEK_ALT = 0b0000000000001000
    IN_G = 0b0000000100000000
    IN_Y1 = 0b0000001000000000
    IN_W1 = 0b0000010000000000
    IN_Y2 = 0b0000100000000000
    IN_W2 = 0b0001000000000000
    IN_OB = 0b0010000000000000
    IN_ACC = 0b0100000000000000
    IN_PEK = 0b1000000000000000
    IN_G2 = IN_Y2  # G2 (medium speed fan) can be configured on the Y2 terminal for supporting devices
    IN_G3 = IN_W2  # G3 (high speed fan) can be configured on the W2 terminal for supporting devices
    IN_OB_ART = IN_W2  # Only for Artemis W2 and O/B share the same terminal
    IN_G3_ART = IN_PEK_ALT  # Only for Artemis G3 shares PEK+ terminal
    IN_ACC_ART = IN_PEK_ALT  # Only for Artemis Acc+ is linked to PEK+ terminal

    # Terminals not currently used in hardware
    IN_TP64 = 0b0000000000000001
    IN_TP63 = 0b0000000000000010
    IN_TP62 = 0b0000000000000100
    IN_EXT4 = 0b0000000000010000
    IN_EXT3 = 0b0000000000100000
    IN_EXT2 = 0b0000000001000000
    IN_EXT1 = 0b0000000010000000

    _current_event = 0b0000000000000000
    _expected_event = 0b0000000000000000

    events = SenseModuleEvents()

    def __init__(self):
        log.info("Initializing sense module")
        self.bus = smbus.SMBus(1)
        # set ports A and B as input
        self.bus.write_byte_data(self.IC, self.IODIRA, 0b11111111)
        self.bus.write_byte_data(self.IC, self.IODIRB, 0b11111111)

        # Reverse the polarity of input pins so that 1 = ON. By default 0 = ON
        self.bus.write_byte_data(self.IC, self.IPOLA, 0b00000000)
        self.bus.write_byte_data(self.IC, self.IPOLB, 0b00000000)

    def __del__(self):
        self.bus.close()

    def _update_current_event(self):
        """Private function to read bus data, then update the current event."""
        current_event_a = self.bus.read_byte_data(self.IC, self.GPIOA)
        current_event_b = self.bus.read_byte_data(self.IC, self.GPIOB)
        self._current_event = current_event_a | current_event_b << 8

    def log_relay_states(self, timeout: int, delta: float):
        """Logs the current and expected relay state into the arb_server_logs

        :param timeout: max number of seconds to wait for current event
        :param delta: elapsed time that has passed
        """
        ce = "{0:016b}".format(self._current_event)
        ee = "{0:016b}".format(self._expected_event)
        log.info(
            f"Current state: ACC={ce[1]} OB={ce[2]} W2/G3={ce[3]} Y2/G2={ce[4]} W1={ce[5]} "
            f"Y1={ce[6]} G={ce[7]} PEK_ALT={ce[12]} "
        )
        log.info(
            f"Wait for state: ACC={ee[1]} OB={ee[2]} W2/G3={ee[3]} Y2/G2={ee[4]} W1={ee[5]} "
            f"Y1={ee[6]} G={ee[7]} PEK_ALT={ee[12]}"
        )
        log.info(f"Expected (Max) time: {timeout} Elapsed time: {round(delta)}\n")

    def _wait_for_condition(self, timeout: int) -> bool:
        """Private function to block until expected event occurs or timeout condition is reached

        :param timeout: max number of seconds to wait for current event
        :return: True if event occured, False otherwise
        """
        start = time.time()
        last_print_time = 0
        last_event = self._current_event
        while True:
            self._update_current_event()
            current_event = self._current_event
            delta = time.time() - start

            if last_event != current_event:
                log.info("RELAY STATE CHANGE")
                last_print_time = delta
                last_event = current_event
                self.log_relay_states(timeout, delta)
            elif (delta - last_print_time) > 10:
                last_print_time = delta
                self.log_relay_states(timeout, delta)
            if self._current_event == self._expected_event:
                log.info("event matched in {:.2f} s".format(delta))
                return True
            if delta >= timeout:
                break
            time.sleep(2)
        return False

    def wait_for_event(self, event: int, timeout: int = 0) -> bool:
        """Block until a specific event occurs

        If timeout is not specified or if it is 0, the function acts as a simple check
        :param event: relay state event represented in binary, each bit representing a relay
        :param timeout: max number of seconds to wait for current event
        :return: True if event occured, False otherwise
        """
        self._expected_event = event
        ee = "{0:016b}".format(self._expected_event)
        log.info(
            f"Wait for state: ACC={ee[1]} OB={ee[2]} W2/G3={ee[3]} Y2/G2={ee[4]} W1={ee[5]} "
            f"Y1={ee[6]} G={ee[7]} PEK_ALT={ee[12]}"
        )
        return self._wait_for_condition(timeout)

    def get_relay_states(self):
        """Provides a list of relay states formattes as a JSON for protocols processing

        :return: JSON list
        """
        self._update_current_event()
        ce = "{0:016b}".format(self._current_event)
        relay_mapping = {1: "ACC", 2: "OB", 3: "W2/G3", 4: "Y2/G2", 5: "W1", 6: "Y1", 7: "G", 12: "PEK_ALT"}

        relay_states = {}
        for pin in relay_mapping:
            relay_states[relay_mapping[pin]] = bool(int(ce[pin]))
        return json.dumps(relay_states)