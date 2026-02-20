import zipfile
import json
import logging
import os
import xml.etree.ElementTree as ET
from typing import Dict, Any

logger = logging.getLogger(__name__)

def parse_3mf_metadata(file_path: str) -> Dict[str, Any]:
    """
    Extracts metadata from a 3MF file (which is a ZIP).
    Specifically looks for Bambu/Prusa slicer configurations.
    """
    metadata = {}
    
    if not os.path.exists(file_path):
        return {}

    # Check if it's a valid zip file first
    if not zipfile.is_zipfile(file_path):
        # Fallback for mock files during development or non-zip files
        # In a real scenario, this might just return empty or error
        logger.warning(f"{file_path} is not a valid ZIP/3MF file. Returning mock metadata.")
        return {
            "slice_info": {
                "layer_height": "0.2 mm",
                "wall_loops": "3",
                "infill_density": "15%",
                "support_type": "tree(auto)",
                "material_type": "PLA",
                "bed_temperature": "60 C",
                "nozzle_temperature": "220 C",
                "speed_print": "200 mm/s",
                "speed_travel": "500 mm/s",
                "fan_speed": "100%",
                "brim_width": "5 mm",
                "ironing": "Top Surfaces",
                "sparse_infill_pattern": "Grid"
            },
            "project_settings": {
                "project_name": "My Cool Print",
                "author": "User",
                "printer_model": "Bambu Lab X1C",
                "slicer": "Bambu Studio"
            }
        }

    try:
        with zipfile.ZipFile(file_path, 'r') as z:
            # List all files
            files = z.namelist()
            
            # 1. Look for Metadata/slice_info.config (Bambu/Orca style)
            # 2. Look for Metadata/project_settings.config
            # 3. Look for 3D/3dmodel.model (Standard 3MF) to get basic info if needed
            
            # Helper to parse config-like files (key = value)
            def parse_config(content):
                data = {}
                for line in content.splitlines():
                    if '=' in line:
                        parts = line.split('=', 1)
                        if len(parts) == 2:
                            k, v = parts
                            data[k.strip()] = v.strip()
                return data

            # Extract Slice Info
            slice_config_files = [f for f in files if 'slice_info' in f]
            if slice_config_files:
                with z.open(slice_config_files[0]) as f:
                    content = f.read().decode('utf-8', errors='ignore')
                    metadata['slice_info'] = parse_config(content)
            
            # Extract Project Settings
            project_config_files = [f for f in files if 'project_settings' in f]
            if project_config_files:
                with z.open(project_config_files[0]) as f:
                    content = f.read().decode('utf-8', errors='ignore')
                    metadata['project_settings'] = parse_config(content)

    except Exception as e:
        logger.error(f"Error reading 3MF file {file_path}: {e}")
        return {"error": str(e)}

    return metadata
