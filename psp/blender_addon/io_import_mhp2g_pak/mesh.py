import bpy
import bmesh
from collections import defaultdict
from itertools import chain
from mathutils import Vector
from structures import MeshData, SubMeshInfo


def create(meshes_data: list[MeshData], name):
    mesh_groups = defaultdict(list)
    for i, m in enumerate(meshes_data):
        for j, submesh in enumerate(m.mesh):
            name = f'Mesh{i:04d}_{j:03d}'
            obj = create_mesh(name, submesh)
            set_material(obj, m.materials[j])
            set_weight(obj, submesh.weights, m.bones[j])
            print(mesh_groups)
            mesh_groups[m.mesh_groups[j]].append(obj)
    return join_meshes(mesh_groups)


def create_mesh(name, mesh_data):
    data = mesh_data.to_blender_coord(scale=0.01)

    # Create a mesh and a mesh obj
    me = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(obj)
    me.from_pydata(list(data.vertices.values()), [], data.faces)

    # Set normal
    me.normals_split_custom_set_from_vertices(list(data.normals.values()))

    # Set uv
    uv_layer = me.uv_layers.new(name='UVMap')
    indecies = chain.from_iterable(data.faces)
    for idx, vert in zip(indecies, uv_layer.data):
        vert.uv = data.uvs[idx]

    return obj


def set_material(obj, material):
    # Set material
    obj.active_material = bpy.data.materials[f'Material{material:02d}']
    return obj


def set_weight(obj, weights, bone_list):
    for v, ws in weights.items():
        for weight, bone in zip(ws, bone_list):
            name = f'Bone{bone:03d}'
            if not name in obj.vertex_groups:
                obj.vertex_groups.new(name=name)
            obj.vertex_groups[name].add([v], weight/TOTAL_WEIGHT, 'REPLACE')


TOTAL_WEIGHT = 128


def join_meshes(mesh_groups):
    bpy.ops.object.mode_set(mode='OBJECT')
    result = []
    for id, meshes in mesh_groups.items():
        ctx = bpy.context.copy()
        ctx['active_object'] = meshes[0]
        ctx['selected_editable_objects'] = meshes
        bpy.ops.object.join(ctx)
        meshes[0].name = f'Mesh{id:02d}'
        result.append(meshes[0])
    return result
