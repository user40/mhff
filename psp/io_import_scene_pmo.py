import array
from dataclasses import dataclass
import struct

import bpy
import bmesh
import mathutils
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty


@dataclass
class SubMeshInfo:
    vertices: dict
    normals: dict
    uvs: dict
    colors: dict
    weights: dict
    faces: dict


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


def run_ge(pmo, scale=(1, 1, 1)):
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
                vert1 = index[i] + index_offset
                vert2 = index[i+1] + index_offset
                vert3 = index[i+2] + index_offset
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
            face_order = command & 1  # TODO: handle face culling
        else:
            raise ValueError('Unknown GE command: 0x%02X' % command_type)
    return SubMeshInfo(vertices, normals, uvs, colors, weights, faces)


def change_coordinate_system(info: SubMeshInfo, scale):
    for v in info.vertices.values():
        v.xyz = v.zxy * scale
    for n in info.vertices.values():
        n.xyz = n.zxy
    return info


def create_mesh(mesh, num, bones):
    me = bpy.data.meshes.new('Mesh%04d' % num)
    ob = bpy.data.objects.new('Mesh%04d' % num, me)
    BONE_NUM = 50
    vgs = []
    for k in range(BONE_NUM):
        vgs.append(ob.vertex_groups.new(name=f'Bone{k:02d}'))
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.layers.deform.verify()
    dl = bm.verts.layers.deform.active
    for submesh, bone in zip(mesh, bones):
        vs = {}
        for j, v in submesh.vertices.items():
            vs[j] = bm.verts.new(v)
        for face in submesh.faces:
            face = bm.faces.new((vs[face[0]], vs[face[1]], vs[face[2]]))
        for j, ws in submesh.weights.items():
            for w, b in zip(ws, bone):
                vs[j][dl][b] = w/128
    bm.to_mesh(me)
    bm.free()
    bpy.context.collection.objects.link(ob)


def load_pmo_mh3(pmo):
    pmo_header = struct.unpack('I4f2H8I', pmo.read(0x38))
    for i in range(pmo_header[5]):
        pmo.seek(pmo_header[7] + i * 0x30)
        mesh_header = struct.unpack('8f2I4H', pmo.read(0x30))
        mesh = []
        for j in range(mesh_header[12]):
            pmo.seek(pmo_header[8] + ((mesh_header[13] + j) * 0x10))
            vertex_group_header = struct.unpack('2BH3I', pmo.read(0x10))
            pmo.seek(pmo_header[12] + vertex_group_header[3])
            vertex_group = run_ge(pmo)
            mesh.append(vertex_group)
        create_mesh(mesh, i)


def load_pmo_mh2(pmo, blender_scale):
    pmo_header = struct.unpack('I4f2H8I', pmo.read(0x38))
    scale = mathutils.Vector(pmo_header[2:5])
    bone = [0] * 8
    for i in range(pmo_header[5]):
        pmo.seek(pmo_header[7] + i * 0x18)
        mesh_header = struct.unpack('2f2I4H', pmo.read(0x18))
        mesh = []
        bones = []
        for j in range(mesh_header[6]):
            pmo.seek(pmo_header[8] + ((mesh_header[7] + j) * 0x10))
            sub_mesh_header = struct.unpack('2BH3I', pmo.read(0x10))
            pmo.seek(pmo_header[12] + sub_mesh_header[3])
            sub_mesh = change_coordinate_system(
                run_ge(pmo, scale), blender_scale)
            mesh.append(sub_mesh)

            pmo.seek(pmo_header[10] + sub_mesh_header[2] * 0x2)
            for _ in range(sub_mesh_header[1]):
                k, l = struct.unpack('2B', pmo.read(0x2))
                bone[k] = l
            bones.append(bone.copy())
        create_mesh(mesh, i, bones)


def load_pmo(pmo_file):
    with open(pmo_file, 'rb') as pmo:
        type, version = struct.unpack('4s4s', pmo.read(8))
        if type == b'pmo\x00' and version == b'102\x00':
            load_pmo_mh3(pmo)
        elif type == b'pmo\x00' and version == b'1.0\x00':
            SCALE = 0.01
            load_pmo_mh2(pmo, SCALE)
        else:
            raise ValueError('Invalid PMO file')


bl_info = {
    'name': 'Import Monster Hunter Objects',
    'author': 'Seth VanHeulen',
    'version': (0, 1),
    'blender': (2, 80, 0),
    'location': 'File > Import > Monster Hunter Object (.pmo)',
    'description': 'Imports a PMO object from Monster Hunter',
    'category': 'Import-Export'
}


class IMPORT_OT_pmo(bpy.types.Operator, ImportHelper):
    bl_idname = 'import_scene.pmo'
    bl_label = 'Import PMO'
    bl_description = 'Import a Monster Hunter PMO file'
    bl_options = {'REGISTER', 'UNDO'}
    filepath = StringProperty(
        name='File Path', description='File path used for importing the PMO file', maxlen=1024, default='')

    def execute(self, context):
        load_pmo(self.filepath)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}


def menu_func(self, context):
    self.layout.operator(IMPORT_OT_pmo.bl_idname,
                         text='Monster Hunter Object (.pmo)')


def register():
    bpy.utils.register_class(IMPORT_OT_pmo)
    bpy.types.TOPBAR_MT_file_import.append(menu_func)


def unregister():
    bpy.utils.unregister_class(IMPORT_OT_pmo)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func)


if __name__ == '__main__':
    register()
