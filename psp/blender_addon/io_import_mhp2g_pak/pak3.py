from struct import unpack
from structures import (
    ChannelFlag,
    KeyFrame,
    Fcurve,
    Joint,
    MHAction,
)
from utils import Memory


class Pak3:
    def __init__(self, streme):
        self.mem = Memory.from_bytes(streme.read())
        pass

    def read(self) -> dict[int, MHAction]:
        keys = self.keys()
        actions = {}
        for idx in keys:
            actions[idx] = self.get(idx)
        return actions

    def keys(self) -> list[int]:
        '''pak3ファイルの有効なインデックスの一覧を取得する。'''
        # ポインタテーブルたちのオフセットを読み出し
        counts = []
        offsets = []
        adr = 0
        while True:
            count = self.mem.get_u32(adr)
            offset = self.mem.get_u32(adr+4)
            if count == 0:
                break
            counts.append(count)
            offsets.append(offset)
            adr = adr + 8

        keys = []
        # 実際のインデックスを探索
        for i, offset in enumerate(offsets):
            for j in range(0, counts[i]):
                if self.mem.get_u32(offset+4*j) != 0xFFFFFFFF:
                    keys.append(100*i+j)

        return keys

    def get(self, index: int) -> MHAction:
        '''インデックスを指定してアクションを取得する。'''
        i = index // 100
        j = index % 100
        offset = self.mem.get_u32(i*8+4)
        address = self.mem.get_u32(offset+4*j)

        if address == 0xFFFFFFFF or address == None:
            return None

        return self.action(address)

    def get_flag(self, address: int) -> ChannelFlag:
        return ChannelFlag(self.mem.get_u16(address + OFFSET_FLAG))

    def get_count(self, address: int) -> int:
        return self.mem.get_u32(address + OFFSET_COUNT)

    def get_size(self, address: int) -> int:
        return self.mem.get_u32(address + OFFSET_SIZE)

    def get_next(self, address: int) -> int:
        size = self.mem.get_u32(address + OFFSET_SIZE)
        return address + size

    def get_file_addresses(self, address: int, is_root=False) -> list[int]:
        if is_root:
            header_size = ROOT_HEADER_SIZE
        else:
            header_size = HEADER_SIZE

        file_num = self.get_count(address)
        ptr = address + header_size
        adrs = []
        for i in range(0, file_num):
            adrs.append(ptr)
            ptr = self.get_next(ptr)

        return adrs

    def action(self, address: int) -> MHAction:
        joints = []
        for adr in self.get_file_addresses(address, is_root=True):
            joints.append(self.joint(adr))
        return MHAction(joints)

    def joint(self, address: int) -> Joint:
        fcurves = []
        for adr in self.get_file_addresses(address):
            fcurves.append(self.fcurve(adr))
        return Joint(fcurves)

    def fcurve(self, address: int) -> Fcurve:
        flag = self.get_flag(address)
        count = self.get_count(address)

        keyframes = []
        for i in range(count):
            adr = address + HEADER_SIZE + KEYFRAME_SIZE * i
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
        if flag in ChannelFlag.EULER:
            return ANGLE_CONVERSION_COEFF
        if flag in ChannelFlag.TRANSLATION:
            return DISTANCE_CONVERSION_COEFF


# キーフレームひとつのサイズ(バイト)
KEYFRAME_SIZE = 8

# 単位系換算用定数
DISTANCE_CONVERSION_COEFF = 0.0625
ANGLE_CONVERSION_COEFF = 0.0003834952076431364

# fcurve_container型のフィールドのオフセット
OFFSET_FLAG = 0
OFFSET_COUNT = 0x4
OFFSET_SIZE = 0x8
# fcurve_container型のヘッダサイズ
HEADER_SIZE = 0xc
# fcurve_container型のルートのヘッダサイズ
ROOT_HEADER_SIZE = 0x14
