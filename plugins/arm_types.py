from yapsy.IPlugin import IPlugin
from bitstring import BitArray

from typing import Optional


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
        parsed_int = self.parse_int(int_string)
        if parsed_int is None:
            return False
        elif -32768 <= parsed_int <= 65535:
            return True
        else:
            return False

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
        if parsed_int < 32768:
            b = BitArray(int=parsed_int, length=16)
        else:
            b = BitArray(uint=parsed_int, length=16)
        return b.bin

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
        parsed_int = parsed_int * -1
        if parsed_int < 2048:
            b = BitArray(int=parsed_int, length=12)
        else:
            b = BitArray(uint=parsed_int, length=12)
        return b.bin
