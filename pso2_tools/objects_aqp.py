import fnmatch
import itertools
from contextlib import closing
from pathlib import Path
from typing import Iterable

import bpy

from . import objects


def guess_aqp_object(
    name: str, context: bpy.types.Context
) -> objects.CmxObjectBase | None:
    with closing(objects.ObjectDatabase(context)) as db:
        candidates = _get_candidates(name, db)

        return candidates[0] if candidates else None


def _get_candidates(
    name: str, db: objects.ObjectDatabase
) -> list[objects.CmxObjectBase]:
    parts = Path(name).stem.split("_")

    match parts:
        case ["pl", "rac", item_id] | ["pl", "ah", item_id, *_]:
            return db.get_accessories(item_id=item_id)

        case ["pl", "rbd", item_id, "bw"] | ["pl", "bd", item_id, _, _, "bw"]:
            return db.get_basewear(item_id=item_id)

        case ["pl", "rbd", item_id, "ow"] | ["pl", "bd", item_id, _, _, "ow"]:
            return db.get_outerwear(item_id=item_id)

        case ["pl", "bd", item_id, _, _, "xx"]:
            return db.get_costumes(item_id=item_id)

        case ["pl", "rbd", item_id, "bd"] | ["pl", "bd", item_id, _, _, "tr"]:
            return db.get_cast_bodies(item_id=item_id)

        case ["pl", "rbd", item_id, "rm"] | ["pl", "bd", item_id, _, _, "rm"]:
            return db.get_cast_arms(item_id=item_id)

        case ["pl", "rbd", item_id, "lg"] | ["pl", "bd", item_id, _, _, "lg"]:
            return db.get_cast_legs(item_id=item_id)

        case ["pl", "rdt", item_id]:
            return db.get_teeth(item_id=item_id)

        case ["pl", "rea", item_id]:
            return db.get_ears(item_id=item_id)

        case ["pl", "rhd", item_id] | ["pl", "hd", item_id, *_]:
            return db.get_faces(item_id=item_id)

        case ["pl", "rhn", item_id]:
            return db.get_horns(item_id=item_id)

        case ["pl", "rhr", item_id] | ["pl", "hr", item_id, *_]:
            return db.get_hair(item_id=item_id)

    return []


class AqpDataFile:
    def __init__(self, path: Path):
        self.path = path

    @property
    def name(self):
        return self.path.name

    @property
    def data(self) -> bytes:
        return self.path.read_bytes()


class AqpDataFileSource:
    def __init__(self, path: Path):
        self.path = path

    def get_files(self) -> Iterable[AqpDataFile]:
        aqp_file = AqpDataFile(self.path)
        resources = (
            AqpDataFile(path)
            for path in self.path.parent.iterdir()
            if path.is_file() and not path.suffix.lower() == ".aqp"
        )

        return itertools.chain([aqp_file], resources)

    def glob(self, pattern: str) -> Iterable[AqpDataFile]:
        return (f for f in self.get_files() if fnmatch.fnmatch(f.name, pattern))
