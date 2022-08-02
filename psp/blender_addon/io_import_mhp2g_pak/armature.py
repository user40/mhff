import bpy
from mathutils import Vector
import utils
import names


def create(skelton_data, name):
    # Create an armature
    bpy.ops.object.add(type='ARMATURE', enter_editmode=True,
                       location=(0, 0, 0))
    amt = bpy.context.object
    amt.name = names.armature(name)

    # Create bones
    bone_names = [names.bone(i) for i in range(len(skelton_data))]
    for name in bone_names:
        create_bone(amt, name)

    # Parenting and Positioning
    bpy.ops.object.mode_set(mode='EDIT')
    for i, d in enumerate(skelton_data):
        b = amt.data.edit_bones[bone_names[i]]
        location = Vector(utils.to_blender_location(d.location))
        b.head = b.head + Vector(location)
        b.tail = b.tail + Vector(location)
        if d.parent_idx != -1:
            b.parent = amt.data.edit_bones[bone_names[d.parent_idx]]
            b.head = b.head + b.parent.head
            b.tail = b.tail + b.parent.head

    # Set relationship
    for name in bone_names:
        b = amt.data.edit_bones[name]
        b.inherit_scale = 'ALIGNED'

    bpy.ops.object.mode_set(mode='OBJECT')
    return amt


def create_bone(armature, name):
    bpy.ops.object.mode_set(mode='EDIT')
    # Create a born
    b = armature.data.edit_bones.new(name)
    b.head = (0, 0, 0)
    b.tail = (0, 1, 0)
    b.roll = 0

    # Set rotation mode
    bpy.ops.object.mode_set(mode='POSE')
    armature.pose.bones[name].rotation_mode = 'XYZ'

    return b


def set_transform(joint, joint_data):
    joint.scale = utils.to_blender_scale(joint_data.scale)
    joint.rotation_euler = utils.to_blender_angle(joint_data.angle)
    joint.location = utils.to_blender_location(joint_data.location)
