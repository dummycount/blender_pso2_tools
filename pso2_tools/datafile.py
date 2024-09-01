from typing import Iterable, Protocol


class DataFile(Protocol):
    name: str
    data: bytes


class DataFileSource(Protocol):
    def get_files(self) -> Iterable[DataFile]: ...

    def glob(self, pattern: str) -> Iterable[DataFile]: ...
