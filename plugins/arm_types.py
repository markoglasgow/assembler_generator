from yapsy.IPlugin import IPlugin
from bitstring import BitArray

from typing import Optional

# This plugin implement the different ARM immediate encodings.


class ARMTypes(IPlugin):

    def __init__(self):
        super().__init__()

        self.valid_chars = "-0123456789#"
        self.valid_chars_map = {}
        for c in self.valid_chars:
            self.valid_chars_map[c] = True

        self.registered_types = {
            "int_8_bits_absolute": True,
            "int_12_bits_offset": True,
            "int_12_bits_constrained": True,
        }

        return

    def get_registered_types(self):
        return self.registered_types

    def chars_int_12_bits_constrained(self):
        return self.valid_chars_map

    def verify_int_12_bits_constrained(self, int_string):
        b = self.emit_int_12_bits_constrained(int_string)
        if b is None:
            return False

        return True

    def chars_int_8_bits_absolute(self):
        return self.valid_chars_map

    def verify_int_8_bits_absolute(self, int_string):
        parsed_int = self.parse_int(int_string)
        if parsed_int is None:
            return False
        elif -128 <= parsed_int <= 255:
            return True
        else:
            return False

    def chars_int_12_bits_offset(self):
        return self.valid_chars_map

    def verify_int_12_bits_offset(self, int_string):
        parsed_int = self.parse_int(int_string)
        if parsed_int < 0:
            parsed_int = parsed_int * -1
        if parsed_int is None:
            return False
        elif -2048 <= parsed_int <= 4095:
            return True
        else:
            return False

    def parse_int(self, int_string: str) -> Optional[int]:
        if int_string.startswith("#"):
            stripped_string = int_string[1:]
            try:
                return int(stripped_string, 10)
            except ValueError:
                return None
        return None

    def emit_int_12_bits_constrained(self, int_string):
        parsed_int = self.parse_int(int_string)
        if parsed_int is None:
            return None
        b = BitArray(int=parsed_int, length=32)
        bits = str(b.bin)

        base = None
        rotation = None
        for i in range(0, 16):

            has_bits_outside_window = False
            bits_outside_window = bits
            # noinspection PyUnusedLocal
            bits_in_window = []

            window_start = i * 2
            window_end = window_start + 8
            if window_end >= len(bits):
                window_end = window_end - len(bits)

                bits_in_window = bits[window_start:len(bits)] + bits[0:window_end]

                bits_outside_window = bits_outside_window[window_end:window_start]
            else:
                bits_in_window = bits[window_start:window_end]
                bits_outside_window = bits_outside_window[0:window_start] + bits_outside_window[window_end:len(bits_outside_window)]

            for bit in bits_outside_window:
                if bit == '1':
                    has_bits_outside_window = True
                    break

            if not has_bits_outside_window:
                base = bits_in_window

                if window_end > window_start:
                    rotation = 4 + i
                else:
                    rotation = (window_end / 2)

                break

        if base is None or rotation is None:
            return None

        base_bits = BitArray('0b' + base)
        rotation_bits = BitArray(uint=rotation, length=4)

        rotation_bits.append(base_bits)

        return rotation_bits.bin

    def emit_int_8_bits_absolute(self, int_string):
        parsed_int = self.parse_int(int_string)
        if parsed_int < 128:
            b = BitArray(int=parsed_int, length=8)
        else:
            b = BitArray(uint=parsed_int, length=8)
        b.prepend('0b0000')
        return b.bin

    def emit_int_12_bits_offset(self, int_string):
        parsed_int = self.parse_int(int_string)
        if parsed_int < 0:
            parsed_int = parsed_int * -1
        if parsed_int < 2048:
            b = BitArray(int=parsed_int, length=12)
        else:
            b = BitArray(uint=parsed_int, length=12)
        return b.bin
