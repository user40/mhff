def mesh_tmp(name, i, j):
    return f'Mesh_tmp_{name}_{i:03d}_{j:03d}'


def mesh(name, i):
    return f'Mesh_{name}_{i:02d}'


def armature(name):
    return f'Armature_{name}'


def material(name, material):
    return f'Material_{name}_{material:02d}'


def image(name, i):
    return f'Image_{name}_{i:02d}'


def action(name, i):
    return f'Action_{name}_{i:03d}'


def bone(i):
    return f"Bone_{i:03d}"
