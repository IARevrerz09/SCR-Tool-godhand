# File: scr_tools/ui.py
"""
UI Panel untuk SCR Tools
Menampilkan panel di 3D View sidebar
"""

import bpy
from bpy.types import Panel, Menu

class SCR_TOOLS_PT_panel(Panel):
    """Main panel untuk SCR Tools di 3D View"""
    bl_label = "SCR Tools"
    bl_idname = "SCR_TOOLS_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SCR Tools'
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        # ====================================================================
        # HEADER
        # ====================================================================
        row = layout.row()
        row.label(text="SCR Model Tools", icon='TOOL_SETTINGS')
        
        # ====================================================================
        # IMPORT SECTION
        # ====================================================================
        box = layout.box()
        box.label(text="Import", icon='IMPORT')
        
        import_op = box.operator(
            "import_scene.scr",
            text="Import SCR File",
            icon='MESH_DATA'
        )
        
        # Options
        col = box.column(align=True)
        col.label(text="Import Options:")
        col.prop(context.scene, "scr_import_normals", text="Normals")
        col.prop(context.scene, "scr_import_uvs", text="UVs")
        col.prop(context.scene, "scr_import_colors", text="Colors")
        col.prop(context.scene, "scr_import_weights", text="Weights")
        
        # ====================================================================
        # EXPORT SECTION
        # ====================================================================
        box = layout.box()
        box.label(text="Export", icon='EXPORT')
        
        active_obj = context.active_object
        
        if active_obj and active_obj.type == 'MESH':
            export_op = box.operator(
                "export_scene.scr",
                text="Export to SCR",
                icon='MESH_DATA'
            )
            
            # Info
            info_box = box.box()
            info_box.label(text=f"Object: {active_obj.name}")
            info_box.label(text=f"Vertices: {len(active_obj.data.vertices)}")
            info_box.label(text=f"Faces: {len(active_obj.data.polygons)}")
            
            # Options
            col = box.column(align=True)
            col.label(text="Export Options:")
            col.prop(context.scene, "scr_export_normals", text="Normals")
            col.prop(context.scene, "scr_export_uvs", text="UVs")
            col.prop(context.scene, "scr_export_colors", text="Colors")
        
        else:
            box.label(text="Select a mesh to export", icon='ERROR')
        
        # ====================================================================
        # INFO SECTION
        # ====================================================================
        box = layout.box()
        box.label(text="Information", icon='INFO')
        
        info_text = box.column(align=True)
        info_text.label(text="SCR Format Support:")
        info_text.label(text="• Version: 3 (God Hand)")
        info_text.label(text="• Max Meshes: 256")
        info_text.label(text="• Max Bones: 64")
        info_text.label(text="• Weights: Up to 3 per vertex")
        
        # ====================================================================
        # HELP SECTION
        # ====================================================================
        box = layout.box()
        box.label(text="Help", icon='QUESTION')
        
        col = box.column(align=True)
        col.label(text="1. Select a mesh object")
        col.label(text="2. Click 'Export to SCR'")
        col.label(text="3. Choose save location")
        col.label(text="4. Click 'Export SCR'")


# ============================================================================
# REGISTER SCENE PROPERTIES - Untuk simpan settings
# ============================================================================

def register_properties():
    """Register custom properties"""
    
    bpy.types.Scene.scr_import_normals = bpy.props.BoolProperty(
        name="Import Normals",
        description="Import vertex normals",
        default=True
    )
    
    bpy.types.Scene.scr_import_uvs = bpy.props.BoolProperty(
        name="Import UVs",
        description="Import UV coordinates",
        default=True
    )
    
    bpy.types.Scene.scr_import_colors = bpy.props.BoolProperty(
        name="Import Colors",
        description="Import vertex colors",
        default=True
    )
    
    bpy.types.Scene.scr_import_weights = bpy.props.BoolProperty(
        name="Import Weights",
        description="Import bone weights",
        default=True
    )
    
    bpy.types.Scene.scr_export_normals = bpy.props.BoolProperty(
        name="Export Normals",
        description="Export vertex normals",
        default=True
    )
    
    bpy.types.Scene.scr_export_uvs = bpy.props.BoolProperty(
        name="Export UVs",
        description="Export UV coordinates",
        default=True
    )
    
    bpy.types.Scene.scr_export_colors = bpy.props.BoolProperty(
        name="Export Colors",
        description="Export vertex colors",
        default=True
    )


def unregister_properties():
    """Unregister properties"""
    
    if hasattr(bpy.types.Scene, "scr_import_normals"):
        del bpy.types.Scene.scr_import_normals
    if hasattr(bpy.types.Scene, "scr_import_uvs"):
        del bpy.types.Scene.scr_import_uvs
    if hasattr(bpy.types.Scene, "scr_import_colors"):
        del bpy.types.Scene.scr_import_colors
    if hasattr(bpy.types.Scene, "scr_import_weights"):
        del bpy.types.Scene.scr_import_weights
    if hasattr(bpy.types.Scene, "scr_export_normals"):
        del bpy.types.Scene.scr_export_normals
    if hasattr(bpy.types.Scene, "scr_export_uvs"):
        del bpy.types.Scene.scr_export_uvs
    if hasattr(bpy.types.Scene, "scr_export_colors"):
        del bpy.types.Scene.scr_export_colors
