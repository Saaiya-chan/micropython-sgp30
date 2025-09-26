"""
sgp30_micropython.py
MicroPython driver for the Sensirion SGP30 air quality sensor (eCO2 / TVOC)

Usage (example):
    from machine import I2C, Pin
    import time
    from sgp30 import SGP30

    i2c = I2C(0, scl=Pin(22), sda=Pin(21))
    sgp = SGP30(i2c)
    sgp.init_air_quality()
    time.sleep(1)
    while True:
        reading = sgp.measure_iaq()
        print("eCO2:", reading.equivalent_co2, "TVOC:", reading.total_voc)
        time.sleep(1)

Author: generated with ChatGPT (Saaya-style)
"""
from time import sleep
from micropython import const

SGP30_DEFAULT_I2C_ADDR = const(0x58)

# Commands (Sensirion datasheet)
_CMD_INIT_AIR_QUALITY = (0x20, 0x03)
_CMD_MEASURE_IAQ = (0x20, 0x08)
_CMD_GET_IAQ_BASELINE = (0x20, 0x15)
_CMD_SET_IAQ_BASELINE = (0x20, 0x1E)
_CMD_MEASURE_RAW = (0x20, 0x50)
_CMD_MEASURE_TEST = (0x20, 0x32)
_CMD_SET_ABSOLUTE_HUMIDITY = (0x20, 0x61)
_CMD_GET_SERIAL_ID = (0x36, 0x82)
_CMD_SOFT_RESET = (0x00, 0x06)

class SGP30Reading:
    __slots__ = ('equivalent_co2', 'total_voc')
    def __init__(self, eco2, tvoc):
        self.equivalent_co2 = eco2
        self.total_voc = tvoc

class SGP30:
    def __init__(self, i2c, address=SGP30_DEFAULT_I2C_ADDR):
        """
        i2c: an initialized machine.I2C instance
        address: I2C address (default 0x58)
        """
        self.i2c = i2c
        self.address = address

    # ---- low-level helpers ----
    def _crc8(self, data):
        """Compute the Sensirion CRC8 for data (iterable of bytes)."""
        crc = 0xFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = ((crc << 1) & 0xFF) ^ 0x31
                else:
                    crc = (crc << 1) & 0xFF
        return crc

    def _cmd_to_bytes(self, cmd):
        return bytes([cmd[0], cmd[1]])

    def _write_command(self, cmd, arguments=()):
        """
        Write a command and optional list of 16-bit argument values.
        Each 16-bit argument is sent MSB, LSB, CRC.
        """
        buf = bytearray(self._cmd_to_bytes(cmd))
        for value in arguments:
            hi = (value >> 8) & 0xFF
            lo = value & 0xFF
            crc = self._crc8((hi, lo))
            buf.extend(bytes([hi, lo, crc]))
        # direct I2C write
        self.i2c.writeto(self.address, buf)

    def _read_bytes(self, count, delay=0.001):
        """Read count bytes from device after optional delay (seconds)."""
        if delay:
            sleep(delay)
        return self.i2c.readfrom(self.address, count)

    def _read_words_with_crc(self, n_words, delay=0.001):
        """
        Read n_words words. Each word is 2 bytes followed by 1 CRC.
        Returns list of integer word values.
        """
        raw = self._read_bytes(n_words * 3, delay=delay)
        if len(raw) != n_words * 3:
            raise OSError("SGP30: expected %d bytes, got %d" % (n_words*3, len(raw)))
        words = []
        for i in range(n_words):
            a = raw[i*3]
            b = raw[i*3 + 1]
            crc = raw[i*3 + 2]
            if self._crc8((a, b)) != crc:
                raise OSError("SGP30 CRC mismatch")
            words.append((a << 8) | b)
        return words

    # ---- high-level API ----
    def init_air_quality(self):
        """Initialize IAQ algorithm (must be called after power-up or soft reset)."""
        self._write_command(_CMD_INIT_AIR_QUALITY)
        # recommended small delay (datasheet suggests a short time)
        sleep(0.01)

    def measure_iaq(self):
        """
        Trigger a single IAQ measurement and return SGP30Reading(eCO2, TVOC).
        Measurement returns two words (eCO2 [ppm], TVOC [ppb]).
        """
        self._write_command(_CMD_MEASURE_IAQ)
        # typical measurement time: ~12-15 ms; Adafruit uses ~0.015s
        words = self._read_words_with_crc(2, delay=0.015)
        return SGP30Reading(words[0], words[1])

    def measure_raw(self):
        """Measure raw sensor signals (H2 and Ethanol raw signals). Returns (raw_h2, raw_ethanol)."""
        self._write_command(_CMD_MEASURE_RAW)
        words = self._read_words_with_crc(2, delay=0.02)
        return words[0], words[1]

    def measure_test(self):
        """Run sensor self-test. Returns True if OK (result word == 0xD400)."""
        self._write_command(_CMD_MEASURE_TEST)
        words = self._read_words_with_crc(1, delay=0.2)
        return words[0] == 0xD400

    def get_baseline(self):
        """Get IAQ baseline values. Returns tuple (eCO2_baseline, TVOC_baseline)."""
        self._write_command(_CMD_GET_IAQ_BASELINE)
        words = self._read_words_with_crc(2, delay=0.015)
        # according to Adafruit, order returned is TVOC baseline, eCO2 baseline
        # but many libraries expose eCO2, TVOC. We return (eCO2, TVOC) for convenience.
        tvoc_baseline, eco2_baseline = words[0], words[1]
        return eco2_baseline, tvoc_baseline

    def set_baseline(self, eCO2, TVOC):
        """
        Set IAQ baseline. Provide eCO2 and TVOC baseline integers returned earlier.
        Note: hardware expects TVOC then eCO2 in the payload.
        """
        if eCO2 == 0 and TVOC == 0:
            raise ValueError("Invalid baseline: both zero")
        # payload order: TVOC, eCO2
        self._write_command(_CMD_SET_IAQ_BASELINE, (TVOC & 0xFFFF, eCO2 & 0xFFFF))

    def set_absolute_humidity(self, grams_per_m3):
        """
        Set absolute humidity in g/m^3 for on-chip humidity compensation.
        The sensor expects an unsigned fixed-point 8.8 value: int(grams * 256).
        Range: minimum 1 (1/256 g/m3) to 0xFFFF.
        """
        if grams_per_m3 <= 0:
            # to disable humidity compensation, send 0 (not recommended) or skip calling
            raise ValueError("absolute humidity must be positive (g/m3)")
        val = int(grams_per_m3 * 256) & 0xFFFF
        if val == 0:
            val = 1
        self._write_command(_CMD_SET_ABSOLUTE_HUMIDITY, (val,))

    def get_serial_id(self):
        """Return 48-bit serial id as integer"""
        self._write_command(_CMD_GET_SERIAL_ID)
        words = self._read_words_with_crc(3, delay=0.001)
        # words are msw..lsw; combine to 48-bit int
        serial = (words[0] << 32) | (words[1] << 16) | words[2]
        return serial

    def soft_reset(self):
        """Soft reset the sensor (general call)"""
        # Soft reset is a general-call command; write to address 0x00 usually.
        # Sensirion defines soft reset 0x0006 as general call; MicroPython I2C cannot easily send general call,
        # so we emulate by writing to the device address (works on many breakouts).
        try:
            self._write_command(_CMD_SOFT_RESET)
        except Exception:
            # ignore errors from reset attempt
            pass


