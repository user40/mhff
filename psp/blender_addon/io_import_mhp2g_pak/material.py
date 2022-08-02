import bpy
import names


def create(texture_data, name):
    materials = []
    for i, image in enumerate(texture_data):
        image.name = names.image(name, i)
        mat = bpy.data.materials.new(name=names.material(name, i))
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        texImage = mat.node_tree.nodes.new('ShaderNodeTexImage')
        texImage.image = image
        mat.node_tree.links.new(
            bsdf.inputs['Base Color'], texImage.outputs['Color'])
        mat.node_tree.links.new(
            bsdf.inputs['Alpha'], texImage.outputs['Alpha'])
        materials.append(mat)
    return materials
