from enum import Enum
from struct import unpack
from structures import (
    ChannelFlag,
    KeyFrame,
    Fcurve,
    Joint,
    MHAction,
    Version,
)
from utils import Memory


# キーフレームひとつのサイズ(バイト)
KEYFRAME_SIZE = 8

# 単位系換算用定数
DISTANCE_CONVERSION_COEFF = 0.0625
ANGLE_CONVERSION_COEFF = 0.0003834952076431364
SCALE2_CONVERSION_COEFF = 0.00390625

# fcurve_container型のフィールドのオフセット
OFFSET_FLAG = 0
OFFSET_COUNT = 0x4
OFFSET_SIZE = 0x8
# fcurve_container型のヘッダサイズ
HEADER_SIZE = 0xc
# fcurve_container型のルートのヘッダサイズ
ROOT_HEADER_SIZE = 0x14


class ContainerType(Enum):
    ACTION = 0
    JOINT = 1
    FCURVE = 2
    
    def child(self):
        return ContainerType(self.value + 1)


OFFSET_2G = {
    ContainerType.ACTION: dict(
        flag=(0, 2),
        count=(4, 4),
        size=(8, 4),
        contents=0x14,
    ),
    ContainerType.JOINT: dict(
        flag=(0, 2),
        count=(4, 4),
        size=(8, 4),
        contents=0xc,
    ),
    ContainerType.FCURVE: dict(
        flag=(0, 2),
        count=(4, 4),
        size=(8, 4),
        contents=0xc,
    ),
}

OFFSET_3 = {
    ContainerType.ACTION: dict(
        count=(0, 4),
        size=(4, 4),
        contents=0x10,
    ),
    ContainerType.JOINT: dict(
        count=(0, 2),
        size=(2, 2),
        contents=4,
    ),
    ContainerType.FCURVE: dict(
        flag=(0, 2),
        count=(2, 2),
        size=(4, 2),
        contents=8,
    ),
}

OFFSET = {Version.SECOND_G: OFFSET_2G, Version.THIRD: OFFSET_3}


class Pak3:
    def __init__(self, streme, version: Version):
        self.mem = Memory.from_bytes(streme.read())
        self.version = version
        self.offset = OFFSET[version]
        self.addresses = self.get_addresses()
        pass

    def read(self) -> dict[int, MHAction]:
        actions = {}
        for idx in self.keys():
            actions[idx] = self.get(idx)
        return actions

    def keys(self) -> list[int]:
        '''pak3ファイルの有効なインデックスの一覧を取得する。'''
        return self.addresses.keys()

    def get_addresses(self) -> dict[int, int]:
        # ポインタテーブルたちのオフセットを読み出し
        counts = []
        offsets = []
        adr = 0
        while True:
            count = self.mem.get_u32(adr)
            offset = self.mem.get_u32(adr+4)
            if count == 0:
                end = offset
                break
            counts.append(count)
            offsets.append(offset)
            adr = adr + 8

        # 整合性チェック
        if end != offsets[-1] + counts[-1]*4:
            raise Exception

        # 実際のインデックスを探索
        addresses = {}
        index = 0
        for count, offset in zip(counts, offsets):
            for j in range(0, count):
                address = self.mem.get_u32(offset+4*j)
                if address != 0xFFFFFFFF:
                    addresses[index] = address
                index = index + 1

        return addresses

    def get(self, index: int) -> MHAction:
        '''インデックスを指定してアクションを取得する。'''
        address = self.addresses[index]

        if address == 0xFFFFFFFF or address == None:
            return None

        return self.action(address)

    def get_flag(self, address: int, type: ContainerType) -> ChannelFlag:
        offset, size = self.offset[type]['flag']
        return ChannelFlag(self.mem.get_unsigned(address + offset, size))

    def get_count(self, address: int, type: ContainerType) -> int:
        offset, size = self.offset[type]['count']
        return self.mem.get_unsigned(address + offset, size)

    def get_size(self, address: int, type: ContainerType) -> int:
        offset, size = self.offset[type]['size']
        return self.mem.get_unsigned(address + offset, size)

    def get_next(self, address: int, type: ContainerType) -> int:
        return address + self.get_size(address, type)

    def get_file_addresses(self, address: int, type: ContainerType) -> list[int]:
        header_size = self.offset[type]['contents']
        
        file_num = self.get_count(address, type)
        ptr = address + header_size
        adrs = []
        for i in range(0, file_num):
            adrs.append(ptr)
            ptr = self.get_next(ptr, type.child())

        return adrs

    def action(self, address: int) -> MHAction:
        joints = []
        for adr in self.get_file_addresses(address, ContainerType.ACTION):
            joints.append(self.joint(adr))
        return MHAction(joints)

    def joint(self, address: int) -> Joint:
        fcurves = []
        for adr in self.get_file_addresses(address, ContainerType.JOINT):
            fcurves.append(self.fcurve(adr))
        return Joint(fcurves)

    def fcurve(self, address: int) -> Fcurve:
        flag = self.get_flag(address, ContainerType.FCURVE)
        count = self.get_count(address, ContainerType.FCURVE)
        header_size = self.offset[ContainerType.FCURVE]['contents']
        
        keyframes = []
        for i in range(count):
            adr = address + header_size + KEYFRAME_SIZE * i
            keyframes.append(self.keyframe(adr, flag))

        return Fcurve(flag, keyframes)

    def keyframe(self, address: int, channel: ChannelFlag) -> KeyFrame:
        conv = self.conversion_coefficient(channel)
        x, t, v0, v1 = unpack(
            'hhhh', self.mem.get_slice_at(address, KEYFRAME_SIZE))
        x = x * conv
        v0 = v0 * conv
        v1 = v1 * conv
        return KeyFrame(x, t, v0, v1)

    def conversion_coefficient(self, flag: ChannelFlag) -> float:
        if flag in ChannelFlag.SCALE:
            return DISTANCE_CONVERSION_COEFF
        elif flag in ChannelFlag.EULER:
            return ANGLE_CONVERSION_COEFF
        elif flag in ChannelFlag.TRANSLATION:
            return DISTANCE_CONVERSION_COEFF
        elif flag in ChannelFlag.SCALE2:
            return SCALE2_CONVERSION_COEFF
        else:
            ValueError(flag)
