import importlib
import sys
from types import ModuleType


def _reload(base_name: str, module: ModuleType, reloaded: set[str]):
    for name in dir(module):
        if (
            (attr := getattr(module, name))
            and isinstance(attr, ModuleType)
            and attr.__name__ not in reloaded
            and attr.__name__.startswith(base_name)
        ):
            _reload(base_name, attr, reloaded)

    if module.__name__ != base_name:
        print("reload", module.__name__)
        importlib.reload(module)
        reloaded.add(module.__name__)


def reload_addon(name: str):
    _reload(name, sys.modules[name], set())
