from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, IntFlag
from collections.abc import Iterator


class SkeltonData(list):
    '''A list of JointData'''

    def index_iter(self, root_idx) -> Iterator[int]:
        stack = []
        stack.append(root_idx)
        while stack:
            idx = stack.pop()
            bone = self[idx]
            yield idx
            if bone.sibling_idx != -1:
                stack.append(bone.sibling_idx)
            if bone.child_idx != -1:
                stack.append(bone.child_idx)

    def iter(self, root_idx) -> Iterator[SkeltonData]:
        stack = []
        stack.append(root_idx)
        while stack:
            idx = stack.pop()
            bone = self[idx]
            yield bone
            if bone.sibling_idx != -1:
                stack.append(bone.sibling_idx)
            if bone.child_idx != -1:
                stack.append(bone.child_idx)

    def subskelton_root_idx(self) -> int:
        d = {}
        for j in self:
            id = j.subskelton_id
            if not id in d.keys():
                d[id] = j.idx
        return d


@dataclass
class JointData:
    # field_00
    # field_04
    # next_offset: int
    idx: int
    parent_idx: int
    child_idx: int
    sibling_idx: int
    scale: int
    angle: int
    location: int
    # ffffffff: int
    subskelton_id: int


class ChannelFlag(IntFlag):
    SCALE_X = 0x1
    SCALE_Y = 0x2
    SCALE_Z = 0x4
    EULER_X = 0x8
    EULER_Y = 0x10
    EULER_Z = 0x20
    TRANSLATION_X = 0x40
    TRANSLATION_Y = 0x80
    TRANSLATION_Z = 0x100
    SCALE = SCALE_X | SCALE_Y | SCALE_Z
    EULER = EULER_X | EULER_Y | EULER_Z
    TRANSLATION = TRANSLATION_X | TRANSLATION_Y | TRANSLATION_Z


@dataclass
class KeyFrame:
    x: int
    t: int
    v0: int
    v1: int


@dataclass
class Fcurve:
    channel: ChannelFlag
    keyframes: list[KeyFrame]


@dataclass
class Joint:
    channels: list[Fcurve]


@dataclass
class MHAction:
    joints: list[Joint]


@dataclass
class SubMeshInfo:
    vertices: dict
    normals: dict
    uvs: dict
    colors: dict
    weights: dict
    faces: list

    def to_blender_coord(self, scale):
        vs = {k: v.zxy * scale for k, v in self.vertices.items()}
        ns = {k: n.zxy for k, n in self.vertices.items()}
        return SubMeshInfo(vs, ns, self.uvs, self.colors, self.weights, self.faces)


@dataclass
class MeshData:
    mesh: list[SubMeshInfo]
    mesh_groups: list[int]
    bones: list[list[int]]
    materials: list[int]
