from yapsy.PluginManager import PluginManager
from typing import Dict


class AsmIntTypes:

    int_types = {}

    valid_chars = {}
    verify_methods = {}
    emit_methods = {}

    def __init__(self):
        return

    @staticmethod
    def load_plugins():
        manager = PluginManager()
        manager.setPluginPlaces(["plugins"])
        manager.collectPlugins()

        for plugin in manager.getAllPlugins():
            plugin_types = plugin.plugin_object.get_registered_types()  # type: Dict[str, bool]

            for p in plugin_types.keys():

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

                AsmIntTypes.int_types[p] = True

        return

    @staticmethod
    def is_defined_type(int_type):
        if int_type not in AsmIntTypes.int_types:
            return False
        return True

    @staticmethod
    def get_valid_chars(int_type):
        if not AsmIntTypes.is_defined_type(int_type):
            print("Integer error: Int of type '%s' is not defined in any plugin." % int_type)
            raise ValueError
        return AsmIntTypes.valid_chars[int_type]

    @staticmethod
    def validate_integer(int_type, int_string):
        verify_method = AsmIntTypes.verify_methods[int_type]
        return verify_method(int_string)
