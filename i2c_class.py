class I2CDevice:
    def __init__(self, address, bus):
        self.address = address
        self.bus = bus

    def _write_then_read(self, _write_buf, _bytes_to_read):
        self.bus.writeto(self.address, _write_buf)
        if _bytes_to_read:
            _result = bytearray(_bytes_to_read)
            self.bus.readfrom_into(self.address, _result)
        return _result if _bytes_to_read else True

