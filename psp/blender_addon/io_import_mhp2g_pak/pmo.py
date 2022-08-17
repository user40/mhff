import array
import io
import struct
import mathutils
from structures import (
    SubMeshInfo,
    MeshData,
)


class Pmo:
    def __init__(self, stream) -> None:
        self.pmo = stream
        
    def extend(self, stream) -> None:
        self.pmo = io.BytesIO(self.pmo.read() + stream.read())

    def read(self) -> list[MeshData]:
        type, version = struct.unpack('4s4s', self.pmo.read(8))
        if type == b'pmo\x00' and version == b'1.0\x00':
            return self.read_mh2()
        elif type == b'pmo\x00' and version == b'102\x00':
            return self.read_mh3()
        else:
            raise ValueError('Invalid PMO file')

    def read_mh2(self):
        pmo = self.pmo
        pmo_header = struct.unpack('I4f2H8I', pmo.read(0x38))
        scale = mathutils.Vector(pmo_header[2:5])
        meshes_data = []
        bone = [0] * 8
        for i in range(pmo_header[5]):
            pmo.seek(pmo_header[7] + i * 0x18)
            mesh_header = struct.unpack('2f2I4H', pmo.read(0x18))
            mesh, mesh_groups, bones, materials = [], [], [], []
            for j in range(mesh_header[6]):
                pmo.seek(pmo_header[8] + ((mesh_header[7] + j) * 0x10))
                sub_mesh_header = struct.unpack('2BH3I', pmo.read(0x10))
                # submesh
                pmo.seek(pmo_header[12] + sub_mesh_header[3])
                sub_mesh = self.run_ge(scale)
                mesh.append(sub_mesh)
                # bone
                pmo.seek(pmo_header[10] + sub_mesh_header[2] * 0x2)
                for _ in range(sub_mesh_header[1]):
                    k, l = struct.unpack('2B', pmo.read(0x2))
                    bone[k] = l
                bones.append(bone.copy())
                # material
                #material = struct.unpack('4I', pmo.read(16))[2]
                # pmo_header[11] -> mesh_group_tbl
                #
                pmo.seek(pmo_header[9] + mesh_header[5] + sub_mesh_header[0])
                mesh_group = struct.unpack('B', pmo.read(1))[0]
                mesh_groups.append(mesh_group)
                pmo.seek(pmo_header[11] + mesh_group * 0x10)
                material = struct.unpack('4I', pmo.read(16))[2]
                materials.append(material)
            meshes_data.append(MeshData(mesh, mesh_groups, bones, materials))
        return meshes_data

    def read_mh3(self):
        pmo = self.pmo
        pmo_header = struct.unpack('I4f2H8I', pmo.read(0x38))
        meshes_data = []
        bone = [0] * 8
        for i in range(pmo_header[5]):
            pmo.seek(pmo_header[7] + i * 0x30)
            mesh_header = struct.unpack('8f2I4H', pmo.read(0x30))
            scale = mesh_header[:3]
            mesh, mesh_groups, bones, materials = [], [], [], []
            for j in range(mesh_header[12]):
                pmo.seek(pmo_header[8] + ((mesh_header[13] + j) * 0x10))
                sub_mesh_header = struct.unpack('2BH3I', pmo.read(0x10))
                # submesh
                pmo.seek(pmo_header[12] + sub_mesh_header[3])
                sub_mesh = self.run_ge(scale)
                mesh.append(sub_mesh)
                # bone
                pmo.seek(pmo_header[10] + sub_mesh_header[2] * 0x2)
                for _ in range(sub_mesh_header[1]):
                    k, l = struct.unpack('2B', pmo.read(0x2))
                    bone[k] = l
                bones.append(bone.copy())
                # material
                mesh_group = mesh_header[11] + sub_mesh_header[0]
                mesh_groups.append(mesh_group)
                pmo.seek(pmo_header[11] + (mesh_header[11] + sub_mesh_header[0]) * 16)
                material = struct.unpack('4I', pmo.read(16))[2]
                materials.append(material)
            meshes_data.append(MeshData(mesh, mesh_groups, bones, materials))
        return meshes_data

    def run_ge(self, scale=(1, 1, 1)):
        pmo = self.pmo
        file_address = pmo.tell()
        index_offset = 0
        vertices = {}
        normals = {}
        uvs = {}
        colors = {}
        weights = {}
        faces = []
        vertex_address = None
        index_address = None
        vertex_format = None
        position_trans = None
        normal_trans = None
        color_trans = None
        texture_trans = None
        weight_trans = None
        index_format = None
        face_order = None
        while True:
            command = array.array('I', pmo.read(4))[0]
            command_type = command >> 24
            # NOP - No Operation
            if command_type == 0x00:
                pass
            # VADDR - Vertex Address (BASE)
            elif command_type == 0x01:
                if vertex_address is not None:
                    index_offset = len(vertices)
                vertex_address = file_address + (command & 0xffffff)
            # IADDR - Index Address (BASE)
            elif command_type == 0x02:
                index_address = file_address + (command & 0xffffff)
            # PRIM - Primitive Kick
            elif command_type == 0x04:
                primative_type = (command >> 16) & 7
                index_count = command & 0xffff
                command_address = pmo.tell()
                index = range(len(vertices) - index_offset,
                              len(vertices) + index_count - index_offset)
                if index_format is not None:
                    index = array.array(index_format)
                    pmo.seek(index_address)
                    index.fromfile(pmo, index_count)
                    index_address = pmo.tell()
                vertex_size = struct.calcsize(vertex_format)
                for i in index:
                    pmo.seek(vertex_address + vertex_size * i)
                    vertex = list(struct.unpack(
                        vertex_format, pmo.read(vertex_size)))
                    position = mathutils.Vector()
                    position.z = vertex.pop() / position_trans * scale[2]
                    position.y = vertex.pop() / position_trans * scale[1]
                    position.x = vertex.pop() / position_trans * scale[0]
                    vertices[i + index_offset] = position
                    if normal_trans is not None:
                        normal = mathutils.Vector()
                        normal.z = vertex.pop() / normal_trans
                        normal.y = vertex.pop() / normal_trans
                        normal.x = vertex.pop() / normal_trans
                        normals[i + index_offset] = normal
                    if color_trans is not None:
                        colors[i + index_offset] = color_trans(vertex.pop())
                    if texture_trans is not None:
                        texture = mathutils.Vector()
                        texture.y = vertex.pop() / texture_trans
                        texture.x = vertex.pop() / texture_trans
                        uvs[i + index_offset] = texture.to_2d()
                    if weight_trans is not None:
                        weights[i + index_offset] = vertex[:]
                pmo.seek(command_address)
                r = range(index_count - 2)
                if primative_type == 3:
                    r = range(0, index_count, 3)
                elif primative_type != 4:
                    ValueError('Unsupported primative type: 0x%02X' %
                               primative_type)
                for i in r:
                    vert3 = index[i+2] + index_offset
                    if ((i + face_order) % 2) or ((primative_type == 3) and face_order):
                        vert2 = index[i] + index_offset
                        vert1 = index[i+1] + index_offset
                    else:
                        vert1 = index[i] + index_offset
                        vert2 = index[i+1] + index_offset
                    faces.append((vert1, vert2, vert3))
            # RET - Return from Call
            elif command_type == 0x0b:
                break
            # BASE - Base Address Register
            elif command_type == 0x10:
                pass
            # VTYPE - Vertex Type
            elif command_type == 0x12:
                vertex_format = ''
                weight = (command >> 9) & 3
                if weight != 0:
                    count = ((command >> 14) & 7) + 1
                    vertex_format += str(count) + (None, 'B', 'H', 'f')[weight]
                    weight_trans = (None, 0x80, 0x8000, 1)[weight]
                bypass_transform = (command >> 23) & 1
                texture = command & 3
                if texture != 0:
                    vertex_format += (None, '2B', '2H', '2f')[texture]
                    texture_trans = 1
                    if not bypass_transform:
                        texture_trans = (None, 0x80, 0x8000, 1)[texture]
                color = (command >> 2) & 7
                if color != 0:
                    vertex_format += (None, None, None, None,
                                      'H', 'H', 'H', 'I')[color]
                    color_trans = (None, None, None, None, convert_rgb565,
                                   convert_rgba5, convert_rgba4, convert_rgba8)[color]
                normal = (command >> 5) & 3
                if normal != 0:
                    vertex_format += (None, '3b', '3h', '3f')[normal]
                    normal_trans = 1
                    if not bypass_transform:
                        normal_trans = (None, 0x7f, 0x7fff, 1)[normal]
                position = (command >> 7) & 3
                if position != 0:
                    if bypass_transform:
                        # TODO: handle Z clamping
                        vertex_format += (None, '2bB', '2hH', '3f')[position]
                        position_trans = 1
                    else:
                        vertex_format += (None, '3b', '3h', '3f')[position]
                        position_trans = (None, 0x7f, 0x7fff, 1)[position]
                index_format = (None, 'B', 'H', 'I')[(command >> 11) & 3]
                if (command >> 18) & 7 > 0:
                    raise ValueError('Can not handle morphing')
            # ??? - Offset Address (BASE)
            elif command_type == 0x13:
                pass
            # ??? - Origin Address (BASE)
            elif command_type == 0x14:
                pass
            # FFACE - Front Face Culling Order
            elif command_type == 0x9b:
                face_order = command & 1
            else:
                raise ValueError('Unknown GE command: 0x%02X' % command_type)
        return SubMeshInfo(vertices, normals, uvs, colors, weights, faces)


def convert_rgb565(i):
    r = round((i & 31) * (255 / 31))
    g = round((i >> 5 & 63) * (255 / 63))
    b = round((i >> 11 & 31) * (255 / 31))
    return mathutils.Color((r, g, b))


def convert_rgba5(i):
    r = round((i & 31) * (255 / 31))
    g = round((i >> 5 & 31) * (255 / 31))
    b = round((i >> 10 & 31) * (255 / 31))
    return mathutils.Color((r, g, b))


def convert_rgba4(i):
    r = (i & 15) * 17
    g = (i >> 4 & 15) * 17
    b = (i >> 8 & 15) * 17
    return mathutils.Color((r, g, b))


def convert_rgba8(i):
    r = i & 255
    g = i >> 8 & 255
    b = i >> 16 & 255
    return mathutils.Color((r, g, b))
