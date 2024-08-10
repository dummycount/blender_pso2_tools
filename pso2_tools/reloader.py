import importlib
import sys
from types import ModuleType


def _reload(base_name: str, module: ModuleType, reloaded: dict[str, ModuleType]):
    for name in dir(module):
        if (
            (attr := getattr(module, name))
            and isinstance(attr, ModuleType)
            and attr.__name__.startswith(base_name)
        ):
            if attr.__name__ not in reloaded:
                _reload(base_name, attr, reloaded)

            setattr(module, attr.__name__, reloaded[attr.__name__])

    if module.__name__ != base_name:
        print("Reloading:", module.__name__)
        reloaded[module.__name__] = importlib.reload(module)


def reload_addon(name: str):
    _reload(name, sys.modules[name], {})
