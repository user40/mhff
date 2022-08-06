from enum import Enum
import io
from dataclasses import dataclass
from utils import Memory


@dataclass
class Entry:
    start: int
    size: int


@dataclass
class Header:
    fileCount: int
    files: list[Entry]


class FileType(Enum):
    PAK0 = 0,
    PMO = 1,
    TMH = 2,
    PAK3 = 3,


class Pak:
    def __init__(self, filepath) -> None:
        bin = Memory(filepath, 0)
        file_count = bin.get_u32(0)
        files = []
        for i in range(0, file_count):
            start = bin.get_u32(4+8*i)
            size = bin.get_u32(4+8*i+4)
            files.append(Entry(start, size))

        self.bin = bin
        self.header = Header(file_count, files)

    def get_byte_streme(self, index) -> io.BytesIO:
        entry = self.header.files[index]
        bin = self.bin.get_slice_at(entry.start, entry.size)
        return io.BytesIO(bin)

    def get_all_byte_stremes(self) -> list[(FileType, io.BytesIO)]:
        result = []
        for i in range(self.header.fileCount):
            file = self.get_byte_streme(i)
            result.append((self.file_type(file), file))
        return result

    @classmethod
    def file_type(cls, file: io.BytesIO) -> FileType:
        head = file.read(4)
        file.seek(0)
        if head == b'\x70\x6d\x6f\x00':
            return FileType.PMO
        elif head == b'\x2e\x54\x4d\x48':
            return FileType.TMH
        elif head == b'\x64\x00\x00\x00':
            return FileType.PAK3
        else:
            # Could be wrong!
            return FileType.PAK0
