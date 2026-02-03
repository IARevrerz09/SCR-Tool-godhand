# File: scr_tools/operators.py
"""
Additional operators dan utilities
"""

import bpy
from bpy.types import Operator

class SCR_OT_validate_mesh(Operator):
    """Validate mesh untuk export"""
    bl_idname = "scr.validate_mesh"
    bl_label = "Validate Mesh"
    bl_description = "Check if mesh is valid for SCR export"
    
    def execute(self, context):
        obj = context.active_object
        
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "Select a mesh object")
            return {'CANCELLED'}
        
        mesh = obj.data
        issues = []
        
        # Check vertices
        if len(mesh.vertices) == 0:
            issues.append("No vertices!")
        
        # Check faces
        if len(mesh.polygons) == 0:
            issues.append("No faces!")
        
        # Check non-triangles
        non_tri = [p for p in mesh.polygons if len(p.vertices) != 3]
        if non_tri:
            issues.append(f"{len(non_tri)} non-triangle faces (will be triangulated)")
        
        # Check UVs
        if not mesh.uv_layers.active:
            issues.append("No active UV layer")
        
        # Report
        if issues:
            msg = "\n".join(issues)
            self.report({'WARNING'}, msg)
        else:
            self.report({'INFO'}, "Mesh is valid for export!")
        
        return {'FINISHED'}
