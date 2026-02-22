import trimesh
import logging
import os

logger = logging.getLogger(__name__)

class EstimationService:
    # Default Density values (g/cm3) - synced with PricingEngine
    DENSITY = {
        "PLA": 1.24,
        "PETG": 1.27,
        "ABS": 1.04,
        "TPU": 1.21,
    }

    def analyze_stl(self, file_path: str, material: str = "PLA") -> dict:
        """
        Performs fast geometric analysis on an STL file to estimate volume, weight, and print time.
        """
        if not os.path.exists(file_path):
             logger.error(f"File not found for analysis: {file_path}")
             return {"success": False, "error": "File not found"}

        try:
            # Load mesh
            # Use force='mesh' but be prepared for Scenes if multiple bodies
            mesh_obj = trimesh.load(file_path, force='mesh')
            
            volume_mm3 = 0.0
            bounds = None

            # Handle Scene vs Trimesh
            if isinstance(mesh_obj, trimesh.Scene):
                # Sum volume of all geometries
                for geom in mesh_obj.geometry.values():
                    if hasattr(geom, 'volume'):
                        volume_mm3 += geom.volume
                    elif hasattr(geom, 'convex_hull'):
                        volume_mm3 += geom.convex_hull.volume
                
                bounds = mesh_obj.extents
            else:
                # Single Mesh
                if hasattr(mesh_obj, 'volume'):
                    volume_mm3 = mesh_obj.volume
                elif hasattr(mesh_obj, 'convex_hull'):
                    volume_mm3 = mesh_obj.convex_hull.volume
                
                if hasattr(mesh_obj, 'extents'):
                    bounds = mesh_obj.extents

            # Safety check for negative/zero volume (can happen with open meshes)
            if volume_mm3 <= 0:
                 # Fallback: estimate from bounding box * factor? or just minimum
                 volume_mm3 = 1000.0 # 1cc fallback
            
            volume_cm3 = volume_mm3 / 1000.0
            
            # Calculate Weight (g)
            material_key = material.upper()
            density = self.DENSITY.get(material_key, 1.24)
            estimated_weight_g = volume_cm3 * density
            
            # Estimate Print Time
            estimated_print_time_s = int(volume_mm3 / 15.0) + 300
            
            # Dimensions
            if bounds is None:
                dimensions = {"x": 0.0, "y": 0.0, "z": 0.0}
            else:
                dimensions = {
                    "x": float(bounds[0]),
                    "y": float(bounds[1]),
                    "z": float(bounds[2])
                }

            return {
                "success": True,
                "volume_cm3": round(volume_cm3, 2),
                "estimated_weight_g": round(estimated_weight_g, 2),
                "estimated_print_time_s": estimated_print_time_s,
                "dimensions": dimensions
            }

        except Exception as e:
            logger.error(f"Error analyzing STL {file_path}: {e}")
            return {"success": False, "error": str(e)}
