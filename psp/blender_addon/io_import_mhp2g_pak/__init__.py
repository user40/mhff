
import bpy
import os
import sys
from bpy.props import *
from bpy_extras.io_utils import ImportHelper

# Add addon dir to system modules directory
sys.path.append(os.path.dirname(__file__))

import pakloader

# addon description
bl_info = {
    "name": "Import Monster Hunter Portable 2G pak",
    "author": "Gahaku",
    "version": (1, 0, 5),
    "blender": (2, 80, 0),
    "location": "File > Import > MHP pak (.pak)",
    "description": "Imports MHP pak",
    "warning": '',
    "category": "Import-Export",
}


class IMPORT_OT_pak(bpy.types.Operator, ImportHelper):
    bl_idname = 'import_scene.pak'
    bl_label = 'Import MHP pak'
    bl_description = 'Import a Monster Hunter Portable Pak file'
    bl_options = {'REGISTER', 'UNDO'}
    filepath = StringProperty(
        name='File Path', description='File path used for importing the pak file', maxlen=1024, default='')

    def execute(self, context):
        pakloader.load_pak(self.filepath)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}


def menu_func(self, context):
    self.layout.operator(IMPORT_OT_pak.bl_idname,
                         text='MHP2G pak file (.pak)')


def register():
    bpy.utils.register_class(IMPORT_OT_pak)
    bpy.types.TOPBAR_MT_file_import.append(menu_func)


def unregister():
    bpy.utils.unregister_class(IMPORT_OT_pak)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func)


if __name__ == '__main__':
    register()

