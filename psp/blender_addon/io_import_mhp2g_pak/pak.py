import io
from dataclasses import dataclass
from utils import Memory


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


@dataclass
class Entry:
    start: int
    size: int

@dataclass
class Header:
    fileCount: int
    files: list[Entry]