from typing import Any, Optional

from System.Collections.Generic import KeyNotFoundException


def dict_get(d, key: Any) -> Optional[Any]:
    try:
        return d[key]
    except KeyNotFoundException:
        return None
