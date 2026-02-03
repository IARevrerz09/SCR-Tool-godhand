# File: scr_tools/triangle_strip.py
"""
Triangle Strip handling (untuk masa depan)
Saat ini simplified, bisa diperluas nanti
"""

from typing import List, Tuple

class TriangleStripper:
    """
    Manage triangle strips untuk optimization
    
    Dalam SCR format, vertices bisa disusun sebagai "strip"
    di mana triangles berbagi edges untuk menghemat memory
    """
    
    def __init__(self):
        self.vertices = []
        self.flags = []
        self.faces = []
    
    def add_vertex(self, position: Tuple[float, float, float], flag: int = 0):
        """Add vertex dengan optional flag"""
        self.vertices.append(position)
        self.flags.append(flag)
    
    def build_faces(self) -> List[Tuple[int, int, int]]:
        """
        Build triangle faces dari strip
        
        Simplified version: just make triangles setiap 3 vertices
        """
        self.faces = []
        
        for i in range(0, len(self.vertices) - 2, 3):
            self.faces.append((i, i+1, i+2))
        
        return self.faces
