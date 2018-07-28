from yapsy.PluginManager import PluginManager
from typing import Dict

class AsmIntTypes:

    int_types = {}

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

                verify_method_name = "verify_" + p
                verify_method = getattr(plugin.plugin_object, verify_method_name, None)
                if verify_method is None:
                    print("Plugin Error: Method '%s' is missing from plugin file '%s' for type '%s'" % (verify_method_name, plugin.path, p))
                    raise ValueError
                AsmIntTypes.verify_methods[p] = verify_method

                AsmIntTypes.int_types[p] = True

        return
