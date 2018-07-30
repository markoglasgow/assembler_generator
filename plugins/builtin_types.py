from yapsy.IPlugin import IPlugin
from bitstring import BitArray

from typing import Optional


class PluginOne(IPlugin):

    def __init__(self):
        super().__init__()

        self.valid_chars = "-0123456789abcdefABCDEFh"
        self.valid_chars_map = {}
        for c in self.valid_chars:
            self.valid_chars_map[c] = True

        self.registered_int_types = {
            "int_32_bits": True,
            "int_16_bits": True,
            "int_8_bits": True,
        }

        return

    def get_registered_types(self):
        return self.registered_int_types

    def chars_int_32_bits(self):
        return self.valid_chars_map

    def chars_int_16_bits(self):
        return self.valid_chars_map

    def chars_int_8_bits(self):
        return self.valid_chars_map

    def verify_int_32_bits(self, int_string):
        parsed_int = self.parse_int(int_string)
        if parsed_int is None:
            return False
        elif -2147483648 <= parsed_int <= 2147483647:
            return True
        else:
            return False

    def verify_int_16_bits(self, int_string):
        parsed_int = self.parse_int(int_string)
        if parsed_int is None:
            return False
        elif -32768 <= parsed_int <= 32767:
            return True
        else:
            return False

    def verify_int_8_bits(self, int_string):
        parsed_int = self.parse_int(int_string)
        if parsed_int is None:
            return False
        elif -128 <= parsed_int <= 127:
            return True
        else:
            return False

    def parse_int(self, int_string: str) -> Optional[int]:
        if int_string.startswith("-") and int_string.endswith("h"):
            return None

        if not int_string.startswith("0") and int_string.endswith("h"):
            return None

        if int_string.startswith("0") and int_string.endswith("h"):
            stripped_string = int_string[1:-1]
            try:
                return int(stripped_string, 16)
            except ValueError:
                return None

        else:
            try:
                return int(int_string, 10)
            except ValueError:
                return None

    def emit_int_32_bits(self, int_string):
        parsed_int = self.parse_int(int_string)
        b = BitArray(int=parsed_int, length=32)
        b.byteswap()
        return b.bin

    def emit_int_16_bits(self, int_string):
        parsed_int = self.parse_int(int_string)
        b = BitArray(int=parsed_int, length=16)
        b.byteswap()
        return b.bin

    def emit_int_8_bits(self, int_string):
        parsed_int = self.parse_int(int_string)
        b = BitArray(int=parsed_int, length=8)
        b.byteswap()
        return b.bin