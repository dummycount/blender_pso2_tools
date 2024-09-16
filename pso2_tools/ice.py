import fnmatch
import itertools
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from System import Array
from System.IO import FileMode, FileStream
from Zamboni import IceFile as InternalIceFile

from . import datafile


@dataclass
class IceDataFile:
    name: str
    data: bytes

    @classmethod
    def from_byte_array(cls, array: Array[int]):  # type: ignore
        name = InternalIceFile.getFileName(array)  # type: ignore
        data = bytes(array)

        header_size = struct.unpack_from("i", data, offset=0xC)[0]

        return IceDataFile(name=name, data=data[header_size:])


class IceFile:
    group_one: list[IceDataFile]
    group_two: list[IceDataFile]

    @classmethod
    def load(cls, path: Path | str):
        stream = FileStream(str(path), FileMode.Open)
        try:
            ice = InternalIceFile.LoadIceFile(stream)

            group_one = [IceDataFile.from_byte_array(f) for f in ice.groupOneFiles]
            group_two = [IceDataFile.from_byte_array(f) for f in ice.groupTwoFiles]

            return IceFile(group_one, group_two)
        finally:
            stream.Close()

    def __init__(
        self,
        group_one: list[IceDataFile] | None = None,
        group_two: list[IceDataFile] | None = None,
    ):
        self.group_one = group_one or []
        self.group_two = group_two or []

    def get_files(self) -> Iterable[datafile.DataFile]:
        return itertools.chain(self.group_one, self.group_two)

    def glob(self, pattern: str) -> Iterable[datafile.DataFile]:
        return (f for f in self.get_files() if fnmatch.fnmatch(f.name, pattern))
