import subprocess
import os
import logging
import json
import shutil
import tempfile
from app.core.config import settings
from app.services.metadata import parse_3mf_metadata

logger = logging.getLogger(__name__)

class BambuSlicer:
    def __init__(self):
        self.slicer_path = settings.SLICER_PATH
        # Use absolute path for config dir
        self.config_dir = os.path.abspath(settings.SLICER_CONFIG_DIR)
        
        if not os.path.exists(self.slicer_path):
            logger.warning(f"Bambu Studio not found at {self.slicer_path}. Slicing will fail.")

    def slice_file(self, input_stl: str, output_3mf: str) -> dict:
        """
        Uses Bambu Studio CLI to slice the file and generate a .3mf with G-code.
        This is a potentially slow operation intended for Admin use.
        """
        if not os.path.exists(input_stl):
            return {"success": False, "error": "Input file not found"}

        if not os.path.exists(self.slicer_path):
            return {"success": False, "error": "Slicer executable not found"}

        try:
            # Bambu Studio CLI command
            config_path = os.path.join(self.config_dir, "default.json")
            
            # Construct command
            # We use --export-3mf because it includes slice data (G-code/metadata) 
            cmd = [
                self.slicer_path,
                "--slice", "0",
                "--export-3mf", output_3mf,
                input_stl
            ]
            
            if os.path.exists(config_path):
                 cmd.extend(["--load-settings", config_path])
            
            logger.info(f"Running slicer: {' '.join(cmd)}")
            
            # 5 minute timeout for slicing
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=300 
            )
            
            if result.returncode == 0 and os.path.exists(output_3mf):
                logger.info("Slicing successful.")
                
                # Parse metadata to confirm success or get extra details
                metadata = {}
                try:
                    metadata = parse_3mf_metadata(output_3mf)
                except Exception as e:
                    logger.warning(f"Metadata parse warning: {e}")

                return {
                    "success": True,
                    "file_path": output_3mf,
                    "metadata": metadata
                }

            else:
                logger.warning(f"Slicing failed or no output: {result.stderr}")
                return {
                    "success": False,
                    "error": f"Slicer failed: {result.stderr}"
                }

        except Exception as e:
            logger.error(f"Slicing exception: {e}")
            return {
                "success": False,
                "error": str(e)
            }
