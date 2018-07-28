from yapsy.IPlugin import IPlugin


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
        return False

    def verify_int_16_bits(self, int_string):
        return False

    def verify_int_8_bits(self, int_string):
        return False
