from i2c_class import *

_DIG_POT_REF = [0.4, 0.4, 0.4, 1.5]
_DIG_POT_WIP_RES = 55
_DIG_POT_NOM_RES = 10000
_DIG_POT_CHANNELS_MASKS = {-1: 0x08,  # -1 : All channels (When applicable)
                           0: 0x00,
                           1: 0x01,
                           2: 0x02,
                           3: 0x03, }
_DIG_POT_WRITE_RDAC = bytearray([0x10, 0x00, ])
_DIG_POT_WRITE_IN_REG = bytearray([0x20, 0x00, ])
_DIG_POT_READ_IN_REG = bytearray([0x30, 0x00, ])
_DIG_POT_READ_EEPROM = bytearray([0x30, 0x01, ])
_DIG_POT_READ_CONTROL = bytearray([0x30, 0x02, ])
_DIG_POT_READ_RDAC = bytearray([0x30, 0x03, ])
_DIG_POT_LIN_INC = bytearray([0x40, 0x01, ])
_DIG_POT_LIN_DEC = bytearray([0x40, 0x00, ])
_DIG_POT_PLUS_6DB = bytearray([0x50, 0x01, ])
_DIG_POT_MINU_6DB = bytearray([0x50, 0x00, ])
_DIG_POT_SOFT_LRDAC = bytearray([0x60, 0x00, ])
_DIG_POT_RDAC_TO_EEPROM = bytearray([0x70, 0x01, ])
_DIG_POT_EEPROM_TO_RDAC = bytearray([0x70, 0x00, ])
_DIG_POT_SET_EEPROM = bytearray([0x80, 0x00, ])
_DIG_POT_SOFT_RST = bytearray([0xB0, 0x00, ])
_DIG_POT_WRITE_CTRL_REG = bytearray([0xD0, 0x00, ])


