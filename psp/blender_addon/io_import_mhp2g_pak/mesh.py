import bpy
import bmesh

def create(meshes_data, texture_data, skelton_data, name):
    meshes = []
    for m in meshes_data:
        mesh = create_mesh(m.mesh, m.index, m.bones, len(skelton_data))
        meshes.append(mesh)
    return meshes

def create_mesh(mesh, num, bones, bone_count):
    me = bpy.data.meshes.new('Mesh%04d' % num)
    ob = bpy.data.objects.new('Mesh%04d' % num, me)
    vgs = []
    for k in range(bone_count):
        vgs.append(ob.vertex_groups.new(name=f'Bone{k:03d}'))
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.layers.deform.verify()
    dl = bm.verts.layers.deform.active
    for submesh, bone in zip(mesh, bones):
        submesh = submesh.to_blender_coord(0.01)
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
    return ob