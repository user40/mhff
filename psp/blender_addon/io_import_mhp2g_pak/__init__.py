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
    "version": (1, 0, 0),
    "blender": (2, 80, 0),
    "location": "File > Import > MHP pak (.pak)",
    "description": "Imports MHP pak",
    "warning": '',
    "category": "Import-Export",
}


class PakFileInputs(bpy.types.PropertyGroup):
    is_3rd: BoolProperty()
    name: StringProperty()
    use_pak_pak0: BoolProperty()
    use_pak_pmo: BoolProperty()
    use_pak_tmh: BoolProperty()
    use_pak_pak3: BoolProperty()
    
    pak_pak0_index: IntProperty(default=0)
    pak_pmo_index: IntProperty(default=1)
    pak_tmh_index: IntProperty(default=2)
    pak_pak3_index: IntProperty(default=3)
    
    pak_path: bpy.props.StringProperty(
        name="File",
        default="",
        description=".pak file",
        maxlen=1024,
        subtype="FILE_PATH",
    )
    
    pak0_path: bpy.props.StringProperty(
        name="File",
        default="",
        description=".pak file",
        maxlen=1024,
        subtype="FILE_PATH",
    )
    
    pmo_path: bpy.props.StringProperty(
        name="File",
        default="",
        description=".pak file",
        maxlen=1024,
        subtype="FILE_PATH",
    )
    
    tmh_path: bpy.props.StringProperty(
        name="File",
        default="",
        description=".pak file",
        maxlen=1024,
        subtype="FILE_PATH",
    )
    
    pak3_path: bpy.props.StringProperty(
        name="File",
        default="",
        description=".pak file",
        maxlen=1024,
        subtype="FILE_PATH",
    )


class PakImporterPanel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Import MHP2G models"
    bl_idname = "OBJECT_PT_pakimporter"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    def draw(self, context):
        layout = self.layout
        inputs = context.scene.pak_file_inputs
        layout.prop(inputs, "name", text='Object Name:')
        layout.label(text=".pak file:")
        layout.prop(inputs, "pak_path")
        layout.separator()
        
        # Skelton
        layout.label(text="Skelton:")
        spl = layout.split()
        checkbox = spl.column()
        checkbox.prop(inputs, "use_pak_pak0", text="Use .pak file")
        index = spl.column()
        index.prop(inputs, "pak_pak0_index", text="file index")
        path = layout.row()
        path.prop(inputs, "pak0_path")
        
        index.active = inputs.use_pak_pak0
        path.active = not inputs.use_pak_pak0
        layout.separator()
        
        # Mesh
        layout.label(text="Mesh:")
        spl = layout.split()
        checkbox = spl.column()
        checkbox.prop(inputs, "use_pak_pmo", text="Use .pak file")
        index = spl.column()
        index.prop(inputs, "pak_pmo_index", text="file index")
        path = layout.row()
        path.prop(inputs, "pmo_path")
        
        index.active = inputs.use_pak_pmo
        path.active = not inputs.use_pak_pmo
        layout.separator()
        
        # Texture
        layout.label(text="Texure:")
        spl = layout.split()
        checkbox = spl.column()
        checkbox.prop(inputs, "use_pak_tmh", text="Use .pak file")
        index = spl.column()
        index.prop(inputs, "pak_tmh_index", text="file index")
        path = layout.row()
        path.prop(inputs, "tmh_path")
        
        index.active = inputs.use_pak_tmh
        path.active = not inputs.use_pak_tmh
        layout.separator()
        
        # Animation
        layout.label(text="Animation:")
        spl = layout.split()
        checkbox = spl.column()
        checkbox.prop(inputs, "use_pak_pak3", text="Use .pak file")
        index = spl.column()
        index.prop(inputs, "pak_pak3_index", text="file index")
        path = layout.row()
        path.prop(inputs, "pak3_path")
        
        index.active = inputs.use_pak_pak3
        path.active = not inputs.use_pak_pak3
        layout.separator()
        
        layout.operator("import_scene.pak")


class IMPORT_OT_pak(bpy.types.Operator):
    bl_idname = 'import_scene.pak'
    bl_label = 'Import MHP pak'
    bl_description = 'Import a Monster Hunter Portable Pak file'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        #pakloader.load_pak(context.scene.pak_file_inputs.pak_path)
        inputs = context.scene.pak_file_inputs
        pak0, pmo, tmh, pak3 = None, None, None, None
        if inputs.pak_path:
            pak = pakloader.Pak(inputs.pak_path)
        
        if inputs.use_pak_pak0:
            pak0 = pak.get_byte_streme(inputs.pak_pak0_index)
        elif inputs.pak0_path:
            pak0 = open(inputs.pak0_path, 'rb')

        if inputs.use_pak_pmo:
            pmo = pak.get_byte_streme(inputs.pak_pmo_index)        
        elif inputs.pmo_path:
            pmo = open(inputs.pmo_path, 'rb')

        if inputs.use_pak_tmh:
            tmh = pak.get_byte_streme(inputs.pak_tmh_index)                
        elif inputs.tmh_path:
            tmh = open(inputs.tmh_path, 'rb')

        if inputs.use_pak_pak3:
            pak3 = pak.get_byte_streme(inputs.pak_pak3_index)              
        if inputs.pak3_path:
            pak3 = open(inputs.pak3_path, 'rb')
        
        pakloader.load_files(inputs.name, pak0, pmo, tmh, pak3, inputs.is_3rd)
        return {'FINISHED'}


classes = (
    PakFileInputs,
    PakImporterPanel,
    IMPORT_OT_pak
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.pak_file_inputs = bpy.props.PointerProperty(
        type=PakFileInputs)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.pak_file_inputs


if __name__ == "__main__":
    register()
