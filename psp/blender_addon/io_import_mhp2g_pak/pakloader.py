import bpy
import pathlib
from pak import Pak
from pak0 import Pak0
from pmo import Pmo
from tmh import Tmh
from pak3 import Pak3
import armature
import action
import mesh


def load_pak(filepath):
    name = get_name(filepath)
    outpath = ''

    pak = Pak(filepath)
    pak0 = pak.get_byte_streme(0)
    pmo = pak.get_byte_streme(1)
    tmh = pak.get_byte_streme(2)
    pak3 = pak.get_byte_streme(3)

    skelton_data = Pak0(pak0).read()
    mesh_data = Pmo(pmo).read()
    texture_data = Tmh(tmh).read(outpath)
    animation_data = Pak3(pak3).read()

    armature_name = armature.create(skelton_data, name)
    meshes = mesh.create(mesh_data, texture_data, skelton_data, name)
    for id, action_data in animation_data.items():
        action.create(action_data, id, skelton_data, name)
    
    amt = bpy.data.objects[armature_name]
    for mesh_ in meshes:
        mesh_.parent = amt


def get_name(filepath):
    # TODO
    return pathlib.Path(filepath).stem
