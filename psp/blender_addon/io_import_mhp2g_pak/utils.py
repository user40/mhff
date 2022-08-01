'''ゲーム内の座標をBlender用の座標に変換する'''

RATIO = 0.01

def to_blender_scale(v: list[float]) -> list[float]:
    return (v[2], v[0], v[1])

def to_blender_angle(v: list[float]) -> list[float]:
    return (v[2], v[0], v[1])

def to_blender_location(v: list[float]) -> list[float]:
    return (v[2]*RATIO, v[0]*RATIO, v[1]*RATIO)

def to_blender(v: list[float]) -> list[float]:
    '''(scale, rotation, location)'''
    (v[2], v[0], v[1], v[5], v[3], v[4], v[8]*RATIO, v[6]*RATIO, v[7]*RATIO)