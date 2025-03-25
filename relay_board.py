import RPi.GPIO

from sense_module_events import SenseModuleEvents
from service_logging import log

from sense_module import SenseModule
from switch_module import SwitchModule
from switch_module_configurations import SwitchModuleConfigurations

RPI_EXECUTE_PIN = 18
DBG_LED = 17
DUT_DET = 27
FLASH_SEL = 22
I2C_EN = 0
FTDI_RSTn = 5
USB_HUB_RST = 6
OUT2_RSTn = 13
OUT1_RSTn = 19
IN_RSTn = 26
AP_RSTn = 23
AP_BOOTn = 24
VOLTAGE_SEL = 25
VBUS_CON = 12


class RelayBoard:

    def __init__(self, model, has_pek=False, has_rh=False, has_rc=True, in_phase=True, acc_minus=False):
        RPi.GPIO.setmode(RPi.GPIO.BCM)
        RPi.GPIO.setup(DBG_LED, RPi.GPIO.OUT)
        RPi.GPIO.setup(DUT_DET, RPi.GPIO.IN)
        RPi.GPIO.setup(FLASH_SEL, RPi.GPIO.OUT)
        RPi.GPIO.setup(I2C_EN, RPi.GPIO.OUT)
        RPi.GPIO.setup(OUT2_RSTn, RPi.GPIO.OUT)
        RPi.GPIO.setup(OUT1_RSTn, RPi.GPIO.OUT)
        RPi.GPIO.setup(IN_RSTn, RPi.GPIO.OUT)
        RPi.GPIO.setup(AP_RSTn, RPi.GPIO.OUT)
        RPi.GPIO.setup(AP_BOOTn, RPi.GPIO.OUT)
        RPi.GPIO.setup(VOLTAGE_SEL, RPi.GPIO.OUT)
        RPi.GPIO.setup(VBUS_CON, RPi.GPIO.OUT)
        RPi.GPIO.setup(FTDI_RSTn, RPi.GPIO.OUT)
        RPi.GPIO.setup(USB_HUB_RST, RPi.GPIO.OUT)

        RPi.GPIO.output(VOLTAGE_SEL, RPi.GPIO.LOW)
        RPi.GPIO.output(DBG_LED, RPi.GPIO.LOW)
        RPi.GPIO.output(I2C_EN, RPi.GPIO.HIGH)
        RPi.GPIO.output(OUT2_RSTn, RPi.GPIO.HIGH)
        RPi.GPIO.output(OUT1_RSTn, RPi.GPIO.HIGH)
        RPi.GPIO.output(IN_RSTn, RPi.GPIO.HIGH)
        RPi.GPIO.output(FTDI_RSTn, RPi.GPIO.HIGH)
        RPi.GPIO.output(USB_HUB_RST, RPi.GPIO.LOW)
        RPi.GPIO.output(FLASH_SEL, RPi.GPIO.LOW)
        self.sense_module = SenseModule()
        self.switch_module = SwitchModule(model, has_pek, has_rh, has_rc, in_phase, acc_minus)
        self.configurations = SwitchModuleConfigurations(model, has_pek, has_rh, has_rc, in_phase, acc_minus)
        self.events = SenseModuleEvents()
        RPi.GPIO.setup(RPI_EXECUTE_PIN, RPi.GPIO.OUT)
        RPi.GPIO.output(RPI_EXECUTE_PIN, RPi.GPIO.HIGH)

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
        self.cleanup()
        return False  # Never suppress exceptions in HVAC control

    def cleanup(self) -> None:
        """Cleanup all resources"""
        log.debug("Initiating RelayBoard cleanup")

        """Cleanup method"""
        try:
            self.switch_module.cleanup()
        finally:
            RPi.GPIO.setmode(RPi.GPIO.BCM)
            RPi.GPIO.setup(RPI_EXECUTE_PIN, RPi.GPIO.OUT)
            RPi.GPIO.output(RPI_EXECUTE_PIN, RPi.GPIO.LOW)
            RPi.GPIO.cleanup()
            self.switch_module.terminate_bus()
            self.sense_module.cleanup()

    def wait_for_event(self, event, timeout):
        """Block until a specific event occurs. If timeout is not
        specified or if it is 0, the function acts as a simple check.
        Returns True if the event occurred and False otherwise.
        """
        return self.sense_module.wait_for_event(event, timeout)


    def configure(self, config):
        """Clean up switch module pins and reconfigure with new
        pin configuration"""
        self.switch_module.configure(config)
