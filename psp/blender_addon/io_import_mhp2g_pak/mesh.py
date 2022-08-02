import bpy
import bmesh
from itertools import chain
from mathutils import Vector
from structures import MeshData, SubMeshInfo

def create(meshes_data: list[MeshData], texture_data, skelton_data, name):
    meshes = []
    for i, m in enumerate(meshes_data):
        for j, (submesh, bone, material) in enumerate(zip(m.mesh, m.bones, m.materials)):
            name = f'Mesh{i:04d}_{j:03d}'
            obj = create_mesh(name, submesh, material)
            set_material(obj, material, i)
            set_weight(obj, submesh.weights, bone, skelton_data)
            meshes.append(obj)
    return meshes

def create_mesh(name, mesh_data, material):
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

def set_material(obj, material, i):
    # Set material
    obj.active_material = bpy.data.materials[f'Material{material:02d}']
    return obj
    
def set_weight(obj, weights, bone_list, skelton_data):
    for k in range(len(skelton_data)):
        obj.vertex_groups.new(name=f'Bone{k:03d}')
    for v, ws in weights.items():
        for w, bone_id in zip(ws, bone_list):
            obj.vertex_groups[bone_id].add([v], w/TOTAL_WEIGHT, 'REPLACE')

TOTAL_WEIGHT = 128