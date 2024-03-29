import time
from collections import namedtuple

import machine

import gt911_constants as gt


def calculate_checksum(configuration: list[int]):
    checksum = sum(configuration[: gt.CONFIG_SIZE])
    checksum = checksum & 0xFF
    return ((~checksum) + 1) & 0xFF


def config_offset(reg: int):
    return reg - gt.CONFIG_START


class GT911:
    def __init__(self, sda, scl, interrupt, reset, freq=100_000):
        self.width = 0
        self.height = 0
        self.address = None
        self.configuration = []
        self.i2c = machine.I2C(freq=freq, scl=machine.Pin(scl), sda=machine.Pin(sda))
        self.interrupt = machine.Pin(interrupt, machine.Pin.OUT)
        self.reset_pin = machine.Pin(reset, machine.Pin.OUT)

    def enable_interrupt(self, callback):
        self.interrupt.irq(trigger=machine.Pin.IRQ_FALLING, handler=callback)

    def begin(self, address):
        self.address = address
        self.reset()
        self.configuration = self.read(gt.CONFIG_START, gt.CONFIG_SIZE)
        wl = self.configuration[config_offset(gt.X_OUTPUT_MAX_LOW)]
        wh = self.configuration[config_offset(gt.X_OUTPUT_MAX_HIGH)]
        hl = self.configuration[config_offset(gt.Y_OUTPUT_MAX_LOW)]
        hh = self.configuration[config_offset(gt.Y_OUTPUT_MAX_HIGH)]
        self.width = (wh << 8) + wl
        self.height = (hh << 8) + hl

    def reset(self):
        self.interrupt.value(0)
        self.reset_pin.value(0)
        time.sleep_ms(10)
        self.interrupt.value(self.address == gt.Addr.ADDR2)
        time.sleep_ms(1)
        self.reset_pin.value(1)
        time.sleep_ms(5)
        self.interrupt.value(0)
        time.sleep_ms(50)
        self.interrupt.init(mode=machine.Pin.IN)
        time.sleep_ms(50)

    def reflash_config(self):
        assert len(self.configuration) == gt.CONFIG_SIZE
        checksum = calculate_checksum(self.configuration)
        self.write(gt.CONFIG_START, self.configuration)
        self.write(gt.CONFIG_CHKSUM, checksum)
        self.write(gt.CONFIG_FRESH, 1)

    def set_resolution(self, width, height):
        self.configuration[gt.X_OUTPUT_MAX_LOW - gt.CONFIG_START] = width & 0xFF
        self.configuration[gt.X_OUTPUT_MAX_HIGH - gt.CONFIG_START] = (width >> 8) & 0xFF
        self.configuration[gt.Y_OUTPUT_MAX_LOW - gt.CONFIG_START] = height & 0xFF
        self.configuration[gt.Y_OUTPUT_MAX_HIGH - gt.CONFIG_START] = (
            height >> 8
        ) & 0xFF
        self.reflash_config()

    def get_points(self):
        points = []
        info = self.read(gt.POINT_INFO, 1)[0]
        ready = bool((info >> 7) & 1)
        # large_touch = bool((info >> 6) & 1)
        touch_count = info & 0xF
        if ready and touch_count > 0:
            for i in range(touch_count):
                data = self.read(gt.POINT_1 + (i * 8), 7)
                points.append(self.parse_point(data))
        self.write(gt.POINT_INFO, [0])
        return points

    def parse_point(self, data):
        track_id = data[0]
        x = data[1] + (data[2] << 8)
        y = data[3] + (data[4] << 8)
        size = data[5] + (data[6] << 8)
        return TouchPoint(track_id, x, y, size)

    def write(self, reg: int, value: list[int]):
        self.i2c.writeto_mem(self.address, reg, bytes(value), addrsize=16)

    def read(self, reg: int, length: int):
        data = self.i2c.readfrom_mem(self.address, reg, length, addrsize=16)
        return list(data)


TouchPoint = namedtuple("TouchPoint", ["id", "x", "y", "size"])
