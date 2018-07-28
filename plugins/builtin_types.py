from yapsy.IPlugin import IPlugin


class PluginOne(IPlugin):

    def __init__(self):
        super().__init__()

        self.registered_int_types = {
            "int_32_bits": True,
            "int_16_bits": True,
            "int_8_bits": True,
        }

        return

    def get_registered_types(self):
        return self.registered_int_types

    def verify_int_32_bits(self):
        return

    def verify_int_16_bits(self):
        return

    def verify_int_8_bits(self):
        return
