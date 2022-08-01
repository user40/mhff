from structures import SkeltonData, JointData
from memory import Memory


class Pak0:
    def __init__(self, streme):
        self.bin = Memory.from_bytes(streme.read())

    def read(self):
        joint_count = self.joint_count()
        adr = self.first_joint_offset()
        joint_data = []
        for idx in range(joint_count):
            joint_data.append(self.make_joint(adr))
            adr = adr + self.bin.get_u32(adr + OFFSETS["next_offset"])
        return SkeltonData(joint_data)
    
    def joint_count(self) -> int:
        count = self.bin.get_u32(OFFSETS["joint_count"])
        if self.bin.get_u32(OFFSETS["minus_one_flag"]) & 0x80000000 != 0:
            count = count - 1
        return count
    
    def first_joint_offset(self) -> int:
        return 0xc + self.bin.get_u32(0xc + 0x8)
    
    def make_joint(self, adr: int) -> JointData:
        idx = self.bin.get_i32(adr + OFFSETS["idx"])
        parentt_idx = self.bin.get_i32(adr + OFFSETS["parent_idx"])
        child_idx = self.bin.get_i32(adr + OFFSETS["child_idx"])
        sibling_idx = self.bin.get_i32(adr + OFFSETS["sibling_idx"])
        scale = self.bin.get_float_vec3(adr + OFFSETS["scale"])
        angle = self.bin.get_float_vec3(adr + OFFSETS["angle"])
        location = self.bin.get_float_vec3(adr + OFFSETS["location"])
        subskelton_id = self.bin.get_i32(adr + OFFSETS["subskelton_id"])
        return JointData(idx, parentt_idx, child_idx, sibling_idx, scale, angle, location, subskelton_id)


OFFSETS = dict(
    # Header構造体用オフセット
    minus_one_flag=0,
    joint_count=0x4,

    # pak0ファイルの先頭から１つ目の関節までのオフセット
    first_join=0,

    # Joint構造体用オフセット
    next_offset=0x8,
    idx=0xc,
    parent_idx=0x10,
    child_idx=0x14,
    sibling_idx=0x18,
    scale=0x1c,
    angle=0x2c,
    location=0x3c,
    subskelton_id=0x50,
)
