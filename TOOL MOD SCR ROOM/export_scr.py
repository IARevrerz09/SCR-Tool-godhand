# File: scr_tools/export_scr.py
"""
Export Blender mesh ke file SCR
"""

import bpy
import bmesh
import struct
import math
from mathutils import Vector
from . import scr_parser

def save(operator, context, filepath, export_normals=True, 
         export_uvs=True, export_colors=True):
    """
    Main export function
    
    Args:
        operator: Operator instance
        context: Blender context
        filepath: Output file path
        export_normals: Export vertex normals
        export_uvs: Export UV coordinates
        export_colors: Export vertex colors
    
    Returns:
        {'FINISHED'} atau {'CANCELLED'}
    """
    
    try:
        # Validate selection
        selected_obj = context.active_object
        
        if not selected_obj:
            raise ValueError("No object selected")
        
        if selected_obj.type != 'MESH':
            raise ValueError(f"Selected object is {selected_obj.type}, not MESH")
        
        print(f"\n[EXPORT SCR] Exporting {selected_obj.name} to {filepath}")
        
        # Prepare mesh data
        mesh_data = prepare_mesh_data(selected_obj, export_normals, export_uvs, export_colors)
        
        # Write to file
        print("[EXPORT SCR] Writing SCR file...")
        write_scr_file(filepath, selected_obj.name, mesh_data)
        
        operator.report({'INFO'}, f"Exported successfully to {filepath}")
        print("[EXPORT SCR] ✓ Export completed!\n")
        return {'FINISHED'}
    
    except Exception as e:
        operator.report({'ERROR'}, f"Export failed: {str(e)}")
        print(f"[EXPORT SCR] ✗ Error: {e}\n")
        import traceback
        traceback.print_exc()
        return {'CANCELLED'}


def prepare_mesh_data(obj, export_normals, export_uvs, export_colors):
    """
    Prepare mesh data dari Blender object
    
    Returns:
        {
            'name': str,
            'vertices': [...],
            'normals': [...],
            'uvs': [...],
            'colors': [...],
            'weights': [...],
            'material_index': int
        }
    """
    
    mesh = obj.data
    
    # Ensure triangulated
    print("[EXPORT SCR] Ensuring mesh is triangulated...")
    temp_mesh = mesh.copy()
    temp_obj = bpy.data.objects.new(obj.name + "_temp", temp_mesh)
    bpy.context.collection.objects.link(temp_obj)
    
    # Triangulate
    bpy.context.view_layer.objects.active = temp_obj
    temp_obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY')
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Get BMesh
    bm = bmesh.new()
    bm.from_mesh(temp_mesh)
    
    # Extract data
    vertices = []
    normals = []
    uvs = []
    colors = []
    weights = []
    
    # Get UV layer
    uv_layer = bm.loops.layers.uv.active
    
    # Get color attribute
    color_attr = None
    if temp_mesh.color_attributes.active:
        color_attr = temp_mesh.color_attributes.active
    
    # Process each vertex
    for vert in bm.verts:
        # Position
        vertices.append((vert.co.x, vert.co.y, vert.co.z, 0))
        
        # Normal
        if export_normals:
            normal = tuple(vert.normal)
            normals.append(normal)
        else:
            normals.append((0, 0, 1))
        
        # UV
        if export_uvs and uv_layer:
            # Get UV dari loop yang terhubung dengan vertex ini
            uv = (0.0, 0.0)
            for loop in vert.link_loops:
                uv_data = loop[uv_layer]
                uv = tuple(uv_data.uv)
                break
            uvs.append(uv)
        else:
            uvs.append((0.0, 0.0))
        
        # Color
        if export_colors and color_attr:
            # Get color dari loop
            color = (1.0, 1.0, 1.0, 1.0)
            for loop in vert.link_loops:
                color_data = color_attr.data[loop.index]
                color = tuple(color_data.color)
                break
            colors.append(color)
        else:
            colors.append((1.0, 1.0, 1.0, 1.0))
        
        # Weights
        vert_weights = []
        for group in obj.vertex_groups:
            try:
                weight = group.weight(vert.index)
                if weight > 0:
                    # Extract bone index dari group name
                    bone_idx = extract_bone_index(group.name)
                    vert_weights.append((bone_idx, weight))
            except:
                pass
        
        # Sort by weight descending, take top 3
        vert_weights.sort(key=lambda x: x[1], reverse=True)
        vert_weights = vert_weights[:3]
        
        # Normalize
        total_weight = sum(w for _, w in vert_weights)
        if total_weight > 0:
            vert_weights = [(idx, w/total_weight) for idx, w in vert_weights]
        
        # Pad to 3
        while len(vert_weights) < 3:
            vert_weights.append((0, 0.0))
        
        weights.append(vert_weights)
    
    # Clean up temp object
    bm.free()
    bpy.data.objects.remove(temp_obj)
    bpy.data.meshes.remove(temp_mesh)
    
    print(f"[EXPORT SCR] Prepared {len(vertices)} vertices")
    
    return {
        'name': obj.name,
        'vertices': vertices,
        'normals': normals,
        'uvs': uvs,
        'colors': colors,
        'weights': weights,
        'material_index': 0
    }


