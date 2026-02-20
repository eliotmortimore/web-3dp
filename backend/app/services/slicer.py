import subprocess
import os

class BambuSlicer:
    def __init__(self, slicer_path: str = "/usr/bin/bambu-studio"):
        self.slicer_path = slicer_path
        
    def slice_file(self, stl_path: str, output_3mf: str, config_file: str):
        """
        Executes Bambu Studio CLI to convert .stl to .3mf.
        
        Args:
            stl_path (str): Path to input .stl
            output_3mf (str): Path to output .3mf
            config_file (str): Path to slicing profile (config.ini / .json)
        """
        if not os.path.exists(stl_path):
            raise FileNotFoundError(f"Input file not found: {stl_path}")
            
        # Command Construction (This may vary based on Bambu Studio version)
        # Assuming xvfb-run for headless environments
        command = [
            "xvfb-run", "-a", 
            self.slicer_path, 
            "--slice", "0", 
            "--conf", config_file, 
            "--output", output_3mf, 
            stl_path
        ]
        
        try:
            result = subprocess.run(
                command, 
                check=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True
            )
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            return False, e.stderr
