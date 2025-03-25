
class SwitchModuleConfigurations(object):
    """Stores pin level configuration data for different equipment combinations.

    If there is a pek option for that wire, then the suffixes PEK or NO_PEK
    are added. Otherwise if a wire cannot be used with pek or if it doesn't
    care if there's pek, then there is no suffix.

    Ensure that any new pins for new configurations are added to power_pins,
    pek/no_pek lists, athena/not_athena lists, in order to protect from unsafe
    configurations

    Distribute new pins over both GPIO expanders to minimize current draw
    """
    BANK = {
        "RH_OUT_PHASE": "IC1_GPIOA",  # IC1:GPA0
        "TP1": "IC1_GPIOA",  # IC1:GPA1  # No Use in hvac sim V2
        "TP2": "IC1_GPIOA",  # No Use in hvac sim V2
        "TP3": "IC1_GPIOA", # No Use in hvac sim V2
        "TP4": "IC1_GPIOA", # No Use in hvac sim V2
        "S8_G_PEK_NOT_ATHENA": "IC1_GPIOA",
        "S7_G_PEK_ATHENA": "IC1_GPIOA",
        "S6_G_NO_PEK": "IC1_GPIOA",

        "S1_RC_PEK": "IC1_GPIOB",  # IC1:GPB0
        "TP5": "IC1_GPIOB",        # No Use in hvac sim V2
        "S3_RC": "IC1_GPIOB",
        "S4_RH": "IC1_GPIOB",
        "TP6": "IC1_GPIOB",        # No Use in hvac sim V2
        "S21_RH": "IC1_GPIOB",
        "S24_RH_ONLY": "IC1_GPIOB",  # Tstat power only through RH (Athena only)
        "PEK_ALT": "IC1_GPIOB", # PEK+ G3+ACC Artemis Only

        "TP7": "IC2_GPIOA",  # IC2:GPA0  No Use in hvac sim V2
        "S23_TOGGLE": "IC2_GPIOA",  # IC2:GPA1 Toggle Aquastat
        "S22_AQUA": "IC2_GPIOA",  # Connect Aquastat
        "S20_ACCM": "IC2_GPIOA",
        "S19_ACCP": "IC2_GPIOA",
        "S18_OB": "IC2_GPIOA",
        "S17_W2_G3": "IC2_GPIOA",
        "S16_Y2_G2": "IC2_GPIOA",

        "S11_Y1_NO_PEK": "IC2_GPIOB",  # IC2:GPB0
        "S12_Y_PEK_ATHENA": "IC2_GPIOB",  # IC2:GPB1
        "S13_Y_PEK_NOT_ATHENA": "IC2_GPIOB",
        "S14_W1_NO_PEK": "IC2_GPIOB",
        "S15_W_PEK": "IC2_GPIOB",
        "TP8": "IC2_GPIOB",            # No Use in hvac sim V2
        "TP9": "IC2_GPIOB",            # No Use in hvac sim V2
        "TP10": "IC2_GPIOB"}           # No Use in hvac sim V2

    DATA = {
        "RH_OUT_PHASE":        0b00000001,  # IC1:GPA0
        "TP1":                 0b00000010,  # IC1:GPA1      # Not Used
        "TP2":                 0b00000100,  # IC1:GPA2      # Not Used
        "TP3":                 0b00001000,  # IC1:GPA3      # Not Used
        "TP4":                 0b00010000,  # IC1:GPA4      # Not Used
        "S8_G_PEK_NOT_ATHENA": 0b00100000,  # IC1:GPA5      # G_KT TO C_TS
        "S7_G_PEK_ATHENA":     0b01000000,  # IC1:GPA6      # G_KT TO G_TS
        "S6_G_NO_PEK":         0b10000000,  # IC1:GPA7      # G_EQ TO G_TS

        "S1_RC_PEK":    0b00000001,  # IC1:GPB0
        "TP5":          0b00000010,  # IC1:GPB1      # Not Used
        "S3_RC":        0b00000100,  # IC1:GPB2      # RC_TS
        "S4_RH":        0b00001000,  # IC1:GPB3
        "TP6":          0b00010000,  # IC1:GPB4      # Not Used
        "S21_RH":       0b00100000,  # IC1:GPB5      # RH_TS
        "S24_RH_ONLY":  0b01000000,  # IC1:GPB6
        "PEK_ALT":      0b10000000,  # IC1:GPB7

        "TP7":         0b00000001,  # IC2:GPA0
        "S23_TOGGLE":   0b00000010,  # IC2:GPA1      # Toggle Aquastat
        "S22_AQUA":     0b00000100,  # IC2:GPA2      # Connect Aquastat
        "S20_ACCM":     0b00001000,  # IC2:GPA3      # RH_ACC TO ACCM_TS
        "S19_ACCP":     0b00010000,  # IC2:GPA4      # ACCP_EQ TO ACCP_TS
        "S18_OB":       0b00100000,  # IC2:GPA5      # OB_EQ TO OB_TS
        "S17_W2_G3":    0b01000000,  # IC2:GPA6      # W2_EQ TO W2_TS
        "S16_Y2_G2":    0b10000000,  # IC2:GPA7      # Y2_EQ TO Y2_TS

        "S11_Y1_NO_PEK":        0b00000001,  # IC2:GPB0      # Y1_EQ TO Y1_TS
        "S12_Y_PEK_ATHENA":     0b00000010,  # IC2:GPB1      # Y_KT TO Y1_TS
        "S13_Y_PEK_NOT_ATHENA": 0b00000100,  # IC2:GPB2     # Y_KT TO PEK_TS
        "S14_W1_NO_PEK":        0b00001000,  # IC2:GPB3      # W1_EQ TO W1_TS
        "S15_W_PEK":            0b00010000,  # IC2:GPB4      # W_KT TO W1_TS
        "TP8":                  0b00100000,  # IC2:GPB5      # Not Used
        "TP9":                  0b01000000,  # IC2:GPB6      # Not Used
        "TP10":                 0b10000000}  # IC2:GPB7      # Not Used

    DATA_IC1_GPA = {
        "RH_OUT_PHASE":        0b00000001,  # IC1:GPA0
        "TP1":                 0b00000010,  # IC1:GPA1      # Not Used
        "TP2":                 0b00000100,  # IC1:GPA2      # Not Used
        "TP3":                 0b00001000,  # IC1:GPA3      # Not Used
        "TP4":                 0b00010000,  # IC1:GPA4      # Not Used
        "S8_G_PEK_NOT_ATHENA": 0b00100000,  # IC1:GPA5      # G_KT TO C_TS
        "S7_G_PEK_ATHENA":     0b01000000,  # IC1:GPA6      # G_KT TO G_TS
        "S6_G_NO_PEK":         0b10000000,  # IC1:GPA7      # G_EQ TO G_TS
    }

    DATA_IC1_GPB = {
        "S1_RC_PEK":    0b00000001,  # IC1:GPB0
        "TP5":          0b00000010,  # IC1:GPB1      # Not Used
        "S3_RC":        0b00000100,  # IC1:GPB2      # RC_TS
        "S4_RH":        0b00001000,  # IC1:GPB3      # RH_ACC To RC_PWR, Athena Rh powered Only
        "TP6":          0b00010000,  # IC1:GPB4      # Not Used
        "S21_RH":       0b00100000,  # IC1:GPB5      # RH_TS hvacsim v2
        "S24_RH_ONLY":  0b01000000,  # IC1:GPB6
        "PEK_ALT":      0b10000000,  # IC1:GPB7
    }

    DATA_IC2_GPA = {
        "TP7":          0b00000001,  # IC2:GPA0      # Not Used
        "S23_TOGGLE":   0b00000010,  # IC2:GPA1
        "S22_AQUA":     0b00000100,  # IC2:GPA2
        "S20_ACCM":     0b00001000,  # IC2:GPA3      # RH_ACC TO ACCM_TS
        "S19_ACCP":     0b00010000,  # IC2:GPA4      # ACCP_EQ TO ACCP_TS
        "S18_OB":       0b00100000,  # IC2:GPA5      # OB_EQ TO OB_TS
        "S17_W2_G3":    0b01000000,  # IC2:GPA6      # W2_EQ TO W2_TS
        "S16_Y2_G2":    0b10000000,  # IC2:GPA7      # Y2_EQ TO Y2_TS
    }

    DATA_IC2_GPB = {
        "S11_Y1_NO_PEK":        0b00000001,  # IC2:GPB0      # Y1_EQ TO Y1_TS
        "S12_Y_PEK_ATHENA":     0b00000010,  # IC2:GPB1      # Y_KT TO Y1_TS
        "S13_Y_PEK_NOT_ATHENA": 0b00000100,  # IC2:GPB2     # Y_KT TO PEK_TS
        "S14_W1_NO_PEK":        0b00001000,  # IC2:GPB3      # W1_EQ TO W1_TS
        "S15_W_PEK":            0b00010000,  # IC2:GPB4      # W_KT TO W1_TS
        "TP8":                  0b00100000,  # IC2:GPB5      # Not Used
        "TP9":                  0b01000000,  # IC2:GPB6      # Not Used
        "TP10":                 0b10000000   # IC2:GPB7      # Not Used
    }

    # control if main power going through switch module's relays
    MAIN_POWER_PINS = ["S3_RC", "S21_RH", "S24_RH_ONLY"]
    # pins used for PEK configurations. Cannot be used at the same time as no_pek pins or RH
    PEK_PINS = ["S8_G_PEK_NOT_ATHENA", "S7_G_PEK_ATHENA", "S1_RC_PEK", "S12_Y_PEK_ATHENA",
                "S13_Y_PEK_NOT_ATHENA", "S15_W_PEK"]
    # pins used for NO_PEK configurations, including RH. Cannot be used at the same time as PEK pins
    NO_PEK_PINS = ["S6_G_NO_PEK", "S11_Y1_NO_PEK", "S14_W1_NO_PEK", "S4_RH", "PEK_ALT"]
    # athena specific pins
    ATHENA_PINS = ["S7_G_PEK_ATHENA", "S12_Y_PEK_ATHENA"]
    # not-athena specific pins
    NOT_ATHENA_PINS = ["S8_G_PEK_NOT_ATHENA", "S13_Y_PEK_NOT_ATHENA"]
    # Multi-purpose pek pin
    PEK_PLUS = ["PEK_ALT"]

    def __init__(self, model, has_pek=False, has_rh=False, has_rc=True, in_phase=True, acc_minus=False):
        # TODO: KEEP TRACK OF ALLOWABLE CONFIGS IN NEW EQUIPMENT/NEW DEVICES
        # (after apollo)
        # rh can only replace rc as power with athena device, as of nike, need
        # to use rc
        if model != "athena" and has_rh and not has_rc:
            raise ValueError(f"Cannot power {model} with RH-only. Only athena can "
                             "be powered by RH-only")
        if has_pek and has_rh:
            raise ValueError("Cannot use PEK and power through RH")
        if not has_rh and not has_rc:
            if model == "athena":
                raise ValueError("Must have RC or RH for power")
            else:
                raise ValueError("Must have RC for power")
        # Different relay configurations to use for accessories
        if not acc_minus and model != "artemis":
            self.ACC_RELAYS = ["S19_ACCP"]
        elif not has_pek and model == "artemis":
            self.ACC_RELAYS = ["PEK_ALT"]
        else:
            self.ACC_RELAYS = ["S19_ACCP", "S20_ACCM"]

        self.FAN_2_STAGE = ["S16_Y2_G2"]
        self.FAN_3_STAGE = ["S16_Y2_G2", "S17_W2_G3"] if model != "artemis" else ["S16_Y2_G2", "PEK_ALT"]
        # W2 and OB are shared terminals in Artemis
        self.OB = ["S17_W2_G3"] if model in ["artemis", "attisRetail"] else ["S18_OB"]
        self.Y2 = ["S17_W2_G3"] if model == "attisRetail" else ["S16_Y2_G2"]

        if has_pek:
            if model == "athena":
                # Note: pek configurations without a Y1 or G wire are actually
                # invalid because of how the signals are processed.
                # W1 is optional.
                self.CONFIG_POWER = ["S1_RC_PEK", "S7_G_PEK_ATHENA", "S3_RC",
                                     "S12_Y_PEK_ATHENA"]
            else:
                self.CONFIG_POWER = ["S1_RC_PEK", "S3_RC",
                                     "S8_G_PEK_NOT_ATHENA", "S13_Y_PEK_NOT_ATHENA"]

            self.CONFIG_FAN = self.CONFIG_POWER
            self.CONFIG_FAN_2_STAGE = self.CONFIG_FAN + self.FAN_2_STAGE
            self.CONFIG_FAN_3_STAGE = self.CONFIG_FAN + self.FAN_3_STAGE

            self.CONFIG_AC_1_STAGE = self.CONFIG_FAN
            self.CONFIG_AC_1_STAGE_FAN_2_STAGE = self.CONFIG_AC_1_STAGE + self.FAN_2_STAGE
            self.CONFIG_AC_1_STAGE_FAN_3_STAGE = self.CONFIG_AC_1_STAGE + self.FAN_3_STAGE

            self.CONFIG_BO_1_STAGE = self.CONFIG_FAN + ["S15_W_PEK"]

            self.CONFIG_AC_2_STAGE = self.CONFIG_POWER + self.Y2  # No multispeed fan if >1 AC stage

            self.CONFIG_BO_1_STAGE_AC_1_STAGE = self.CONFIG_AC_1_STAGE + ["S15_W_PEK"]
            self.CONFIG_BO_1_STAGE_AC_1_STAGE_FAN_2_STAGE = self.CONFIG_BO_1_STAGE_AC_1_STAGE + self.FAN_2_STAGE
            self.CONFIG_BO_1_STAGE_AC_1_STAGE_FAN_3_STAGE = self.CONFIG_BO_1_STAGE_AC_1_STAGE + self.FAN_3_STAGE

            self.CONFIG_FN_1_STAGE = self.CONFIG_POWER + ["S15_W_PEK"]
            self.CONFIG_FN_1_STAGE_FAN_2_STAGE = self.CONFIG_FN_1_STAGE + self.FAN_2_STAGE
            self.CONFIG_FN_1_STAGE_FAN_3_STAGE = self.CONFIG_FN_1_STAGE + self.FAN_3_STAGE

            self.CONFIG_FN_1_STAGE_AC_1_STAGE = self.CONFIG_AC_1_STAGE + ["S15_W_PEK"]
            self.CONFIG_FN_1_STAGE_AC_1_STAGE_FAN_2_STAGE = self.CONFIG_FN_1_STAGE_AC_1_STAGE + self.FAN_2_STAGE
            self.CONFIG_FN_1_STAGE_AC_1_STAGE_FAN_3_STAGE = self.CONFIG_FN_1_STAGE_AC_1_STAGE + self.FAN_3_STAGE

        # If system is not using a PEK:
        else:
            # Can only reach/use this condition if thermostat is an athena:
            if has_rh and not has_rc:
                self.CONFIG_POWER = ["S24_RH_ONLY"]
            # Default: RC-only power:
            elif not has_rh and has_rc:
                self.CONFIG_POWER = ["S3_RC"]
            # Has both RH and RC, and they are in phase:
            elif has_rh and in_phase:
                self.CONFIG_POWER = ["S3_RC", "S21_RH"]
            # Has both RH and RC, and they are out of phase:
            elif has_rh and not in_phase:
                self.CONFIG_POWER = ["S3_RC", "S21_RH", "RH_OUT_PHASE"]

            # For Attis Devices, PEK+ wire will be wired to G/PEK terminal
            self.CONFIG_FAN = (self.CONFIG_POWER + ["PEK_ALT"]) if model in ["attisRetail", "attisPro"] \
                else (self.CONFIG_POWER + ["S6_G_NO_PEK"])

            self.CONFIG_FAN_2_STAGE = self.CONFIG_FAN + self.FAN_2_STAGE
            self.CONFIG_FAN_3_STAGE = self.CONFIG_FAN + self.FAN_3_STAGE

            self.CONFIG_BO_1_STAGE = self.CONFIG_POWER + ["S14_W1_NO_PEK"]  # no fan therefore no multispeed fan

            self.CONFIG_AC_1_STAGE = self.CONFIG_FAN + ["S11_Y1_NO_PEK"]
            self.CONFIG_AC_1_STAGE_FAN_2_STAGE = self.CONFIG_AC_1_STAGE + self.FAN_2_STAGE
            self.CONFIG_AC_1_STAGE_FAN_3_STAGE = self.CONFIG_AC_1_STAGE + self.FAN_3_STAGE

            self.CONFIG_BO_1_STAGE_AC_1_STAGE = self.CONFIG_AC_1_STAGE + ["S14_W1_NO_PEK"]
            self.CONFIG_BO_1_STAGE_AC_1_STAGE_FAN_2_STAGE = self.CONFIG_BO_1_STAGE_AC_1_STAGE + self.FAN_2_STAGE
            self.CONFIG_BO_1_STAGE_AC_1_STAGE_FAN_3_STAGE = self.CONFIG_BO_1_STAGE_AC_1_STAGE + self.FAN_3_STAGE

            self.CONFIG_FN_1_STAGE = self.CONFIG_FAN + ["S14_W1_NO_PEK"]
            self.CONFIG_FN_1_STAGE_FAN_2_STAGE = self.CONFIG_FN_1_STAGE + self.FAN_2_STAGE
            self.CONFIG_FN_1_STAGE_FAN_3_STAGE = self.CONFIG_FN_1_STAGE + self.FAN_3_STAGE

            self.CONFIG_FN_1_STAGE_AC_1_STAGE = self.CONFIG_BO_1_STAGE_AC_1_STAGE
            self.CONFIG_FN_1_STAGE_AC_1_STAGE_FAN_2_STAGE = self.CONFIG_BO_1_STAGE_AC_1_STAGE_FAN_2_STAGE
            self.CONFIG_FN_1_STAGE_AC_1_STAGE_FAN_3_STAGE = self.CONFIG_BO_1_STAGE_AC_1_STAGE_FAN_3_STAGE
            self.CONFIG_AC_2_STAGE = self.CONFIG_AC_1_STAGE + self.Y2  # no multi-speed fan allowed

        self.CONFIG_BO_2_STAGE = self.CONFIG_BO_1_STAGE + ["S17_W2_G3"]

        self.CONFIG_BO_1_STAGE_AC_2_STAGE = self.CONFIG_BO_1_STAGE_AC_1_STAGE + self.Y2 # no multi-speed fan allowed

        self.CONFIG_BO_2_STAGE_AC_1_STAGE = self.CONFIG_BO_1_STAGE_AC_1_STAGE + ["S17_W2_G3"]  # max fan stages = 2
        self.CONFIG_BO_2_STAGE_AC_1_STAGE_FAN_2_STAGE = self.CONFIG_BO_2_STAGE_AC_1_STAGE + self.FAN_2_STAGE

        self.CONFIG_BO_2_STAGE_AC_2_STAGE = self.CONFIG_BO_2_STAGE_AC_1_STAGE + self.Y2 # no multi-speed fan

        self.CONFIG_FN_2_STAGE = self.CONFIG_FN_1_STAGE + ["S17_W2_G3"]  # max fan stages = 2
        self.CONFIG_FN_2_STAGE_FAN_2_STAGE = self.CONFIG_FN_2_STAGE + self.FAN_2_STAGE

        self.CONFIG_FN_1_STAGE_AC_2_STAGE = self.CONFIG_FN_1_STAGE_AC_1_STAGE + self.Y2  # no multi-speed fan allowed

        self.CONFIG_FN_2_STAGE_AC_1_STAGE = self.CONFIG_FN_1_STAGE_AC_1_STAGE + ["S17_W2_G3"]  # max fan stages = 2
        self.CONFIG_FN_2_STAGE_AC_1_STAGE_FAN_2_STAGE = self.CONFIG_FN_2_STAGE_AC_1_STAGE + self.FAN_2_STAGE

        self.CONFIG_FN_2_STAGE_AC_2_STAGE = self.CONFIG_FN_2_STAGE_AC_1_STAGE + self.Y2  # no multi-speed fan

        self.CONFIG_HPCOOL_1_STAGE = self.CONFIG_AC_1_STAGE + self.OB
        self.CONFIG_HPCOOL_1_STAGE_FAN_2_STAGE = self.CONFIG_HPCOOL_1_STAGE + self.FAN_2_STAGE
        self.CONFIG_HPCOOL_1_STAGE_FAN_3_STAGE = self.CONFIG_HPCOOL_1_STAGE + self.FAN_3_STAGE

        self.CONFIG_HPCOOL_2_STAGE = self.CONFIG_HPCOOL_1_STAGE + self.Y2  # no multi-speed fan allowed

        self.CONFIG_HPHEAT_1_STAGE = self.CONFIG_HPCOOL_1_STAGE
        self.CONFIG_HPHEAT_1_STAGE_FAN_2_STAGE = self.CONFIG_HPCOOL_1_STAGE_FAN_2_STAGE
        self.CONFIG_HPHEAT_1_STAGE_FAN_3_STAGE = self.CONFIG_HPCOOL_1_STAGE_FAN_3_STAGE

        self.CONFIG_HPHEAT_2_STAGE = self.CONFIG_HPCOOL_2_STAGE  # no multi-speed fan

        self.CONFIG_HPCOOL_1_STAGE_AUX_1_STAGE = self.CONFIG_FN_1_STAGE_AC_1_STAGE + self.OB
        self.CONFIG_HPCOOL_1_STAGE_AUX_1_STAGE_FAN_2_STAGE = self.CONFIG_HPCOOL_1_STAGE_AUX_1_STAGE + self.FAN_2_STAGE
        self.CONFIG_HPCOOL_1_STAGE_AUX_1_STAGE_FAN_3_STAGE = self.CONFIG_HPCOOL_1_STAGE_AUX_1_STAGE + self.FAN_3_STAGE

        # 2 stage AUX not supported in Artemis Heat Pump configuration
        self.CONFIG_HPCOOL_1_STAGE_AUX_2_STAGE = self.CONFIG_FN_2_STAGE_AC_1_STAGE + self.OB   # max fan stages = 2
        self.CONFIG_HPCOOL_1_STAGE_AUX_2_STAGE_FAN_2_STAGE = self.CONFIG_HPCOOL_1_STAGE_AUX_2_STAGE + self.FAN_2_STAGE  # max fan stages = 2

        self.CONFIG_HPCOOL_2_STAGE_AUX_1_STAGE = self.CONFIG_HPCOOL_1_STAGE_AUX_1_STAGE + self.Y2  # no multi-speed fan allowed

        self.CONFIG_HPCOOL_2_STAGE_AUX_2_STAGE = self.CONFIG_HPCOOL_2_STAGE_AUX_1_STAGE + ["S17_W2_G3"]  # no multi-speed fan

        self.CONFIG_HPHEAT_1_STAGE_AUX_1_STAGE = self.CONFIG_HPCOOL_1_STAGE_AUX_1_STAGE
        self.CONFIG_HPHEAT_1_STAGE_AUX_1_STAGE_FAN_2_STAGE = self.CONFIG_HPCOOL_1_STAGE_AUX_1_STAGE_FAN_2_STAGE
        self.CONFIG_HPHEAT_1_STAGE_AUX_1_STAGE_FAN_3_STAGE = self.CONFIG_HPCOOL_1_STAGE_AUX_1_STAGE_FAN_3_STAGE

        self.CONFIG_HPHEAT_1_STAGE_AUX_2_STAGE = self.CONFIG_HPCOOL_1_STAGE_AUX_2_STAGE
        self.CONFIG_HPHEAT_1_STAGE_AUX_2_STAGE_FAN_2_STAGE = self.CONFIG_HPCOOL_1_STAGE_AUX_2_STAGE_FAN_2_STAGE

        self.CONFIG_HPHEAT_2_STAGE_AUX_1_STAGE = self.CONFIG_HPCOOL_2_STAGE_AUX_1_STAGE  # no multi-speed fan allowed
        self.CONFIG_HPHEAT_2_STAGE_AUX_2_STAGE = self.CONFIG_HPCOOL_2_STAGE_AUX_2_STAGE  # no multi-speed fan

        # Equipment configurations - accessories
        self.CONFIG_FAN_ACC = self.CONFIG_FAN + self.ACC_RELAYS
        self.CONFIG_FAN_ACC_2_STAGE = self.CONFIG_FAN_ACC + self.PEK_PLUS
        self.CONFIG_FAN_2_STAGE_ACC = self.CONFIG_FAN_ACC + self.FAN_2_STAGE
        self.CONFIG_FAN_2_STAGE_ACC_2_STAGE = self.CONFIG_FAN_2_STAGE_ACC + self.PEK_PLUS
        self.CONFIG_FAN_3_STAGE_ACC = self.CONFIG_FAN_ACC + self.FAN_3_STAGE
        self.CONFIG_FAN_3_STAGE_ACC_2_STAGE = self.CONFIG_FAN_3_STAGE_ACC + self.PEK_PLUS

        self.CONFIG_AC_1_STAGE_ACC = self.CONFIG_AC_1_STAGE + self.ACC_RELAYS
        self.CONFIG_AC_1_STAGE_FAN_2_STAGE_ACC = self.CONFIG_AC_1_STAGE_ACC + self.FAN_2_STAGE
        self.CONFIG_AC_1_STAGE_FAN_2_STAGE_ACC_2_STAGE = self.CONFIG_AC_1_STAGE_FAN_2_STAGE_ACC + self.PEK_PLUS
        # ACC and 3 stage fan not supported in Artemis
        self.CONFIG_AC_1_STAGE_FAN_3_STAGE_ACC = self.CONFIG_AC_1_STAGE_ACC + self.FAN_3_STAGE
        self.CONFIG_AC_1_STAGE_FAN_3_STAGE_ACC_2_STAGE = self.CONFIG_AC_1_STAGE_FAN_3_STAGE_ACC + self.PEK_PLUS

        self.CONFIG_AC_2_STAGE_ACC = self.CONFIG_AC_2_STAGE + self.ACC_RELAYS  # no multi-speed fan allowed
        self.CONFIG_AC_2_STAGE_ACC_2_STAGE = self.CONFIG_AC_2_STAGE_ACC + self.PEK_PLUS

        self.CONFIG_AC_1_STAGE_ACC_2_STAGE = self.CONFIG_AC_1_STAGE_ACC + self.PEK_PLUS

        self.CONFIG_FN_1_STAGE_ACC = self.CONFIG_FN_1_STAGE + self.ACC_RELAYS
        self.CONFIG_FN_1_STAGE_FAN_2_STAGE_ACC = self.CONFIG_FN_1_STAGE_FAN_2_STAGE + self.ACC_RELAYS
        self.CONFIG_FN_1_STAGE_FAN_3_STAGE_ACC = self.CONFIG_FN_1_STAGE_FAN_3_STAGE + self.ACC_RELAYS
        self.CONFIG_FN_1_STAGE_FAN_2_STAGE_ACC_2_STAGE = self.CONFIG_FN_1_STAGE_FAN_2_STAGE_ACC + self.PEK_PLUS
        self.CONFIG_FN_1_STAGE_FAN_3_STAGE_ACC_2_STAGE = self.CONFIG_FN_1_STAGE_FAN_3_STAGE_ACC + self.PEK_PLUS

        self.CONFIG_FN_2_STAGE_ACC = self.CONFIG_FN_2_STAGE + self.ACC_RELAYS
        self.CONFIG_FN_2_STAGE_ACC_2_STAGE = self.CONFIG_FN_2_STAGE_ACC + self.PEK_PLUS
        self.CONFIG_FN_2_STAGE_FAN_2_STAGE_ACC = self.CONFIG_FN_2_STAGE_FAN_2_STAGE + self.ACC_RELAYS

        self.CONFIG_FN_1_STAGE_ACC_2_STAGE = self.CONFIG_FN_1_STAGE_ACC + self.PEK_PLUS

        self.CONFIG_BO_1_STAGE_ACC = self.CONFIG_BO_1_STAGE + self.ACC_RELAYS
        self.CONFIG_BO_2_STAGE_ACC = self.CONFIG_BO_2_STAGE + self.ACC_RELAYS

        self.CONFIG_BO_1_STAGE_ACC_2_STAGE = self.CONFIG_BO_1_STAGE_ACC + self.PEK_PLUS
        self.CONFIG_BO_2_STAGE_ACC_2_STAGE = self.CONFIG_BO_2_STAGE_ACC + self.PEK_PLUS

        self.CONFIG_BO_1_STAGE_AC_1_STAGE_ACC = self.CONFIG_BO_1_STAGE_AC_1_STAGE + self.ACC_RELAYS
        self.CONFIG_BO_1_STAGE_AC_1_STAGE_ACC_2_STAGE = self.CONFIG_BO_1_STAGE_AC_1_STAGE_ACC + self.PEK_PLUS
        self.CONFIG_BO_1_STAGE_AC_1_STAGE_FAN_2_STAGE_ACC = self.CONFIG_BO_1_STAGE_AC_1_STAGE_ACC + self.FAN_2_STAGE
        self.CONFIG_BO_1_STAGE_AC_1_STAGE_FAN_3_STAGE_ACC = self.CONFIG_BO_1_STAGE_AC_1_STAGE_ACC + self.FAN_3_STAGE

        self.CONFIG_BO_1_STAGE_AC_2_STAGE_ACC = self.CONFIG_BO_1_STAGE_AC_2_STAGE + self.ACC_RELAYS  # no multi-speed fan
        self.CONFIG_BO_1_STAGE_AC_2_STAGE_ACC_2_STAGE = self.CONFIG_BO_1_STAGE_AC_2_STAGE_ACC + self.PEK_PLUS

        self.CONFIG_BO_2_STAGE_AC_1_STAGE_ACC = self.CONFIG_BO_2_STAGE_AC_1_STAGE + self.ACC_RELAYS
        self.CONFIG_BO_2_STAGE_AC_1_STAGE_ACC_2_STAGE = self.CONFIG_BO_2_STAGE_AC_1_STAGE_ACC + self.PEK_PLUS
        self.CONFIG_BO_2_STAGE_AC_1_STAGE_FAN_2_STAGE_ACC = self.CONFIG_BO_2_STAGE_AC_1_STAGE_ACC + self.FAN_2_STAGE

        self.CONFIG_BO_2_STAGE_AC_2_STAGE_ACC = self.CONFIG_BO_2_STAGE_AC_2_STAGE + self.ACC_RELAYS  # no multi-speed fan
        self.CONFIG_BO_2_STAGE_AC_2_STAGE_ACC_2_STAGE = self.CONFIG_BO_2_STAGE_AC_2_STAGE_ACC + self.PEK_PLUS

        # The following config is for a single accessory connected to PEK terminal

        self.CONFIG_FN_1_STAGE_AC_1_STAGE_PEK_ACC = self.CONFIG_FN_1_STAGE_AC_1_STAGE + self.PEK_PLUS
        self.CONFIG_FN_1_STAGE_AC_1_STAGE_ACC = self.CONFIG_FN_1_STAGE_AC_1_STAGE + self.ACC_RELAYS
        self.CONFIG_FN_1_STAGE_AC_1_STAGE_ACC_2_STAGE = self.CONFIG_FN_1_STAGE_AC_1_STAGE_ACC + self.PEK_PLUS
        self.CONFIG_FN_1_STAGE_AC_1_STAGE_FAN_2_STAGE_ACC = self.CONFIG_FN_1_STAGE_AC_1_STAGE_ACC + self.FAN_2_STAGE
        self.CONFIG_FN_1_STAGE_AC_1_STAGE_FAN_3_STAGE_ACC = self.CONFIG_FN_1_STAGE_AC_1_STAGE_ACC + self.FAN_3_STAGE
        self.CONFIG_FN_1_STAGE_AC_1_STAGE_FAN_2_STAGE_ACC_2_STAGE = \
            self.CONFIG_FN_1_STAGE_AC_1_STAGE_FAN_2_STAGE_ACC + self.PEK_PLUS
        self.CONFIG_FN_1_STAGE_AC_1_STAGE_FAN_3_STAGE_ACC_2_STAGE = \
            self.CONFIG_FN_1_STAGE_AC_1_STAGE_FAN_3_STAGE_ACC + self.PEK_PLUS

        self.CONFIG_FN_1_STAGE_AC_2_STAGE_ACC = self.CONFIG_FN_1_STAGE_AC_2_STAGE + self.ACC_RELAYS
        self.CONFIG_FN_1_STAGE_AC_2_STAGE_ACC_2_STAGE = self.CONFIG_FN_1_STAGE_AC_2_STAGE_ACC + self.PEK_PLUS

        self.CONFIG_FN_2_STAGE_AC_1_STAGE_ACC = self.CONFIG_FN_2_STAGE_AC_1_STAGE + self.ACC_RELAYS
        self.CONFIG_FN_2_STAGE_AC_1_STAGE_ACC_2_STAGE = self.CONFIG_FN_2_STAGE_AC_1_STAGE_ACC + self.PEK_PLUS
        self.CONFIG_FN_2_STAGE_AC_1_STAGE_FAN_2_STAGE_ACC = self.CONFIG_FN_2_STAGE_AC_1_STAGE_ACC + self.FAN_2_STAGE

        self.CONFIG_FN_2_STAGE_AC_2_STAGE_ACC = self.CONFIG_FN_2_STAGE_AC_2_STAGE + self.ACC_RELAYS
        self.CONFIG_FN_2_STAGE_AC_2_STAGE_ACC_2_STAGE = self.CONFIG_FN_2_STAGE_AC_2_STAGE_ACC + self.PEK_PLUS

        self.CONFIG_HPCOOL_1_STAGE_ACC = self.CONFIG_HPCOOL_1_STAGE + self.ACC_RELAYS
        self.CONFIG_HPCOOL_1_STAGE_ACC_2_STAGE = self.CONFIG_HPCOOL_1_STAGE_ACC + self.PEK_PLUS
        self.CONFIG_HPCOOL_1_STAGE_FAN_2_STAGE_ACC = self.CONFIG_HPCOOL_1_STAGE_ACC + self.FAN_2_STAGE
        self.CONFIG_HPCOOL_1_STAGE_FAN_3_STAGE_ACC = self.CONFIG_HPCOOL_1_STAGE_ACC + self.FAN_3_STAGE
        self.CONFIG_HPCOOL_1_STAGE_FAN_3_STAGE_ACC_2_STAGE = self.CONFIG_HPCOOL_1_STAGE_ACC + self.FAN_3_STAGE + self.PEK_PLUS

        self.CONFIG_HPCOOL_2_STAGE_ACC = self.CONFIG_HPCOOL_2_STAGE + self.ACC_RELAYS  # no multi-speed fan
        self.CONFIG_HPCOOL_2_STAGE_ACC_2_STAGE = self.CONFIG_HPCOOL_2_STAGE_ACC + self.PEK_PLUS

        self.CONFIG_HPHEAT_1_STAGE_ACC = self.CONFIG_HPHEAT_1_STAGE + self.ACC_RELAYS
        self.CONFIG_HPHEAT_1_STAGE_ACC_2_STAGE = self.CONFIG_HPHEAT_1_STAGE_ACC + self.PEK_PLUS
        self.CONFIG_HPHEAT_1_STAGE_FAN_2_STAGE_ACC = self.CONFIG_HPHEAT_1_STAGE_ACC + self.FAN_2_STAGE
        self.CONFIG_HPHEAT_1_STAGE_FAN_3_STAGE_ACC = self.CONFIG_HPHEAT_1_STAGE_ACC + self.FAN_3_STAGE

        self.CONFIG_HPHEAT_2_STAGE_ACC = self.CONFIG_HPHEAT_2_STAGE + self.ACC_RELAYS
        self.CONFIG_HPHEAT_2_STAGE_ACC_2_STAGE = self.CONFIG_HPHEAT_2_STAGE_ACC + self.PEK_PLUS

        self.CONFIG_HPCOOL_1_STAGE_AUX_1_STAGE_ACC = self.CONFIG_HPCOOL_1_STAGE_AUX_1_STAGE + self.ACC_RELAYS
        self.CONFIG_HPCOOL_1_STAGE_AUX_1_STAGE_ACC_2_STAGE = self.CONFIG_HPCOOL_1_STAGE_AUX_1_STAGE_ACC + self.PEK_PLUS
        self.CONFIG_HPCOOL_1_STAGE_AUX_1_STAGE_FAN_2_STAGE_ACC = self.CONFIG_HPCOOL_1_STAGE_AUX_1_STAGE_ACC + self.FAN_2_STAGE
        self.CONFIG_HPCOOL_1_STAGE_AUX_1_STAGE_FAN_3_STAGE_ACC = self.CONFIG_HPCOOL_1_STAGE_AUX_1_STAGE_ACC + self.FAN_3_STAGE
        self.CONFIG_HPCOOL_1_STAGE_AUX_1_STAGE_FAN_2_STAGE_ACC_2_STAGE = \
            self.CONFIG_HPCOOL_1_STAGE_AUX_1_STAGE_FAN_2_STAGE_ACC + self.PEK_PLUS
        self.CONFIG_HPCOOL_1_STAGE_AUX_1_STAGE_FAN_3_STAGE_ACC_2_STAGE = \
            self.CONFIG_HPCOOL_1_STAGE_AUX_1_STAGE_FAN_3_STAGE_ACC + self.PEK_PLUS

        self.CONFIG_HPCOOL_1_STAGE_AUX_2_STAGE_ACC = self.CONFIG_HPCOOL_1_STAGE_AUX_2_STAGE + self.ACC_RELAYS
        self.CONFIG_HPCOOL_1_STAGE_AUX_2_STAGE_ACC_2_STAGE = self.CONFIG_HPCOOL_1_STAGE_AUX_2_STAGE_ACC + self.PEK_PLUS
        self.CONFIG_HPCOOL_1_STAGE_AUX_2_STAGE_FAN_2_STAGE_ACC = self.CONFIG_HPCOOL_1_STAGE_AUX_2_STAGE_ACC + self.FAN_2_STAGE

        self.CONFIG_HPCOOL_2_STAGE_AUX_1_STAGE_ACC = self.CONFIG_HPCOOL_2_STAGE_AUX_1_STAGE + self.ACC_RELAYS
        self.CONFIG_HPCOOL_2_STAGE_AUX_1_STAGE_ACC_2_STAGE = self.CONFIG_HPCOOL_2_STAGE_AUX_1_STAGE_ACC + self.PEK_PLUS
        self.CONFIG_HPCOOL_2_STAGE_AUX_2_STAGE_ACC = self.CONFIG_HPCOOL_2_STAGE_AUX_2_STAGE + self.ACC_RELAYS
        self.CONFIG_HPCOOL_2_STAGE_AUX_2_STAGE_ACC_2_STAGE = self.CONFIG_HPCOOL_2_STAGE_AUX_2_STAGE_ACC + self.PEK_PLUS

        self.CONFIG_HPHEAT_1_STAGE_AUX_1_STAGE_ACC = self.CONFIG_HPHEAT_1_STAGE_AUX_1_STAGE + self.ACC_RELAYS
        self.CONFIG_HPHEAT_1_STAGE_AUX_1_STAGE_ACC_2_STAGE = self.CONFIG_HPHEAT_1_STAGE_AUX_1_STAGE_ACC + self.PEK_PLUS
        self.CONFIG_HPHEAT_1_STAGE_AUX_1_STAGE_FAN_2_STAGE_ACC = self.CONFIG_HPHEAT_1_STAGE_AUX_1_STAGE_ACC + self.FAN_2_STAGE
        self.CONFIG_HPHEAT_1_STAGE_AUX_1_STAGE_FAN_3_STAGE_ACC = self.CONFIG_HPHEAT_1_STAGE_AUX_1_STAGE_ACC + self.FAN_3_STAGE
        self.CONFIG_HPHEAT_1_STAGE_AUX_1_STAGE_FAN_2_STAGE_ACC_2_STAGE = self.CONFIG_HPCOOL_1_STAGE_AUX_1_STAGE_FAN_2_STAGE_ACC_2_STAGE
        self.CONFIG_HPHEAT_1_STAGE_AUX_1_STAGE_FAN_3_STAGE_ACC_2_STAGE = self.CONFIG_HPCOOL_1_STAGE_AUX_1_STAGE_FAN_3_STAGE_ACC_2_STAGE

        self.CONFIG_HPHEAT_1_STAGE_AUX_2_STAGE_ACC = self.CONFIG_HPHEAT_1_STAGE_AUX_2_STAGE + self.ACC_RELAYS
        self.CONFIG_HPHEAT_1_STAGE_AUX_2_STAGE_ACC_2_STAGE = self.CONFIG_HPHEAT_1_STAGE_AUX_2_STAGE_ACC + self.PEK_PLUS
        self.CONFIG_HPHEAT_1_STAGE_AUX_2_STAGE_FAN_2_STAGE_ACC = self.CONFIG_HPHEAT_1_STAGE_AUX_2_STAGE_ACC + self.FAN_2_STAGE

        self.CONFIG_HPHEAT_2_STAGE_AUX_1_STAGE_ACC = self.CONFIG_HPHEAT_2_STAGE_AUX_1_STAGE + self.ACC_RELAYS
        self.CONFIG_HPHEAT_2_STAGE_AUX_1_STAGE_ACC_2_STAGE = self.CONFIG_HPHEAT_2_STAGE_AUX_1_STAGE_ACC + self.PEK_PLUS
        self.CONFIG_HPHEAT_2_STAGE_AUX_2_STAGE_ACC = self.CONFIG_HPHEAT_2_STAGE_AUX_2_STAGE + self.ACC_RELAYS
        self.CONFIG_HPHEAT_2_STAGE_AUX_2_STAGE_ACC_2_STAGE = self.CONFIG_HPHEAT_2_STAGE_AUX_2_STAGE_ACC + self.PEK_PLUS

        self.CONFIG_ALL = self.CONFIG_HPCOOL_2_STAGE_AUX_2_STAGE + self.ACC_RELAYS
