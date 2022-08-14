import bpy
import pathlib
from pak import Pak, FileType
from pak0 import Pak0
from pak3 import Pak3
import armature
import action
import material
import mesh
from structures import Version

def load_pak(filepath):
    name = get_name(filepath)
    outpath = ''

    pak = Pak(filepath)
    meshes = []
    skelton_data = None
    animation_data = None
    i, j, k, l = 0, 0, 0, 0
    for type_, file in pak.get_all_byte_stremes():
        print(type_)
        if type_ == FileType.PAK0:
            skelton_data = Pak0(file).read()
            amt = armature.create(skelton_data, name + f'{i}')
            for mesh_ in meshes:
                mesh_.modifiers.new('Armature', type='ARMATURE')
                mesh_.modifiers["Armature"].object = amt
                mesh_.parent = amt
            i = i + 1
        elif type_ == FileType.PMO:
            meshes = mesh.create(file, name + f'{j}')
            j = j + 1
        elif type_ == FileType.TMH:
            material.create(file, name + f'{k}')
            k = k + 1
        elif type_ == FileType.PAK3:
            animation_data = Pak3(file).read()
            for id, action_data in animation_data.items():
                action.create(action_data, id, skelton_data, name + f'{l}')
            l = l + 1

    bpy.context.scene.frame_start = 0
    bpy.context.scene.render.fps = 60
    bpy.context.scene.render.fps_base = 2
    

def load_files(name, pak0=None, pmo=None, tmh=None, pak3=None, is_third=False):
    #version = Version.SECOND_G
    version = Version.THIRD
    meshes = []
    if pmo:
        meshes = mesh.create(pmo, name)
    if tmh:
        material.create(tmh, name)
    if pak0:
        skelton_data = skelton_data = Pak0(pak0).read()
        amt = armature.create(skelton_data, name)
        for mesh_ in meshes:
            mesh_.modifiers.new('Armature', type='ARMATURE')
            mesh_.modifiers["Armature"].object = amt
            mesh_.parent = amt
        
        if pak3:
            animation_data = Pak3(pak3, version).read()
            for id, action_data in animation_data.items():
                action.create(action_data, id, skelton_data, name, version)


    bpy.context.scene.frame_start = 0
    bpy.context.scene.render.fps = 60
    bpy.context.scene.render.fps_base = 2


def get_name(filepath):
    # TODO
    return pathlib.Path(filepath).stem
