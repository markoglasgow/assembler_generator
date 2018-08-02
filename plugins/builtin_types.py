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

        self.registered_types = {
            "int_32_bits": True,
            "int_16_bits": True,
            "int_8_bits": True,
            "label_x86_imm_32_bits": True,
            "label_x86_rel_32_bit_branch": True,
        }

        return

    def get_registered_types(self):
        return self.registered_types

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
        elif -2147483648 <= parsed_int <= 4294967295:
            return True
        else:
            return False

    def verify_int_16_bits(self, int_string):
        parsed_int = self.parse_int(int_string)
        if parsed_int is None:
            return False
        elif -32768 <= parsed_int <= 65535:
            return True
        else:
            return False

    def verify_int_8_bits(self, int_string):
        parsed_int = self.parse_int(int_string)
        if parsed_int is None:
            return False
        elif -128 <= parsed_int <= 255:
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
        if parsed_int < 2147483648:
            b = BitArray(int=parsed_int, length=32)
        else:
            b = BitArray(uint=parsed_int, length=32)
        b.byteswap()
        return b.bin

    def emit_int_16_bits(self, int_string):
        parsed_int = self.parse_int(int_string)
        if parsed_int < 32768:
            b = BitArray(int=parsed_int, length=16)
        else:
            b = BitArray(uint=parsed_int, length=16)
        b.byteswap()
        return b.bin

    def emit_int_8_bits(self, int_string):
        parsed_int = self.parse_int(int_string)
        if parsed_int < 128:
            b = BitArray(int=parsed_int, length=8)
        else:
            b = BitArray(uint=parsed_int, length=8)
        b.byteswap()
        return b.bin

    # noinspection PyUnusedLocal
    def calc_label_x86_imm_32_bits(self, source_instruction_address, label_address):
        b = BitArray(int=label_address, length=32)
        b.byteswap()
        return b.bin

    def calc_label_x86_rel_32_bit_branch(self, source_instruction_address, label_address):
        rel = label_address - source_instruction_address - 5
        b = BitArray(int=rel, length=32)
        b.byteswap()
        return b.bin
