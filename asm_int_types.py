from yapsy.PluginManager import PluginManager
from typing import Dict

# This module is responsible for loading and validating all plugins, registering their types, and then presenting a
# simple interface for the rest of the program to be able to use the plugin system to validate ints/labels and emit
# bitstreams for them.


class AsmIntTypes:

    defined_types = {}

    valid_chars = {}
    verify_methods = {}
    emit_methods = {}
    calc_methods = {}

    def __init__(self):
        return

    # This method is run at the beginning of the generic assembler. It loads all plugins, registers their types, and
    # makes sure the plugin implements the correct interface for each type.
    @staticmethod
    def load_plugins():
        manager = PluginManager()
        manager.setPluginPlaces(["plugins"])
        manager.collectPlugins()

        for plugin in manager.getAllPlugins():
            plugin_types = plugin.plugin_object.get_registered_types()  # type: Dict[str, bool]

            for p in plugin_types.keys():

                if p.startswith("int"):
                    chars_method_name = "chars_" + p
                    chars_method = getattr(plugin.plugin_object, chars_method_name, None)
                    if chars_method is None:
                        print("Plugin Error: Method '%s' is missing from plugin file '%s' for type '%s'" % (
                            chars_method, plugin.path, p))
                        raise ValueError
                    AsmIntTypes.valid_chars[p] = chars_method()

                    verify_method_name = "verify_" + p
                    verify_method = getattr(plugin.plugin_object, verify_method_name, None)
                    if verify_method is None:
                        print("Plugin Error: Method '%s' is missing from plugin file '%s' for type '%s'" % (
                            verify_method_name, plugin.path, p))
                        raise ValueError
                    AsmIntTypes.verify_methods[p] = verify_method

                    emit_method_name = "emit_" + p
                    emit_method = getattr(plugin.plugin_object, emit_method_name, None)
                    if emit_method is None:
                        print("Plugin Error: Method '%s' is missing from plugin file '%s' for type '%s'" % (
                            emit_method_name, plugin.path, p))
                        raise ValueError
                    AsmIntTypes.emit_methods[p] = emit_method

                elif p.startswith("label"):
                    calc_method_name = "calc_" + p
                    calc_method = getattr(plugin.plugin_object, calc_method_name, None)
                    if calc_method is None:
                        print("Plugin Error: Method '%s' is missing from plugin file '%s' for type '%s'" % (
                            calc_method_name, plugin.path, p))
                        raise ValueError
                    AsmIntTypes.calc_methods[p] = calc_method

                AsmIntTypes.defined_types[p] = True

        return

    # This function lets the rest of the program check if a type is defined in the plugin system.
    @staticmethod
    def is_defined_type(int_type):
        if int_type not in AsmIntTypes.defined_types:
            return False
        return True

    # This function lets the rest of the program get a character whitelist for parsing integers of a certain type.
    @staticmethod
    def get_valid_chars(int_type):
        if not AsmIntTypes.is_defined_type(int_type):
            print("Integer error: Int of type '%s' is not defined in any plugin." % int_type)
            raise ValueError
        return AsmIntTypes.valid_chars[int_type]

    # This function lets the rest of the program query the plugin system to see if a certain type of interger it has
    # parsed is valid (for example: is in valid format, isn't overflowing, etc...)
    @staticmethod
    def validate_integer(int_type, int_string):
        verify_method = AsmIntTypes.verify_methods[int_type]
        return verify_method(int_string)

    # This function lets the rest of the program use the plugin system to emit the bitstream for a certain type of
    # integer
    @staticmethod
    def emit_bits(int_type, int_string):
        emit_method = AsmIntTypes.emit_methods[int_type]
        return emit_method(int_string)

    # This function lets the rest of the program use the plugin system to calculate and emit the bitstream for a label.
    # As input, it takes the type of the label, the address of the instruction using the label, and the actual memory
    # location associated with the label.
    @staticmethod
    def calc_label_bits(label_type, source_address, label_address):
        calc_method = AsmIntTypes.calc_methods[label_type]
        return calc_method(source_address, label_address)
