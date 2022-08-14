import bpy
import pak3
from structures import (
    Joint,
    MHAction,
    SkeltonData
)
import names


def create(action_data: MHAction, action_id: int, skelton_data: SkeltonData, name: str):
    action = bpy.data.actions.new(names.action(name, action_id))
    action.use_fake_user = True

    subskelton_id = get_subskelton_id(action_id)
    root_idx = skelton_data.subskelton_root_idx()[subskelton_id]

    idx = 0
    for joint in skelton_data.iter(root_idx):
        if joint.subskelton_id == subskelton_id or joint == 0xffffffff:
            
            print(joint.idx)
            
            set_fcurves(action, action_data.joints[idx], joint.idx)
            idx = idx + 1


def set_fcurves(action, joint_data: Joint, bone_idx):
    for c in joint_data.channels:
        # Add a Fcurve
        data_path, index, coeff = channel_data[c.channel]
        data_path = f'pose.bones["{names.bone(bone_idx)}"]' + data_path
        fcurve = action.fcurves.new(data_path, index=index)

        is_first = True
        for kf in c.keyframes:
            # Add a keyframe
            keyframe = fcurve.keyframe_points.insert(kf.t, kf.x * coeff)

            # Modify the handles
            if is_first:
                prev_keyframe = keyframe
                prev_x = kf.x
                prev_t = kf.t
                prev_v1 = kf.v1
                is_first = False
                continue

            dt = kf.t - prev_t
            prev_keyframe.handle_right = (
                prev_t + 1/3*dt, (prev_x + prev_v1 * (1+dt/3)) * coeff)
            keyframe.handle_left = (
                kf.t - 1/3*dt, (kf.x - kf.v0 * (1-dt/3)) * coeff)

            prev_keyframe = keyframe
            prev_x = kf.x
            prev_t = kf.t
            prev_v1 = kf.v1


def get_subskelton_id(action_id):
    return action_id // 200


channel_data = dict([
    (pak3.ChannelFlag.SCALE_X, ('scale', 0, 1.0)),
    (pak3.ChannelFlag.SCALE_Y, ('scale', 2, 1.0)),
    (pak3.ChannelFlag.SCALE_Z, ('scale', 1, 1.0)),
    (pak3.ChannelFlag.EULER_X, ('rotation_euler', 0, 1.0)),
    (pak3.ChannelFlag.EULER_Y, ('rotation_euler', 2, 1.0)),
    (pak3.ChannelFlag.EULER_Z, ('rotation_euler', 1, -1.0)),
    (pak3.ChannelFlag.TRANSLATION_X, ('location', 0, 0.01)),
    (pak3.ChannelFlag.TRANSLATION_Y, ('location', 2, 0.01)),
    (pak3.ChannelFlag.TRANSLATION_Z, ('location', 1, -0.01)),
])
