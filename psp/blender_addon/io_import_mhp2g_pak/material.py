import bpy
import names
from tmh import Tmh


def create(tmh, name):
    texture_data = Tmh(tmh).read()
    materials = []
    for i, image in enumerate(texture_data):
        image.name = names.image(name, i)
        mat = bpy.data.materials.get(names.material(name, i))
        if not mat:
            mat = bpy.data.materials.new(name=names.material(name, i))
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        bsdf.inputs['Specular'].default_value = 0
        texImage = mat.node_tree.nodes.new('ShaderNodeTexImage')
        texImage.image = image
        mat.node_tree.links.new(
            bsdf.inputs['Base Color'], texImage.outputs['Color'])
        mat.node_tree.links.new(
            bsdf.inputs['Alpha'], texImage.outputs['Alpha'])
        mat.blend_method = 'CLIP'
        mat.shadow_method = 'CLIP'
        materials.append(mat)
    return materials
