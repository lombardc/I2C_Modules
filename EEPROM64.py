from i2c_class import *
import time
from random import randint


class EEPROM64(I2CDevice):
    def __init__(self, adr=0x50, i2c_bus=1, size=64, max_write=32):
        super().__init__(adr, i2c_bus)
        self.__max_address = int((size*1024/8)-1)
        self.__max_size_write = max_write

    def write_single(self, address, data):
        assert 0 <= address <= self.__max_address
        assert 0 <= data <= 0xFF
        _address_low = 0x00FF & address
        _address_high = (0xFF00 & address) >> 8
        self._write_then_read(bytearray([_address_high, _address_low, data]), 0)

    def read_single(self, address):
        assert 0 <= address <= self.__max_address
        _address_low = 0x00FF & address
        _address_high = (0xFF00 & address) >> 8
        read = self._write_then_read(bytearray([_address_high, _address_low]), 1)
        return int(read[0])

    def write_page(self, address_start, data):
        assert 0 <= address_start <= self.__max_address  # Check that start address is in memory range
        assert address_start + len(data) - 1 <= self.__max_address  # Check that final address is in memory range
        assert len(data) <= self.__max_size_write  # Check that data length is not greater than buffer size
        assert False not in (byte <= 0xFF for byte in data)  # Check that each data is compatible with byte size.
        _address_low = 0x00FF & address_start
        _address_high = (0xFF00 & address_start) >> 8
        _BUFFER = [_address_high, _address_low, ]
        for byte in data:
            _BUFFER.append(byte)
        self._write_then_read(bytearray(_BUFFER), 0)

    def read_page(self, address_start, nob):
        assert 0 <= address_start <= self.__max_address  # Check that start address is in memory range
        assert address_start + nob - 1 <= self.__max_address  # Check that final address is in memory range
        _address_low = 0x00FF & address_start
        _address_high = (0xFF00 & address_start) >> 8
        _read = self._write_then_read(bytearray([_address_high, _address_low]), nob)
        _output = []
        for byte in _read:
            _output.append(byte)
        return _output

    def read_complete(self, batch_size=0xFF):
        _output = []
        for i in range(0, self.__max_address + 1, batch_size):
            nob = batch_size if (i + batch_size) < self.__max_address else self.__max_address - i + 1
            _output += self.read_page(i, nob)
            time.sleep(0.005)
        return _output

    def complete_erase(self, method=-1):
        max_length = self.__max_size_write
        assert -1 <= method <= 0xFF
        for i in range(0, self.__max_address + 1, max_length):
            nob = max_length if (i + max_length) < self.__max_address else self.__max_address - i + 1
            if method == -1:
                _buffer = [randint(0, 0xFF) for x in range(nob)]
            else:
                _buffer = [method for x in range(nob)]
            self.write_page(i, _buffer)
            time.sleep(0.005)
