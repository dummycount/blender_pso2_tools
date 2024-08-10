import struct
from dataclasses import dataclass
from pathlib import Path

from System import Array, Byte
from System.IO import FileMode, FileStream
from Zamboni import IceFile as InternalIceFile


@dataclass
class DataFile:
    name: str
    data: bytes

    @classmethod
    def from_byte_array(cls, array: Array[Byte]):
        name = InternalIceFile.getFileName(array)
        data = bytes(array)

        header_size = struct.unpack_from("i", data, offset=0xC)[0]

        return DataFile(name=name, data=data[header_size:])


class IceFile:
    group_one: list[DataFile]
    group_two: list[DataFile]

    @classmethod
    def load(cls, path: Path | str):
        stream = FileStream(str(path), FileMode.Open)
        try:
            ice = InternalIceFile.LoadIceFile(stream)

            group_one = [DataFile.from_byte_array(f) for f in ice.groupOneFiles]
            group_two = [DataFile.from_byte_array(f) for f in ice.groupTwoFiles]

            return IceFile(group_one, group_two)
        finally:
            stream.Close()

    def __init__(
        self, group_one: list[DataFile] = None, group_two: list[DataFile] = None
    ):
        self.group_one = group_one or []
        self.group_two = group_two or []
