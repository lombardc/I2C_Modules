from i2c_class import *

_Si7050_BITS = {14: 0, 12: 1, 13: 2, 11: 3}
_Si7050_RESET = [0xFE]
_Si7050_MEASURE = [0xE3]
_Si7050_READ_USR = [0xE7]
_Si7050_WRITE_USR = [0xE6]
_Si7050_SN_B1 = [0xFA, 0x0F]
_Si7050_SN_B2 = [0xFC, 0xC9]
_Si7050_FIRMWARE = [0x84, 0xB8]


class Si7050(I2CDevice):
    def __init__(self, adr, i2c_bus=1):
        super().__init__(adr, i2c_bus)
        self.__sn = None
        self.__firmware = None
        self.__mode = None
        self.__power_watch_dog = None
        self.__config()

    def temp(self):
        read = self._write_then_read(_Si7050_MEASURE, 2)
        result = (int(ord(read.buf[0])) << 8) + int(ord(read.buf[1]))
        c_temp = ((175.72 * result)/65536) - 48.85
        return round(c_temp)

    def reset(self):
        self._write_then_read(_Si7050_RESET, 0)

    @property
    def power_good(self):
        self.__config()
        return True if not self.__power_watch_dog else False

    @property
    def mode(self):
        self.__config()
        assert self.__mode in _Si7050_BITS.values()
        nob = list(_Si7050_BITS.keys())[list(_Si7050_BITS.values()).index(self.__mode)]
        return nob

    @mode.setter
    def mode(self, nob):
        assert nob in _Si7050_BITS.keys()
        int_nob = _Si7050_BITS[nob]
        cur_val = self.__config()
        d_7 = (int_nob & 2) >> 1
        d_0 = int_nob & 1
        target_val = (d_7 << 7) + (cur_val & 0x7E) + d_0
        self._write_then_read([_Si7050_WRITE_USR[0], target_val], 0)
        assert target_val == self.__config()

    @property
    def sn(self):
        if self.__sn is None:
            msb = self._write_then_read(_Si7050_SN_B1, 4)
            lsb = self._write_then_read(_Si7050_SN_B2, 4)
            self.__sn = ""
            for k in range(msb.len):
                self.__sn += format(hex(ord(msb.buf[k]))).replace("0x", "")
            for k in range(lsb.len):
                self.__sn += format(hex(ord(lsb.buf[k]))).replace("0x", "")
        return self.__sn

    @property
    def firmware(self):
        if self.__firmware is None:
            firmware = self._write_then_read(_Si7050_FIRMWARE, 1)
            temp = ""
            for k in range(firmware.len):
                temp += format(ord(firmware.buf[k]))
            if int(temp) == 32:
                self.__firmware = "Firmware version 2.0"
            elif int(temp) == 255:
                self.__firmware = "Firmware version 1.0"
            else:
                self.__firmware = "Unknown Firmware"
        return self.__firmware

    def __config(self):
        config = self._write_then_read(_Si7050_READ_USR, 1)
        conf_reg = int(format(ord(config.buf[0])))
        self.__mode = ((conf_reg & 0x80) >> 6) + (conf_reg & 0x01)
        self.__power_watch_dog = (conf_reg & 0x04)
        return conf_reg


a = Si7050(0x40)
