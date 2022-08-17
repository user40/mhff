import bpy
from collections import defaultdict
from itertools import chain
import io
from pmo import Pmo
import names


def create(pmo: io.BytesIO, name: str):
    meshes_data = Pmo(pmo).read()
    mesh_groups = defaultdict(list)
    for i, m in enumerate(meshes_data):
        for j, submesh in enumerate(m.mesh):
            obj = create_mesh(submesh, names.mesh_tmp(name, i, j))
            set_material(obj, m.materials[j], name)
            set_weight(obj, submesh.weights, m.bones[j])
            mesh_groups[m.mesh_groups[j]].append(obj)
    return join_meshes(mesh_groups, name)


def create_mesh(mesh_data, name):
    data = mesh_data.to_blender_coord()

    # Create a mesh and a mesh obj
    me = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(obj)
    index_max = max(data.vertices.keys())
    vertices = [data.vertices[i] for i in range(1 + index_max)]
    me.from_pydata(vertices, [], data.faces)

    # Set normal
    me.normals_split_custom_set_from_vertices(list(data.normals.values()))

    # Set uv
    uv_layer = me.uv_layers.new(name='UVMap')
    indecies = chain.from_iterable(data.faces)
    for idx, vert in zip(indecies, uv_layer.data):
        vert.uv = data.uvs[idx]

    return obj


def set_material(obj, material, name):
    # Set material
    mat_name = names.material(name, material)
    mat = bpy.data.materials.get(mat_name)
    if not mat:
        mat = bpy.data.materials.new(name=mat_name)
    obj.active_material = mat
    return obj


def set_weight(obj, weights, bone_list):
    TOTAL_WEIGHT = 128
    for v, ws in weights.items():
        for weight, bone in zip(ws, bone_list):
            name = names.bone(bone)
            if not name in obj.vertex_groups:
                obj.vertex_groups.new(name=name)
            obj.vertex_groups[name].add([v], weight/TOTAL_WEIGHT, 'REPLACE')


TOTAL_WEIGHT = 128


def join_meshes(mesh_groups, name):
    result = []
    for id, meshes in mesh_groups.items():
        ctx = bpy.context.copy()
        ctx['active_object'] = meshes[0]
        ctx['selected_editable_objects'] = meshes
        bpy.ops.object.join(ctx)
        meshes[0].name = names.mesh(name, id)
        result.append(meshes[0])
    return result
