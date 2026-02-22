import ftplib
import logging
import ssl
import json
import time
import os
from ftplib import FTP_TLS
from typing import Dict, Any

import paho.mqtt.client as mqtt
from app.core.config import settings

logger = logging.getLogger(__name__)

class BambuPrinter:
    def __init__(self):
        self.ip = settings.BAMBU_PRINTER_IP
        self.access_code = settings.BAMBU_ACCESS_CODE
        self.serial = settings.BAMBU_SERIAL_NUMBER
        self.username = "bblp"  # Standard Bambu user

    def upload_file(self, local_path: str, remote_filename: str) -> bool:
        """
        Uploads a .gcode.3mf file to the printer via FTPS (Implicit TLS).
        """
        logger.info(f"Uploading {local_path} to printer at {self.ip}...")
        
        try:
            # Connect using Implicit TLS on port 990
            ftps = FTP_TLS()
            ftps.connect(self.ip, 990)
            ftps.login(self.username, self.access_code)
            ftps.prot_p()  # Switch data connection to secure mode

            with open(local_path, "rb") as file:
                ftps.storbinary(f"STOR {remote_filename}", file)
            
            ftps.quit()
            logger.info("Upload successful.")
            return True
        except Exception as e:
            logger.error(f"Failed to upload file: {e}")
            return False

    def send_print_command(self, filename: str, project_id: str = "0", plates: list = [1]) -> bool:
        """
        Sends the MQTT command to start printing the uploaded file.
        """
        topic = f"device/{self.serial}/request"
        
        # Command payload structure (Simplified based on community docs)
        payload = {
            "print": {
                "sequence_id": "0",
                "command": "project_file",
                "param": f"Metadata/plate_{plates[0]}.gcode",  # Assuming standard 3MF structure
                "project_id": project_id,
                "profile_id": "0",
                "task_id": "0",
                "subtask_id": "0",
                "subtask_name": "",
                "file": filename, # e.g. "my_print.gcode.3mf"
                "url": f"ftp://{filename}", # Usually redundant if file is local
                "md5": "", # Optional but good practice
                "timelapse": True,
                "bed_type": "textured_pei_plate", # Default
                "bed_levelling": True,
                "flow_cali": True,
                "vibration_cali": True,
                "layer_inspect": True,
                "use_ams": False # Simple mode
            }
        }
        
        try:
            client = mqtt.Client()
            client.username_pw_set(self.username, self.access_code)
            
            # Configure TLS context for secure connection
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            client.tls_set_context(context)
            
            client.connect(self.ip, 8883, 60)
            client.loop_start()
            
            msg_info = client.publish(topic, json.dumps(payload), qos=1)
            msg_info.wait_for_publish()
            
            time.sleep(1) # Give it a moment to send
            client.loop_stop()
            client.disconnect()
            
            logger.info(f"Print command sent for {filename}")
            return True
        except Exception as e:
            logger.error(f"Failed to send MQTT command: {e}")
            return False

bambu_client = BambuPrinter()
