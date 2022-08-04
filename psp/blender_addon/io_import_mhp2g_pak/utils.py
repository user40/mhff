import struct
from mathutils import Vector

'''ゲーム内の座標をBlender用の座標に変換する'''

RATIO = 0.01


def to_blender_scale(v: Vector) -> Vector:
    return Vector((v[0], v[2], v[1]))


def to_blender_angle(v: Vector) -> Vector:
    return Vector((v[0], v[2], -v[1]))


def to_blender_location(v: Vector) -> Vector:
    return Vector((v[0]*RATIO, -v[2]*RATIO, v[1]*RATIO))


class Memory:
    '''ダンプしたメモリから値を読み出すためのヘルパークラス'''

    def __init__(self, file_path=None, offset=0x0880_0000):
        if file_path:
            self.offset = offset
            with open(file_path, 'rb') as f:
                self.mem = f.read()
        else:
            self.offset = 0
            self.mem = bytes()

    def from_bytes(bin, offset=0):
        m = Memory()
        m.offset = offset
        m.mem = bin
        return m

    def get_slice(self, start, end):
        if start < self.offset or end > self.offset + len(self.mem):
            raise OutOfRangeError(
                f"read {start:08x}-{end:08x}, memory block {self.offset:08x}-{self.offset + len(self.mem):08x}")
            pass
        return self.mem[start - self.offset:end - self.offset]

    def get_slice_at(self, start, size):
        return self.get_slice(start, start + size)

    def get_sliced_memory(self, start, end, inherit_offset=False):
        offset = start if inherit_offset else 0
        return Memory.from_bytes(self.get_slice(start, end), offset)

    def get_sliced_memory_at(self, start, size, inherit_offset=False):
        offset = start if inherit_offset else 0
        return Memory.from_bytes(self.get_slice_at(start, size), offset)

    def unpack(self, address, format):
        size = struct.calcsize(format)
        b = self.get_slice_at(address, size)
        return struct.unpack(format, b)

    def get_u32(self, address):
        b = self.get_slice_at(address, 4)
        return struct.unpack('I', b)[0]

    def get_i32(self, address):
        b = self.get_slice_at(address, 4)
        return struct.unpack('i', b)[0]

    def get_u16(self, address):
        b = self.get_slice_at(address, 2)
        return struct.unpack('H', b)[0]

    def get_i16(self, address):
        b = self.get_slice_at(address, 2)
        return struct.unpack('h', b)[0]

    def get_u8(self, address):
        b = self.get_slice_at(address, 1)
        return struct.unpack('B', b)[0]

    def get_i8(self, address):
        b = self.get_slice_at(address, 1)
        return struct.unpack('b', b)[0]

    def get_float(self, address):
        b = self.get_slice_at(address, 4)
        return struct.unpack('f', b)[0]

    def get_float_vec3(self, address):
        b = self.get_slice_at(address, 4*3)
        return struct.unpack('fff', b)

    def get_float_vec4(self, address):
        b = self.get_slice_at(address, 4*4)
        return struct.unpack('ffff', b)

    def get_float_mat33(self, address):
        b = self.get_slice_at(address, 4*3*3)
        return struct.unpack('fffffffff', b)

    def get_float_mat44(self, address):
        b = self.get_slice_at(address, 4*4*4)
        return struct.unpack('ffffffffffffffff', b)


class OutOfRangeError(Exception):
    pass
