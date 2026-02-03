# File: scr_tools/import_scr.py
"""
Import SCR file ke Blender scene
"""

import bpy
import bmesh
from mathutils import Vector
from . import scr_parser

def load(operator, context, filepath, import_normals=True, import_uvs=True, 
         import_colors=True, import_weights=True):
    """
    Main import function
    
    Args:
        operator: Operator instance (untuk report messages)
        context: Blender context
        filepath: Path ke SCR file
        import_normals: Import vertex normals
        import_uvs: Import UVs
        import_colors: Import vertex colors
        import_weights: Import bone weights
    
    Returns:
        {'FINISHED'} atau {'CANCELLED'}
    """
    
    try:
        print(f"\n[IMPORT SCR] Importing {filepath}")
        
        # Parse file
        with scr_parser.SCRParser(filepath) as parser:
            scr_data = parser.parse()
        
        if not scr_data.meshes:
            raise ValueError("No meshes found in file")
        
        # Create armature
        print("[IMPORT SCR] Creating armature...")
        armature_obj = create_armature(context)
        
        # Import each mesh
        for i, mesh_data in enumerate(scr_data.meshes):
            print(f"[IMPORT SCR] Importing mesh {i}...")
            import_mesh(
                context,
                armature_obj,
                mesh_data,
                f"Mesh_{i:02d}",
                import_normals,
                import_uvs,
                import_colors,
                import_weights
            )
        
        operator.report(
            {'INFO'},
            f"Imported {len(scr_data.meshes)} meshes successfully!"
        )
        print("[IMPORT SCR] ✓ Import completed!\n")
        return {'FINISHED'}
    
    except Exception as e:
        operator.report({'ERROR'}, f"Import failed: {str(e)}")
        print(f"[IMPORT SCR] ✗ Error: {e}\n")
        import traceback
        traceback.print_exc()
        return {'CANCELLED'}


def create_armature(context):
    """Create skeleton/armature"""
    
    armature_data = bpy.data.armatures.new("Armature")
    armature_obj = bpy.data.objects.new("Armature", armature_data)
    
    context.collection.objects.link(armature_obj)
    context.view_layer.objects.active = armature_obj
    
    # Create root bone
    bpy.ops.object.mode_set(mode='EDIT')
    
    root_bone = armature_obj.data.edit_bones.new("root")
    root_bone.head = Vector((0, 0, 0))
    root_bone.tail = Vector((0, 0.1, 0))
    
    bpy.ops.object.mode_set(mode='OBJECT')
    
    return armature_obj


def import_mesh(context, armature_obj, mesh_data, mesh_name,
                import_normals, import_uvs, import_colors, import_weights):
    """
    Import satu mesh
    """
    
    # Create mesh
    mesh = bpy.data.meshes.new(mesh_name)
    mesh_obj = bpy.data.objects.new(mesh_name, mesh)
    
    # Link ke scene
    context.collection.objects.link(mesh_obj)
    context.view_layer.objects.active = mesh_obj
    
    # Create bmesh
    bm = bmesh.new()
    
    # Add vertices ke bmesh
    vert_positions = []
    for vert in mesh_data.vertices:
        v = bm.verts.new((vert.x, vert.y, vert.z))
        vert_positions.append(v)
    
    bm.verts.ensure_lookup_table()
    
    # Create faces
    for face_data in mesh_data.faces:
        try:
            v0 = vert_positions[face_data[0]]
            v1 = vert_positions[face_data[1]]
            v2 = vert_positions[face_data[2]]
            bm.faces.new([v0, v1, v2])
        except IndexError:
            # Skip invalid faces
            pass
    
    bm.to_mesh(mesh)
    mesh.update()
    
    # Import normals
    if import_normals:
        normals_data = [v.normal for v in mesh_data.vertices]
        try:
            mesh.normals_split_custom_set_from_vertices(normals_data)
            mesh.use_auto_smooth = True
        except:
            pass
    
    # Import UVs
    if import_uvs:
        uv_layer = mesh.uv_layers.new(name="UVMap")
        for loop_idx, loop in enumerate(mesh.loops):
            vert_idx = loop.vertex_index
            if vert_idx < len(mesh_data.vertices):
                uv = mesh_data.vertices[vert_idx].uv
                uv_layer.data[loop_idx].uv = uv
    
    # Import colors
    if import_colors:
        color_layer = mesh.color_attributes.new(
            name="Col",
            type="FLOAT_COLOR",
            domain="POINT"
        )
        for i, vert in enumerate(mesh_data.vertices):
            color_layer.data[i].color = vert.color
    
    # Set parent to armature
    mesh_obj.parent = armature_obj
    
    # Add armature modifier
    modifier = mesh_obj.modifiers.new(name="Armature", type='ARMATURE')
    modifier.object = armature_obj
    
    # Import weights
    if import_weights:
        assign_vertex_weights(mesh_obj, mesh_data.vertices)
    
    bm.free()
    
    print(f"  ✓ Created mesh: {mesh_name}")


def assign_vertex_weights(mesh_obj, vertices_data):
    """
    Assign vertex groups (bone weights) ke mesh
    """
    
    for vert_idx, vert_data in enumerate(vertices_data):
        if not vert_data.weights:
            continue
        
        for bone_idx, weight in vert_data.weights:
            if weight <= 0:
                continue
            
            # Create vertex group jika belum ada
            group_name = f"Bone_{bone_idx:03d}"
            
            if group_name not in mesh_obj.vertex_groups:
                mesh_obj.vertex_groups.new(name=group_name)
            
            group = mesh_obj.vertex_groups[group_name]
            group.add([vert_idx], weight, 'ADD')