class AD5144(I2CDevice):
    def __init__(self, adr=0x2B, i2c_bus=1, channels_ref=None, whipper=55, res=10000):
        super().__init__(adr, i2c_bus)
        if channels_ref is None:
            self.__channels_ref = [0.4, 0.4, 0.4, 1.24]
        self.__res = res
        self.__whipper = whipper
        self.__output = {0: 0,
                         1: 0,
                         2: 0,
                         3: 0, }
        self.__in_register = {0: 0,
                              1: 0,
                              2: 0,
                              3: 0, }
        self.__default = {0: 0,
                          1: 0,
                          2: 0,
                          3: 0, }
        self.__RDAC_WRITE_PROTECT = None
        self.__EEPROM_PROGRAM_ENABLE = None
        self.__GAIN_OR_POT_MODE = None
        self.__BURST_MODE = None

    @property
    def whipper(self):
        """ Value of the whipper resistor """
        return self.__whipper

    @whipper.setter
    def whipper(self, val):
        """ Set the value of the whipper resistor to val. Val as to be >= 0"""
        assert val >= 0
        self.__whipper = val

    @property
    def resistor(self):
        """ Value of the full-range potentiometer resistor"""
        return self.__res

    @resistor.setter
    def resistor(self, val):
        """ Set the value of the full-range potentiometer resistor to val. Val as to be >= 0"""
        assert val >= 0
        self.__res = val

    @property
    def references(self):
        """ Value of reference voltages for each channel"""
        return self.__channels_ref

    @references.setter
    def references(self, val):
        """ Set the references voltage to val.
        Val is a list of the references ordered by channel :
        val[0] = reference voltage for channel 0"""
        self.__channels_ref = val

    @property
    def params(self):
        """Return the value of the Control Register Bit.
        See datasheet for more information"""
        read = self._write_then_read(_DIG_POT_READ_CONTROL, 1)
        value = read[0]
        self.__RDAC_WRITE_PROTECT = value & 0x01
        self.__EEPROM_PROGRAM_ENABLE = (value & 0x02) >> 1
        self.__GAIN_OR_POT_MODE = (value & 0x04) >> 2
        self.__BURST_MODE = (value & 0x08) >> 3
        return {"RDAC Write Protect": self.__RDAC_WRITE_PROTECT,
                "EEPROM Write Enable": self.__EEPROM_PROGRAM_ENABLE,
                "Mode": self.__GAIN_OR_POT_MODE,
                "I2C Burst Mode": self.__BURST_MODE,
                }

    @params.setter
    def params(self, reg_val):
        """ Set the value of the control register. See datasheet for information"""
        assert 0 <= reg_val <= 15
        _BUFFER = _DIG_POT_WRITE_CTRL_REG[:]
        _BUFFER[1] += reg_val
        self._write_then_read(bytearray(_BUFFER), 0)

    @property
    def default(self):
        """ Return the current status of the EEPROM as a dict (channel : value).
         Value displayed are the one used when the device is started, or when
         a reset is performed."""
        self.__in_register = self.__get_multiple_channel(_DIG_POT_READ_EEPROM)
        return self.__in_register

    @default.setter
    def default(self, data):
        """ Set the default position of the whipper (after start-up or reset).
        # Data expect a tuple (channel, value)
        - Channel (either 0, 1, 2 or 3. Updating all the value together is not possible...
        - Value : 0 to 255 """
        assert data[0] >= 0  # Not allowed to set multiple default value (hard limitation)
        self.__set_multiple_channel(_DIG_POT_SET_EEPROM, data)

    @property
    def in_reg(self):
        """ Return the current status of the input register as a dict :
        channel : value """
        self.__in_register = self.__get_multiple_channel(_DIG_POT_READ_IN_REG)
        return self.__in_register

    @in_reg.setter
    def in_reg(self, data):
        """Set the value of the input register. It does not update the outputs.
        To update the outputs, use a hard update (high to low transition of /LRDAC) or a soft update (self.soft_lrdac).

        # Data expect a tuple (channel, value)
        - Channel (either 0, 1, 2 or 3. -1 for all
        - Value : 0 to 255"""
        self.__set_multiple_channel(_DIG_POT_WRITE_IN_REG, data)

    @property
    def rdac(self):
        """ Return the current status of the outputs as a dict :
        channel : value """
        self.__output = self.__get_multiple_channel(_DIG_POT_READ_RDAC)
        return self.__output

    @rdac.setter
    def rdac(self, data):
        """Set the position of the whipper for the specified channel.
        Effect is immediate, and output will change without any other
        action.
        # Data expect a tuple (channel, value)
        - Channel (either 0, 1, 2 or 3. -1 for all
        - Value : 0 to 255"""
        self.__set_multiple_channel(_DIG_POT_WRITE_RDAC, data)

    def soft_lrdac(self, channel):
        """ Call the soft LRDAC function for the specified channel (-1 for all together).
        A soft LRDAC set the copy the value of the input register to the RDAC."""
        assert channel in _DIG_POT_CHANNELS_MASKS.keys()
        _BUFFER = _DIG_POT_SOFT_LRDAC[:]
        _BUFFER[0] += _DIG_POT_CHANNELS_MASKS[channel]
        self._write_then_read(bytearray(_BUFFER), 0)

    def increase_channel(self, channel):
        """ Increase the specified channel (-1 for all channel) by one"""
        self.__set_multiple_channel(_DIG_POT_LIN_INC, (channel, 0))

    def decrease_channel(self, channel):
        """ Decrease the specified channel (-1 for all channel) by one"""
        self.__set_multiple_channel(_DIG_POT_LIN_DEC, (channel, 0))

    def plus_6_db(self, channel):
        """Add 6 dB (double the voltage) to the output of the specified channel (-1 for all).
        If the future value is greater than 255, the output is set to 255"""
        self.__set_multiple_channel(_DIG_POT_PLUS_6DB, (channel, 0))

    def minus_6_db(self, channel):
        """Remove 6 dB (voltage divided by 2) to the output of the specified channel (-1 for all).
        If the future value is lower than 0, the output is set to 0"""
        self.__set_multiple_channel(_DIG_POT_MINU_6DB, (channel, 0))

    def current_val_to_default(self, channel):
        """ Set the current position of the whipper according to the default value for the specified channel.
        Channel has to be either 0, 1, 2 or 3."""
        assert channel >= 0
        self.__set_multiple_channel(_DIG_POT_RDAC_TO_EEPROM, (channel, 0))

    def default_val_to_output(self, channel):
        """ Restore the default value for the specified channel.
        Channel has to be either 0, 1, 2 or 3."""
        assert channel >= 0
        self.__set_multiple_channel(_DIG_POT_EEPROM_TO_RDAC, (channel, 0))

    def output_voltage(self, channel, voltage):
        """Set the specified output to a specified voltage.
        This action directly affect the output as the RDAC register is writen.
        Whipper, Resistor, and References are used to perform this action"""
        assert (channel in _DIG_POT_CHANNELS_MASKS.keys()) and channel >= 0
        _ref = self.__channels_ref[channel]
        assert 0 <= voltage <= _ref
        data = round((256 / _ref) * (voltage - _ref * (self.__whipper / self.__res)))
        self.rdac = (channel, data)

    def __get_multiple_channel(self, reg_to_read):
        """ Read the value of all the channels for the reg_to_read register"""
        temp = {}
        for i in self.__output.keys():
            temp[i] = self.__get_single_channel(i, reg_to_read)
        return temp

    def __set_multiple_channel(self, reg_to_write, data):
        """ Set the value of reg_to_write register according to data
        data expect a tuple : data[0] = channel (-1 for all)
        data[1] = value (0 - 255)"""
        _channel = data[0]
        _value = data[1]
        assert _channel in _DIG_POT_CHANNELS_MASKS.keys()
        assert 0 <= _value <= 255

        _BUFFER = reg_to_write[:]
        _BUFFER[0] += _DIG_POT_CHANNELS_MASKS[_channel]
        _BUFFER[1] += _value
        self._write_then_read(bytearray(_BUFFER), 0)

    def __get_single_channel(self, channel, reg_to_read):
        """ Read the value of all the specified channel for the reg_to_read register"""
        assert (channel in _DIG_POT_CHANNELS_MASKS.keys()) and channel >= 0
        _BUFFER = reg_to_read[:]
        _BUFFER[0] += _DIG_POT_CHANNELS_MASKS[channel]
        read = self._write_then_read(bytearray(_BUFFER), 1)
        return read[0]
