# File: scr_tools/scr_parser.py
"""
SCR File Format Parser
Menghandle membaca/menulis file binary SCR
"""

import struct
import math
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass

# ============================================================================
# CONSTANTS
# ============================================================================
SCR_MAGIC = b'scr\x00'
MDB_MAGIC = b'mdb\x00'
SCR_HEADER_SIZE = 16
MDB_HEADER_SIZE = 48

# ============================================================================
# DATA CLASSES - Struktur data untuk menyimpan info
# ============================================================================

@dataclass
class Vertex:
    """Satu vertex dalam mesh"""
    x: float
    y: float
    z: float
    flag: int
    normal: Tuple[float, float, float] = (0, 0, 1)
    uv: Tuple[float, float] = (0, 0)
    color: Tuple[float, float, float, float] = (1, 1, 1, 1)
    weights: List[Tuple[int, float]] = None  # [(bone_idx, weight), ...]
    
    def __post_init__(self):
        """Jalankan setelah __init__"""
        if self.weights is None:
            self.weights = []


@dataclass
class Mesh:
    """Satu mesh/object"""
    name: str
    vertices: List[Vertex]
    faces: List[Tuple[int, int, int]]
    material_index: int
    bones: List[str]


@dataclass
class SCRFile:
    """Keseluruhan file SCR"""
    version: int
    meshes: List[Mesh]


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def byte_to_normal(b: int) -> float:
    """
    Konversi signed byte (-128..127) ke normal vector (-1.0..1.0)
    
    Formula: (b + 128) / 255 * 2 - 1
    
    Contoh:
        -128 → -1.0
        0   → -0.00392
        127 → 0.99609
    """
    return (b + 128) / 255.0 * 2.0 - 1.0


def normal_to_byte(n: float) -> int:
    """
    Reverse dari byte_to_normal
    Konversi normal (-1.0..1.0) ke signed byte (-128..127)
    """
    clamped = max(-1.0, min(1.0, n))
    return int((clamped + 1.0) / 2.0 * 255.0) - 128


def normalize_vector(x: float, y: float, z: float) -> Tuple[float, float, float]:
    """Normalize vektor 3D"""
    length = math.sqrt(x*x + y*y + z*z)
    if length < 0.0001:  # Avoid division by zero
        return (0, 0, 1)  # Default normal
    return (x/length, y/length, z/length)


# ============================================================================
# PARSER CLASS - Membaca file SCR
# ============================================================================

