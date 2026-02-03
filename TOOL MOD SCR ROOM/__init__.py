# File: scr_tools/__init__.py
"""
SCR Tools - Addon untuk import/export God Hand SCR format
Versi: 1.0.0
Author:IARevrerz09
License: MIT
"""

# ============================================================================
# BLENDER INFO - WAJIB!
# ============================================================================
bl_info = {
    "name": "SCR Tools",
    "description": "Import/Export tools untuk format SCR (God Hand models)",
    "author": "IARevrerz09",
    "version": (1, 0, 0),
    "blender": (3, 4, 0),
    "location": "File > Import/Export",
    "category": "Import-Export",
    "support": "COMMUNITY",
    "doc_url": "https://github.com/IARevrerz09/SCR-Tool-godhand/TOOL MOD SCR ROOM",
    "tracker_url": "https://github.com/IARevrerz09/SCR-Tool-godhand/TOOL MOD SCR ROOM/issues",
}

# ============================================================================
# IMPORTS
# ============================================================================
import bpy
from bpy.props import StringProperty, BoolProperty
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper, ExportHelper

# Import modul-modul custom
from . import scr_parser
from . import import_scr
from . import export_scr
from . import ui
from . import operators

# ============================================================================
# OPERATOR: IMPORT
# ============================================================================
class IMPORT_OT_scr(Operator, ImportHelper):
    """Import file SCR"""
    bl_idname = "import_scene.scr"
    bl_label = "Import SCR"
    bl_options = {'REGISTER', 'UNDO'}
    
    # File extension yang bisa di-import
    filename_ext = ".scr"
    filter_glob: StringProperty(
        default="*.scr;*.md",
        options={'HIDDEN'}
    )
    
    # Properties - options untuk user
    import_normals: BoolProperty(
        name="Import Normals",
        description="Import vertex normals dari file",
        default=True
    )
    
    import_uvs: BoolProperty(
        name="Import UVs",
        description="Import UV coordinates",
        default=True
    )
    
    import_colors: BoolProperty(
        name="Import Colors",
        description="Import vertex colors",
        default=True
    )
    
    import_weights: BoolProperty(
        name="Import Weights",
        description="Import bone weights",
        default=True
    )
    
    def execute(self, context):
        """Dijalankan saat user klik OK"""
        return import_scr.load(
            self,
            context,
            self.filepath,
            self.import_normals,
            self.import_uvs,
            self.import_colors,
            self.import_weights
        )


# ============================================================================
# OPERATOR: EXPORT
# ============================================================================
class EXPORT_OT_scr(Operator, ExportHelper):
    """Export ke file SCR"""
    bl_idname = "export_scene.scr"
    bl_label = "Export SCR"
    bl_options = {'REGISTER', 'UNDO'}
    
    filename_ext = ".scr"
    filter_glob: StringProperty(
        default="*.scr",
        options={'HIDDEN'}
    )
    
    export_normals: BoolProperty(
        name="Export Normals",
        description="Export vertex normals",
        default=True
    )
    
    export_uvs: BoolProperty(
        name="Export UVs",
        description="Export UV coordinates",
        default=True
    )
    
    export_colors: BoolProperty(
        name="Export Colors",
        description="Export vertex colors",
        default=True
    )
    
    def execute(self, context):
        """Dijalankan saat user klik OK"""
        return export_scr.save(
            self,
            context,
            self.filepath,
            self.export_normals,
            self.export_uvs,
            self.export_colors
        )


# ============================================================================
# MENU FUNCTIONS - Tambah ke File menu
# ============================================================================
def menu_func_import(self, context):
    """Tambah ke File > Import menu"""
    self.layout.operator(
        IMPORT_OT_scr.bl_idname,
        text="SCR Model (.scr)"
    )

def menu_func_export(self, context):
    """Tambah ke File > Export menu"""
    self.layout.operator(
        EXPORT_OT_scr.bl_idname,
        text="SCR Model (.scr)"
    )


# ============================================================================
# REGISTRATION - PENTING!
# ============================================================================
# Daftar semua class yang ingin register
classes = (
    IMPORT_OT_scr,
    EXPORT_OT_scr,
    ui.SCR_TOOLS_PT_panel,
    operators.SCR_OT_validate_mesh,
)

def register():
    """Dipanggil saat addon di-enable"""
    print("\n" + "="*70)
    print("[SCR TOOLS] REGISTERING ADDON")
    print("="*70)
    
    # Register semua class
    for cls in classes:
        print(f"  ✓ Registering {cls.__name__}")
        bpy.utils.register_class(cls)
    
    # Register properties
    ui.register_properties()
    
    # Tambah ke menu
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    
    print("[SCR TOOLS] ✓ Addon registered successfully!")
    print("="*70 + "\n")


def unregister():
    """Dipanggil saat addon di-disable"""
    print("\n" + "="*70)
    print("[SCR TOOLS] UNREGISTERING ADDON")
    print("="*70)
    
    # Unregister properties
    ui.unregister_properties()
    
    # Hapus dari menu
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    
    # Unregister semua class (urutan terbalik!)
    for cls in reversed(classes):
        print(f"  ✓ Unregistering {cls.__name__}")
        bpy.utils.unregister_class(cls)
    
    print("[SCR TOOLS] ✓ Addon unregistered!")
    print("="*70 + "\n")


# Entry point (required by Python)
if __name__ == "__main__":
    register()
    