def write_scr_file(filepath, mesh_name, mesh_data):
    """
    Write SCR file format
    """
    
    with open(filepath, 'wb') as f:
        # ====================================================================
        # HEADER (16 bytes)
        # ====================================================================
        print("[EXPORT SCR] Writing header...")
        f.write(scr_parser.SCR_MAGIC)
        f.write(struct.pack('<I', 3))  # version
        f.write(struct.pack('<I', 1))  # 1 mesh
        f.write(struct.pack('<I', 0))  # reserved
        
        # Offset placeholder
        offset_pos = f.tell()
        f.write(struct.pack('<I', 0))  # Will fill later
        
        # ====================================================================
        # ALIGN (ke 16 bytes)
        # ====================================================================
        while f.tell() % 16 != 0:
            f.write(b'\x00')
        
        # ====================================================================
        # MESH OFFSET
        # ====================================================================
        mesh_offset = f.tell()
        f.seek(offset_pos)
        f.write(struct.pack('<I', mesh_offset))
        f.seek(mesh_offset)
        
        # ====================================================================
        # MDB HEADER (48 bytes)
        # ====================================================================
        print("[EXPORT SCR] Writing MDB header...")
        f.write(scr_parser.MDB_MAGIC)
        f.write(struct.pack('<I', 48))  # header size
        f.write(struct.pack('<H', 1))   # bone count
        f.write(struct.pack('<H', 1))   # submesh count
        f.write(b'\x00' * 24)  # reserved
        
        # Offset placeholders (akan diisi setelah)
        offset_placements = []
        for _ in range(5):  # 5 offsets: verts, normals, uvs, colors, weights
            offset_placements.append(f.tell())
            f.write(struct.pack('<I', 0))
        
        # Vertex count dan material index
        f.write(struct.pack('<H', len(mesh_data['vertices'])))
        f.write(struct.pack('<H', mesh_data['material_index']))
        f.write(b'\x00' * 8)  # reserved
        
        # ====================================================================
        # VERTICES DATA
        # ====================================================================
        print("[EXPORT SCR] Writing vertices...")
        verts_start = f.tell()
        
        # Update offset
        f.seek(offset_placements[0])
        f.write(struct.pack('<I', verts_start - mesh_offset))
        f.seek(verts_start)
        
        # Write vertices
        for x, y, z, flag in mesh_data['vertices']:
            x_int = int(x * 100)
            y_int = int(y * 100)
            z_int = int(z * 100)
            f.write(struct.pack('<hhh', x_int, y_int, z_int))
            f.write(struct.pack('<H', flag))
        
        # ====================================================================
        # NORMALS DATA
        # ====================================================================
        print("[EXPORT SCR] Writing normals...")
        normals_start = f.tell()
        
        f.seek(offset_placements[1])
        f.write(struct.pack('<I', normals_start - mesh_offset))
        f.seek(normals_start)
        
        for x, y, z in mesh_data['normals']:
            x_byte = scr_parser.normal_to_byte(x)
            y_byte = scr_parser.normal_to_byte(y)
            z_byte = scr_parser.normal_to_byte(z)
            f.write(struct.pack('<bbbb', x_byte, y_byte, z_byte, 0))
        
        # ====================================================================
        # UVS DATA
        # ====================================================================
        print("[EXPORT SCR] Writing UVs...")
        uvs_start = f.tell()
        
        f.seek(offset_placements[2])
        f.write(struct.pack('<I', uvs_start - mesh_offset))
        f.seek(uvs_start)
        
        for u, v in mesh_data['uvs']:
            u_int = int(u * 4096)
            v_int = int(v * -4096)  # NEGATIVE!
            f.write(struct.pack('<hh', u_int, v_int))
        
        # ====================================================================
        # COLORS DATA
        # ====================================================================
        print("[EXPORT SCR] Writing colors...")
        colors_start = f.tell()
        
        f.seek(offset_placements[3])
        f.write(struct.pack('<I', colors_start - mesh_offset))
        f.seek(colors_start)
        
        for r, g, b, a in mesh_data['colors']:
            r_int = int(max(0, min(255, r * 255)))
            g_int = int(max(0, min(255, g * 255)))
            b_int = int(max(0, min(255, b * 255)))
            a_int = int(max(0, min(255, a * 255)))
            f.write(struct.pack('<BBBB', r_int, g_int, b_int, a_int))
        
        # ====================================================================
        # WEIGHTS DATA
        # ====================================================================
        print("[EXPORT SCR] Writing weights...")
        weights_start = f.tell()
        
        f.seek(offset_placements[4])
        f.write(struct.pack('<I', weights_start - mesh_offset))
        f.seek(weights_start)
        
        for weight_list in mesh_data['weights']:
            # Write bone indices
            f.write(struct.pack('<B', 0))  # null byte
            for bone_idx, _ in weight_list:
                f.write(struct.pack('<B', bone_idx * 4))
            
            # Align to 4 bytes
            while f.tell() % 4 != 0:
                f.write(b'\x00')
            
            # Write weight values
            for _, weight in weight_list:
                f.write(struct.pack('<B', int(weight * 100)))
            
            # Align to 4 bytes
            while f.tell() % 4 != 0:
                f.write(b'\x00')
        
        print("[EXPORT SCR] ✓ File written successfully")


def extract_bone_index(bone_name):
    """
    Extract bone index dari bone name
    
    Contoh:
        "Bone_001" → 1
        "Bone_042" → 42
        "root" → 0
    """
    import re
    
    if "root" in bone_name.lower():
        return 0
    
    match = re.search(r'\d+', bone_name)
    if match:
        return int(match.group())
    
    return 0