class SCRParser:
    """Main parser untuk membaca file SCR"""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.file = None
    
    def __enter__(self):
        self.file = open(self.filepath, 'rb')
        return self
    
    def __exit__(self, *args):
        if self.file:
            self.file.close()
    
    # ========================================================================
    # READING METHODS
    # ========================================================================
    
    def read_header(self) -> Dict:
        """
        Baca SCR header (16 bytes)
        
        Layout:
        Offset  Size   Field
        ──────────────────────
        0x00    4      Magic "scr\0"
        0x04    4      Version
        0x08    4      Mesh Count
        0x0C    4      Reserved
        """
        self.file.seek(0)
        
        magic = self.file.read(4)
        if magic != SCR_MAGIC:
            raise ValueError(f"Invalid SCR magic: {magic!r}")
        
        version = struct.unpack('<I', self.file.read(4))[0]
        mesh_count = struct.unpack('<I', self.file.read(4))[0]
        reserved = struct.unpack('<I', self.file.read(4))[0]
        
        return {
            'magic': magic,
            'version': version,
            'mesh_count': mesh_count,
            'reserved': reserved
        }
    
    def read_mesh_offsets(self, mesh_count: int) -> List[int]:
        """
        Baca offset array setelah header
        
        Setiap offset adalah 4 bytes (uint32 Little Endian)
        Offset menunjuk ke posisi MDB block
        """
        offsets = []
        for i in range(mesh_count):
            offset = struct.unpack('<I', self.file.read(4))[0]
            offsets.append(offset)
            print(f"  Mesh {i} offset: 0x{offset:06X}")
        
        return offsets
    
    def read_mdb_header(self, mesh_offset: int) -> Dict:
        """
        Baca MDB (Model Data Block) header
        
        Layout (dari hex dump analysis):
        Offset  Size   Field
        ──────────────────────────
        +0x00   4      Magic "mdb\0"
        +0x04   4      Header Size (48)
        +0x08   2      Bone Count
        +0x0A   2      SubMesh Count
        +0x0C   24     Reserved
        +0x24   4      Vertices Offset (relative)
        +0x28   4      Normals Offset
        +0x2C   4      UVs Offset
        +0x30   4      Colors Offset
        +0x34   4      Weights Offset
        +0x38   2      Vertex Count
        +0x3A   2      Material Index
        """
        self.file.seek(mesh_offset)
        
        magic = self.file.read(4)
        if magic != MDB_MAGIC:
            raise ValueError(f"Invalid MDB magic at 0x{mesh_offset:06X}: {magic!r}")
        
        header_size = struct.unpack('<I', self.file.read(4))[0]
        bone_count = struct.unpack('<H', self.file.read(2))[0]
        submesh_count = struct.unpack('<H', self.file.read(2))[0]
        
        # Skip reserved (24 bytes)
        self.file.read(24)
        
        # Baca offsets (relative to MDB start)
        verts_offset_rel = struct.unpack('<I', self.file.read(4))[0]
        normals_offset_rel = struct.unpack('<I', self.file.read(4))[0]
        uvs_offset_rel = struct.unpack('<I', self.file.read(4))[0]
        colors_offset_rel = struct.unpack('<I', self.file.read(4))[0]
        weights_offset_rel = struct.unpack('<I', self.file.read(4))[0]
        
        vertex_count = struct.unpack('<H', self.file.read(2))[0]
        material_idx = struct.unpack('<H', self.file.read(2))[0]
        
        # Convert relative offsets ke absolute
        verts_offset = mesh_offset + verts_offset_rel
        normals_offset = mesh_offset + normals_offset_rel
        uvs_offset = mesh_offset + uvs_offset_rel
        colors_offset = mesh_offset + colors_offset_rel
        weights_offset = mesh_offset + weights_offset_rel
        
        return {
            'bone_count': bone_count,
            'submesh_count': submesh_count,
            'vertices_offset': verts_offset,
            'normals_offset': normals_offset,
            'uvs_offset': uvs_offset,
            'colors_offset': colors_offset,
            'weights_offset': weights_offset,
            'vertex_count': vertex_count,
            'material_idx': material_idx
        }
    
    def read_vertices(self, offset: int, count: int) -> List[Tuple[float, float, float, int]]:
        """
        Baca vertex positions
        
        Format (8 bytes per vertex):
        - Bytes 0-1: X (int16) × 0.01
        - Bytes 2-3: Y (int16) × 0.01
        - Bytes 4-5: Z (int16) × 0.01
        - Bytes 6-7: Flag (uint16)
        """
        vertices = []
        self.file.seek(offset)
        
        for i in range(count):
            x = struct.unpack('<h', self.file.read(2))[0] * 0.01
            y = struct.unpack('<h', self.file.read(2))[0] * 0.01
            z = struct.unpack('<h', self.file.read(2))[0] * 0.01
            flag = struct.unpack('<H', self.file.read(2))[0]
            
            vertices.append((x, y, z, flag))
        
        return vertices
    
    def read_normals(self, offset: int, count: int) -> List[Tuple[float, float, float]]:
        """
        Baca vertex normals
        
        Format (4 bytes per vertex):
        - Byte 0: X normal (signed byte)
        - Byte 1: Y normal (signed byte)
        - Byte 2: Z normal (signed byte)
        - Byte 3: Padding
        """
        normals = []
        self.file.seek(offset)
        
        for i in range(count):
            x = byte_to_normal(struct.unpack('<b', self.file.read(1))[0])
            y = byte_to_normal(struct.unpack('<b', self.file.read(1))[0])
            z = byte_to_normal(struct.unpack('<b', self.file.read(1))[0])
            w = struct.unpack('<b', self.file.read(1))[0]  # padding
            
            # Normalize
            x, y, z = normalize_vector(x, y, z)
            normals.append((x, y, z))
        
        return normals
    
    def read_uvs(self, offset: int, count: int) -> List[Tuple[float, float]]:
        """
        Baca UV coordinates
        
        Format (4 bytes per vertex):
        - Bytes 0-1: U (int16 / 4096.0)
        - Bytes 2-3: V (int16 / -4096.0)  ← Note: negative!
        """
        uvs = []
        self.file.seek(offset)
        
        for i in range(count):
            u_raw = struct.unpack('<h', self.file.read(2))[0]
            v_raw = struct.unpack('<h', self.file.read(2))[0]
            
            u = u_raw / 4096.0
            v = v_raw / -4096.0  # NEGATIVE!
            
            uvs.append((u, v))
        
        return uvs
    
    def read_colors(self, offset: int, count: int) -> List[Tuple[float, float, float, float]]:
        """
        Baca vertex colors
        
        Format (4 bytes per vertex):
        - Byte 0: R (0-255 → 0.0-1.0)
        - Byte 1: G
        - Byte 2: B
        - Byte 3: A
        """
        colors = []
        self.file.seek(offset)
        
        for i in range(count):
            r = struct.unpack('<B', self.file.read(1))[0] / 255.0
            g = struct.unpack('<B', self.file.read(1))[0] / 255.0
            b = struct.unpack('<B', self.file.read(1))[0] / 255.0
            a = struct.unpack('<B', self.file.read(1))[0] / 255.0
            
            colors.append((r, g, b, a))
        
        return colors
    
    def read_weights(self, offset: int, count: int) -> List[List[Tuple[int, float]]]:
        """
        Baca bone weights
        
        Format (8 bytes per vertex):
        - Byte 0: Padding
        - Byte 1: Bone Index 1 (raw × 4)
        - Byte 2: Bone Index 2
        - Byte 3: Bone Index 3
        [Align to 4 bytes]
        - Byte 4: Weight 1 (0-100%)
        - Byte 5: Weight 2
        - Byte 6: Weight 3
        - Byte 7: Padding
        """
        weights = []
        self.file.seek(offset)
        
        for i in range(count):
            # Baca bone indices
            _ = struct.unpack('<B', self.file.read(1))[0]  # null byte
            idx1_raw = struct.unpack('<B', self.file.read(1))[0]
            idx2_raw = struct.unpack('<B', self.file.read(1))[0]
            idx3_raw = struct.unpack('<B', self.file.read(1))[0]
            
            # Konversi index (encoded sebagai idx * 4)
            idx1 = (int(idx1_raw / 4)) if idx1_raw != 0 else 0
            idx2 = (int(idx2_raw / 4)) if idx2_raw != 0 else 0
            idx3 = (int(idx3_raw / 4)) if idx3_raw != 0 else 0
            
            # Align ke 4 bytes
            while self.file.tell() % 4 != 0:
                self.file.read(1)
            
            # Baca weights (percentage)
            w1 = struct.unpack('<B', self.file.read(1))[0] / 100.0
            w2 = struct.unpack('<B', self.file.read(1))[0] / 100.0
            w3 = struct.unpack('<B', self.file.read(1))[0] / 100.0
            _ = struct.unpack('<B', self.file.read(1))[0]  # padding
            
            # Normalize weights (sum harus 1.0)
            total = w1 + w2 + w3
            if total > 0:
                w1 /= total
                w2 /= total
                w3 /= total
            
            weight_data = [
                (idx1, w1),
                (idx2, w2),
                (idx3, w3)
            ]
            weights.append(weight_data)
        
        return weights
    
    def parse(self) -> SCRFile:
        """
        Parse keseluruhan file SCR
        
        Returns:
            SCRFile object dengan semua data
        """
        print("\n" + "="*70)
        print("[SCR PARSER] PARSING FILE")
        print("="*70)
        
        # Baca header
        header = self.read_header()
        print(f"Version: {header['version']}, Meshes: {header['mesh_count']}")
        
        # Baca offsets
        print(f"\nMesh offsets:")
        offsets = self.read_mesh_offsets(header['mesh_count'])
        
        # Parse setiap mesh
        meshes = []
        for mesh_idx, mesh_offset in enumerate(offsets):
            print(f"\n[Mesh {mesh_idx}] Parsing at 0x{mesh_offset:06X}...")
            
            try:
                # Baca MDB header
                mdb_info = self.read_mdb_header(mesh_offset)
                print(f"  Vertices: {mdb_info['vertex_count']}")
                print(f"  Bones: {mdb_info['bone_count']}")
                
                # Baca semua vertex data
                verts_raw = self.read_vertices(
                    mdb_info['vertices_offset'],
                    mdb_info['vertex_count']
                )
                
                normals = self.read_normals(
                    mdb_info['normals_offset'],
                    mdb_info['vertex_count']
                )
                
                uvs = self.read_uvs(
                    mdb_info['uvs_offset'],
                    mdb_info['vertex_count']
                )
                
                colors = self.read_colors(
                    mdb_info['colors_offset'],
                    mdb_info['vertex_count']
                )
                
                weights = self.read_weights(
                    mdb_info['weights_offset'],
                    mdb_info['vertex_count']
                )
                
                # Buat Vertex objects
                vertices = []
                for j in range(mdb_info['vertex_count']):
                    vert = Vertex(
                        x=verts_raw[j][0],
                        y=verts_raw[j][1],
                        z=verts_raw[j][2],
                        flag=verts_raw[j][3],
                        normal=normals[j],
                        uv=uvs[j],
                        color=colors[j],
                        weights=weights[j]
                    )
                    vertices.append(vert)
                
                # Build faces dari vertices
                # Simplified: just create triangles setiap 3 vertices
                faces = []
                for k in range(0, len(vertices) - 2, 3):
                    faces.append((k, k+1, k+2))
                
                # Buat Mesh object
                mesh = Mesh(
                    name=f"Mesh_{mesh_idx}",
                    vertices=vertices,
                    faces=faces,
                    material_index=mdb_info['material_idx'],
                    bones=[]
                )
                
                meshes.append(mesh)
                print(f"  ✓ Loaded {len(vertices)} vertices, {len(faces)} faces")
            
            except Exception as e:
                print(f"  ✗ Error: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print("\n" + "="*70)
        print(f"[SCR PARSER] ✓ Parsed {len(meshes)} meshes successfully!")
        print("="*70 + "\n")
        
        return SCRFile(version=header['version'], meshes=meshes)


# ============================================================================
# WRITER CLASS - Menulis file SCR
# ============================================================================

class SCRWriter:
    """Main writer untuk menulis file SCR"""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.file = None
    
    def __enter__(self):
        self.file = open(self.filepath, 'wb')
        return self
    
    def __exit__(self, *args):
        if self.file:
            self.file.close()
    
    def write_header(self, version: int, mesh_count: int):
        """Write SCR header"""
        self.file.write(SCR_MAGIC)
        self.file.write(struct.pack('<I', version))
        self.file.write(struct.pack('<I', mesh_count))
        self.file.write(struct.pack('<I', 0))  # reserved
    
    def write_vertices(self, vertices: List[Tuple[float, float, float, int]]):
        """Write vertices"""
        for x, y, z, flag in vertices:
            x_int = int(x * 100)
            y_int = int(y * 100)
            z_int = int(z * 100)
            self.file.write(struct.pack('<hhh', x_int, y_int, z_int))
            self.file.write(struct.pack('<H', flag))
    
    def write_normals(self, normals: List[Tuple[float, float, float]]):
        """Write normals"""
        for x, y, z in normals:
            x_byte = normal_to_byte(x)
            y_byte = normal_to_byte(y)
            z_byte = normal_to_byte(z)
            self.file.write(struct.pack('<bbbb', x_byte, y_byte, z_byte, 0))
    
    def write_uvs(self, uvs: List[Tuple[float, float]]):
        """Write UVs"""
        for u, v in uvs:
            u_int = int(u * 4096)
            v_int = int(v * -4096)  # NEGATIVE!
            self.file.write(struct.pack('<hh', u_int, v_int))
    
    def write_colors(self, colors: List[Tuple[float, float, float, float]]):
        """Write colors"""
        for r, g, b, a in colors:
            r_int = int(max(0, min(255, r * 255)))
            g_int = int(max(0, min(255, g * 255)))
            b_int = int(max(0, min(255, b * 255)))
            a_int = int(max(0, min(255, a * 255)))
            self.file.write(struct.pack('<BBBB', r_int, g_int, b_int, a_int))
    
    def write_weights(self, weights: List[List[Tuple[int, float]]]):
        """Write bone weights"""
        for weight_list in weights:
            # Ensure 3 bones
            while len(weight_list) < 3:
                weight_list.append((0, 0))
            weight_list = weight_list[:3]
            
            # Write bone indices
            self.file.write(struct.pack('<B', 0))  # null
            for bone_idx, _ in weight_list:
                self.file.write(struct.pack('<B', bone_idx * 4))
            
            # Align to 4 bytes
            while self.file.tell() % 4 != 0:
                self.file.write(b'\x00')
            
            # Write weights
            for _, weight in weight_list:
                self.file.write(struct.pack('<B', int(weight * 100)))
            
            # Align
            while self.file.tell() % 4 != 0:
                self.file.write(b'\x00')
