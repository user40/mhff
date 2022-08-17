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


def load_files(name, pak0=None, pmo=None, tmh=None, pak3=None, version=Version.SECOND_G):
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
