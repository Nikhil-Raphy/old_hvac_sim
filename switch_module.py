"""Switch module driver

Make sure i2c is enabled in raspi-config
"""

import os
import sys
import time
from typing import List

from service_logging import log
from flask import Response, make_response

from switch_module_configurations import SwitchModuleConfigurations
from constants import AquastatBoardMode, AquastatState

try:
    import smbus2 as smbus
except ImportError as e:
    log.info("Failed to import smbus.")


class SwitchModule:
    # generally kept 0x as addresses/registers and 0b as data

    # interrupts (not used so far)
    # IC1:INTA1
    # IC1:INTA2
    # IC2:INTB5
    # IC2:INTB6
    # IC2:INTB7

    # slave address part of control byte/device opcode, the final 0/1 for write/read is added by smbus functions (by
    # left shifting and possibly adding 1)
    # IC1 = 0b0100000  # 0100 -> fixed bits; 000 -> A2, A1, A0
    # IC2 = 0b0100001  # 0100 -> fixed bits; 001 -> A2, A1, A0
    IC1 = 0x21
    IC2 = 0x20

    # NOTE: set up for configuration register with BANK=0 (default setting, A and B addresses are sequential)

    # GPIO direction registers
    IODIRA = 0x00  # address of register assigning gpio pins in A to input or output
    IODIRB = 0x01  # address of register assigning gpio pins in B to input or output

    # GPIO input polarity
    IPOLA = 0x02
    IPOLB = 0x03

    # GPIO registers
    GPIOA = 0x12
    GPIOB = 0x13

    # latch registers
    OLATA = 0x14
    OLATB = 0x15

    IC1_GPIOA_DATA = 0b00000000
    IC1_GPIOB_DATA = 0b00000000
    IC2_GPIOA_DATA = 0b00000000
    IC2_GPIOB_DATA = 0b00000000

    # add params: model, has_pek, has_rh (some configs of these are invalid)
    def __init__(self, model, has_pek=False, has_rh=False, has_rc=True, in_phase=True, acc_minus=False):

        log.info("Initializing Switch Module")
        self.model = model
        self.has_pek = has_pek
        self.has_rh = has_rh
        self.SwitchModuleConfigurations = SwitchModuleConfigurations(
            model, has_pek, has_rh, has_rc, in_phase, acc_minus
        )
        self.bus = smbus.SMBus(1)

        # set all GPIOs to output
        self.bus.write_byte_data(self.IC1, self.IODIRA, 0b00000000)
        self.bus.write_byte_data(self.IC1, self.IODIRB, 0b00000000)
        self.bus.write_byte_data(self.IC2, self.IODIRA, 0b00000000)
        self.bus.write_byte_data(self.IC2, self.IODIRB, 0b00000000)

        # set all GPIOs to zero (disconnect all terminals)
        self.cleanup()

    def __enter__(self):
        """Context manager entry point"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - automatic cleanup

        :param exc_type: Exception type if any
        :param exc_val: Exception value if any
        :param exc_tb: Exception traceback if any

        :Returns: False to propagate exceptions, True to suppress
        """
        self.terminate_bus()
        return False  # Never suppress exceptions in HVAC control

    def terminate_bus(self):
        """Cleanup method"""
        self.bus.close()

    def _write_pin_data_to_registers(self):
        """Turns on pins, closing relays. DOES NOT consider necessary order of opening and closing relays"""
        time.sleep(1)
        self.bus.write_byte_data(self.IC1, self.GPIOA, self.IC1_GPIOA_DATA)
        self.bus.write_byte_data(self.IC1, self.GPIOB, self.IC1_GPIOB_DATA)
        self.bus.write_byte_data(self.IC2, self.GPIOA, self.IC2_GPIOA_DATA)
        self.bus.write_byte_data(self.IC2, self.GPIOB, self.IC2_GPIOB_DATA)

    # can't do a nice | operation to write to pins since pins are distributed
    # and some use same registers on different I/O expanders
    def _add_pins_to_pin_data(self, pins):
        """Prepares pins to be turned on. DOES NOT turn any pins on/off. DOES NOT consider if pins were already on."""
        for pin in pins:
            if self.SwitchModuleConfigurations.BANK[pin] == "IC1_GPIOA":
                self.IC1_GPIOA_DATA |= self.SwitchModuleConfigurations.DATA[pin]
            elif self.SwitchModuleConfigurations.BANK[pin] == "IC1_GPIOB":
                self.IC1_GPIOB_DATA |= self.SwitchModuleConfigurations.DATA[pin]
            elif self.SwitchModuleConfigurations.BANK[pin] == "IC2_GPIOA":
                self.IC2_GPIOA_DATA |= self.SwitchModuleConfigurations.DATA[pin]
            elif self.SwitchModuleConfigurations.BANK[pin] == "IC2_GPIOB":
                self.IC2_GPIOB_DATA |= self.SwitchModuleConfigurations.DATA[pin]

    def _remove_pins_from_pin_data(self, pins):
        """Prepares pins to be turned off. DOES NOT turn any pins on/off. DOES NOT consider if pins were already off."""
        # AND's the complement, which has all 1's and one 0 at pin to turn off that pin
        for pin in pins:
            if self.SwitchModuleConfigurations.BANK[pin] == "IC1_GPIOA":
                self.IC1_GPIOA_DATA &= ~self.SwitchModuleConfigurations.DATA[pin]
            elif self.SwitchModuleConfigurations.BANK[pin] == "IC1_GPIOB":
                self.IC1_GPIOB_DATA &= ~self.SwitchModuleConfigurations.DATA[pin]
            elif self.SwitchModuleConfigurations.BANK[pin] == "IC2_GPIOA":
                self.IC2_GPIOA_DATA &= ~self.SwitchModuleConfigurations.DATA[pin]
            elif self.SwitchModuleConfigurations.BANK[pin] == "IC2_GPIOB":
                self.IC2_GPIOB_DATA &= ~self.SwitchModuleConfigurations.DATA[pin]

    def _remove_all_pins_from_pin_data(self):
        """Prepares all pins to be turned off. DOES NOT turn any pins on/off.
        DOES NOT consider if pins were already off."""
        self.IC1_GPIOA_DATA = 0b00000000
        self.IC1_GPIOB_DATA = 0b00000000
        self.IC2_GPIOA_DATA = 0b00000000
        self.IC2_GPIOB_DATA = 0b00000000

    def _remove_non_power_pins_from_pin_data(self):
        """Prepares all non power pins to be turned off. DOES NOT turn any pins on/off.
        DOES NOT consider if pins were already off."""
        self.IC1_GPIOA_DATA = 0b00000000
        self.IC1_GPIOB_DATA = 0b00000000 | 0b00000100
        self.IC2_GPIOA_DATA = 0b00000000
        self.IC2_GPIOB_DATA = 0b00000000

    def _log_register_bank_data(self):
        """Reads the data on all registers and logs it"""
        log.info(f"Bank IC1_GPIOA: {self.bus.read_byte_data(self.IC1, self.GPIOA):>08b}")
        log.info(f"Bank IC1_GPIOB: {self.bus.read_byte_data(self.IC1, self.GPIOB):>08b}")
        log.info(f"Bank IC2_GPIOA: {self.bus.read_byte_data(self.IC2, self.GPIOA):>08b}")
        log.info(f"Bank IC2_GPIOB: {self.bus.read_byte_data(self.IC2, self.GPIOB):>08b}")

    def _read_pins(self) -> List:
        """Reads the IC pins of the switch module and determines which pins are activated on the switch module

        :return: list of pins that are currently activated on the switch module
        """
        # reads and logs each pin
        self._log_register_bank_data()

        # reads each pin and determines if the pin has been turned on or not to determine its config
        config = []
        for key, val in self.SwitchModuleConfigurations.DATA_IC1_GPA.items():
            if (self.bus.read_byte_data(self.IC1, self.GPIOA) & val) == val:
                config.append(key)
        for key, val in self.SwitchModuleConfigurations.DATA_IC1_GPB.items():
            if (self.bus.read_byte_data(self.IC1, self.GPIOB) & val) == val:
                config.append(key)
        for key, val in self.SwitchModuleConfigurations.DATA_IC2_GPA.items():
            if (self.bus.read_byte_data(self.IC2, self.GPIOA) & val) == val:
                config.append(key)
        for key, val in self.SwitchModuleConfigurations.DATA_IC2_GPB.items():
            if (self.bus.read_byte_data(self.IC2, self.GPIOB) & val) == val:
                config.append(key)
        log.info(f"HVACSim currently configured with: {config}")

        return config

    def read_config(self) -> Response:
        """Reads the current HVACSim configuration

        :return: status code and HTTP code pertaining to result of the _read_pins function
            200 - Success
        """
        current_config = " ".join(self._read_pins())
        return make_response(current_config, 200)

    def read_config_str(self) -> str:
        """Reads the current HVACSim configuration

        :return: string of HVACSim config
        """
        current_config = ", ".join(self._read_pins())
        return current_config

    def configure(self, config):
        """Clean up pins and configure switch module with new pin configuration"""
        log.info(f"Configure Switch Module with {config}")

        # confirm that configuration is valid
        pek_pins = [pin for pin in config if pin in self.SwitchModuleConfigurations.PEK_PINS]
        no_pek_pins = [pin for pin in config if pin in self.SwitchModuleConfigurations.NO_PEK_PINS]
        if pek_pins and no_pek_pins:
            log.info("Invalid pin configuration detected (PEK and NO_PEK pins)")
            raise ValueError(f"pek pins: {pek_pins}, cannot be used with no_pek pins: {no_pek_pins}")
        athena_pins = [pin for pin in config if pin in self.SwitchModuleConfigurations.ATHENA_PINS]
        not_athena_pins = [pin for pin in config if pin in self.SwitchModuleConfigurations.NOT_ATHENA_PINS]
        if athena_pins and not_athena_pins:
            log.info("Invalid pin configuration detected (ATHENA and NOT_ATHENA pins)")
            raise ValueError(f"athena pins: {athena_pins}, cannot be used with not_athena pins:{not_athena_pins}")
        pek_plus = [pin for pin in config if pin in self.SwitchModuleConfigurations.PEK_PLUS]
        if pek_pins and pek_plus:
            log.info("Invalid pin configuration detected (PEK_PLUS and PEK pins")
            raise ValueError(f"pek_plus pin: {pek_plus}, cannot be used with pek pins: {pek_pins}")

        # reset all lines (will turn off tstat)
        self.cleanup()
        time.sleep(1)

        log.info("Configuring non-power pins")
        # set non power lines first (so not switching with possibly high
        # current running through)
        used_main_power_pins = [pin for pin in config if pin in self.SwitchModuleConfigurations.MAIN_POWER_PINS]
        self._add_pins_to_pin_data(config)
        self._remove_pins_from_pin_data(used_main_power_pins)
        self._write_pin_data_to_registers()

        time.sleep(1)

        log.info("Configuring power pins")
        # set power pins and let power go through board
        self._add_pins_to_pin_data(used_main_power_pins)
        self._write_pin_data_to_registers()

        log.info("Fully configured")
        self._read_pins()

    # MAKE SURE THIS IS CALLED
    def cleanup(self):
        """Clear GPIO connections and stop power from going to the thermostat"""
        log.info("Cleanup Switch Module")
        # Adding delay before reading the current relay state
        time.sleep(1)
        if self._read_pins():
            #  stop power going through board, concentrates any damage on power switching relays
            log.info("Clean up power pins")
            self._remove_pins_from_pin_data(self.SwitchModuleConfigurations.MAIN_POWER_PINS)
            self._write_pin_data_to_registers()
            self._log_register_bank_data()

            # Adding delay for relays to switch properly
            time.sleep(1)

            # reset rest of lines
            log.info("Clean up non-power pins")
            # self._remove_non_power_pins_from_pin_data()
            self._remove_all_pins_from_pin_data()
            self._write_pin_data_to_registers()
            self._log_register_bank_data()
            time.sleep(1)
        log.info("Fully cleaned")

    def start_aquastat_mode(self) -> Response:
        """Starts aquastat mode

        :return: HTTP message + status code pertaining to result of start aquastat function
            200 - Success
            417 - Expectation Failed
        """
        # AttisPro does not need S22 to be High, if it is High for AttisPro, it can cause issues
        if self.has_pek or self.has_rh or self.model in ["athena", "artemis", "attisRetail, attisPro"]:
            return make_response(f"Aquastat cannot be started if PEK/Rh is enabled or Device is {self.model}", 417)

        if self.current_mode() == AquastatBoardMode.ON:
            return make_response("Aquastat mode already started")

        # Activating S22_AQUA
        self.IC2_GPIOA_DATA |= self.SwitchModuleConfigurations.DATA["S22_AQUA"] + self.bus.read_byte_data(
            self.IC2, self.GPIOA
        )
        self.bus.write_byte_data(self.IC2, self.GPIOA, self.IC2_GPIOA_DATA)

        if self.current_mode() == AquastatBoardMode.OFF:
            return make_response("Hardware couldn't activate aquastat mode", 417)

        return make_response("Aquastat mode started", 200)

    def end_aquastat_mode(self) -> Response:
        """Ends aquastat mode

        :return: HTTP message + status code pertaining to result of end aquastat function
            200 - Success
            417 - Expectation Failed
        """
        # AttisPro does not need S22 to be High, hence does not require to lower it
        if self.current_mode() == AquastatBoardMode.OFF:
            return make_response("Aquastat mode already disabled", 200)

        # Deactivating S22_AQUA and S23_TOGGLE
        self.IC2_GPIOA_DATA &= ~(
            self.SwitchModuleConfigurations.DATA["S22_AQUA"] + self.SwitchModuleConfigurations.DATA["S23_TOGGLE"]
        )

        # Delay execution for 10ms to allow for DPDT relay to open
        time.sleep(0.01)
        self.bus.write_byte_data(self.IC2, self.GPIOA, self.IC2_GPIOA_DATA)

        if self.current_mode() == AquastatBoardMode.ON or self.current_state() == AquastatState.CLOSED:
            return make_response("Hardware couldn't deactivate aquastat mode", 417)

        return make_response("Aquastat mode ended", 200)

    def open_aquastat(self) -> Response:
        """Opens aquastat

        :return: HTTP message + status code pertaining to result of the open aquastat function
            200 - Success
            417 - Expectation Failed
            428 - Precondition Required
        """
        # AttisPro does not need S22 to be High, if it is High for AttisPro, it can cause issues
        if self.model != "attisPro" and self.current_mode() == AquastatBoardMode.OFF:
            return make_response("Aquastat mode is disabled, unable to open aquastat", 428)

        if self.current_state() == AquastatState.OPEN:
            return make_response("Aquastat already opened", 200)

        # Activating S23_TOGGLE
        self.IC2_GPIOA_DATA &= ~self.SwitchModuleConfigurations.DATA["S23_TOGGLE"]
        self.bus.write_byte_data(self.IC2, self.GPIOA, self.IC2_GPIOA_DATA)

        if self.current_state() == AquastatState.CLOSED:
            return make_response("Hardware couldn't open aquastat", 417)

        return make_response("Aquastat is now open", 200)

    def close_aquastat(self) -> Response:
        """Closes aquastat

        :return: HTTP message + status code pertaining to result of the close aquastat function
            200 - Success
            417 - Expectation Failed
            428 - Precondition Required
        """
        # AttisPro does not need S22 to be High, if it is High for AttisPro, it can cause issues
        if self.model != "attisPro" and self.current_mode() == AquastatBoardMode.OFF:
            return make_response("Aquastat mode is disabled, unable to close aquastat", 428)
        if self.current_state() == AquastatState.CLOSED:
            return make_response("Aquastat already closed", 200)

        # Deactivating S23_TOGGLE
        self.IC2_GPIOA_DATA |= self.SwitchModuleConfigurations.DATA["S23_TOGGLE"]

        # Delay execution for 10ms to allow for relay to close
        time.sleep(0.01)
        self.bus.write_byte_data(self.IC2, self.GPIOA, self.IC2_GPIOA_DATA)

        if self.current_state() == AquastatState.OPEN:
            return make_response("Hardware couldn't close Aquastat", 417)

        return make_response("Aquastat is now closed", 200)

    def current_mode(self) -> str:
        """Returns a string with the current mode (on / off)

        :return: current aquastat mode
        """

        if (
            self.bus.read_byte_data(self.IC2, self.GPIOA) & self.SwitchModuleConfigurations.DATA["S22_AQUA"]
            == self.SwitchModuleConfigurations.DATA["S22_AQUA"]
        ):
            return AquastatBoardMode.ON
        return AquastatBoardMode.OFF

    def current_state(self) -> str:
        """Returns a string with the current state (open / closed)

        :return: current aquastat state
        """

        if (
            self.bus.read_byte_data(self.IC2, self.GPIOA) & self.SwitchModuleConfigurations.DATA["S23_TOGGLE"]
            == self.SwitchModuleConfigurations.DATA["S23_TOGGLE"]
        ):
            return AquastatState.CLOSED
        return AquastatState.OPEN

    def get_aquastat_mode(self) -> Response:
        """Gets aquastat mode (On / Off)

        :return: status code pertaining to result of the close aquastat function
            200 - Success
        """

        if self.current_mode() == AquastatBoardMode.ON:
            return make_response(AquastatBoardMode.ON, 200)
        return make_response(AquastatBoardMode.OFF, 200)

    def get_aquastat_state(self) -> Response:
        """Gets aquastat relay state (Open / Closed)

        :return: HTTP message + status code pertaining to result of the close aquastat function
            200 - Success
        """

        if self.current_state() == AquastatState.CLOSED:
            return make_response(AquastatState.CLOSED, 200)
        return make_response(AquastatState.OPEN, 200)
