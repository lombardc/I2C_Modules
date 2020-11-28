from smbus2 import SMBus, i2c_msg


class I2CDevice:
    def __init__(self, address, bus):
        self.address = address
        self.bus = bus

    def _write_then_read(self, _write_buf, _bytes_to_read):
        write = i2c_msg.write(self.address, _write_buf)
        read = i2c_msg.read(self.address, _bytes_to_read)
        with SMBus(self.bus) as bus_temp:
            bus_temp.i2c_rdwr(write, read) if _bytes_to_read else bus_temp.i2c_rdwr(write)
        return read if _bytes_to_read else True
