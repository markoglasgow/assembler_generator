from yapsy.IPlugin import IPlugin
from bitstring import BitArray

from typing import Optional

# This plugin implements the data and label types for the Sigma16 architecture.


class Sigma16Types(IPlugin):

    def __init__(self):
        super().__init__()

        self.valid_chars = "-0123456789abcdefABCDEF$"
        self.valid_chars_map = {}
        for c in self.valid_chars:
            self.valid_chars_map[c] = True

        self.registered_types = {
            "int_sigma16_data": True,
            "label_sigma16": True,
        }

        return

    def get_registered_types(self):
        return self.registered_types

    def chars_int_sigma16_data(self):
        return self.valid_chars_map

    def verify_int_sigma16_data(self, int_string):
        parsed_int = self.parse_int(int_string)
        if parsed_int is None:
            return False
        elif -32768 <= parsed_int <= 65535:
            return True
        else:
            return False

    def parse_int(self, int_string: str) -> Optional[int]:
        if int_string.startswith("$") and len(int_string) == 5:
            stripped_string = int_string[1:]
            try:
                return int(stripped_string, 16)
            except ValueError:
                return None

        else:
            try:
                return int(int_string, 10)
            except ValueError:
                return None

    def emit_int_sigma16_data(self, int_string):
        parsed_int = self.parse_int(int_string)
        if parsed_int < 32768:
            b = BitArray(int=parsed_int, length=16)
        else:
            b = BitArray(uint=parsed_int, length=16)
        return b.bin

    # noinspection PyUnusedLocal
    def calc_label_sigma16(self, source_instruction_address, label_address):
        b = BitArray(int=(int(label_address/2)), length=16)
        return b.bin
