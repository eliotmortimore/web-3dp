import ftplib
import logging
import ssl
import json
import socket
import time
import os
from ftplib import FTP_TLS
from typing import Dict, Any

import paho.mqtt.client as mqtt
from app.core.config import settings

logger = logging.getLogger(__name__)


class ImplicitFTP_TLS(FTP_TLS):
    """FTP_TLS subclass for implicit TLS (port 990).

    Python's FTP_TLS uses explicit TLS (AUTH TLS after connect).
    Bambu printers require implicit TLS where the socket is wrapped
    in SSL immediately on connect.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def connect(self, host='', port=0, timeout=-999, source_address=None):
        if host != '':
            self.host = host
        if port > 0:
            self.port = port
        if timeout != -999:
            self.timeout = timeout
        if source_address is not None:
            self.source_address = source_address

        self.sock = socket.create_connection(
            (self.host, self.port), self.timeout, source_address=self.source_address
        )
        self.af = self.sock.family

        # Immediately wrap the socket in TLS (implicit TLS)
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        self.sock = context.wrap_socket(self.sock, server_hostname=self.host)
        self.file = self.sock.makefile('r')
        self.welcome = self.getresp()
        return self.welcome


class BambuPrinter:
    def __init__(self):
        self.ip = settings.BAMBU_PRINTER_IP
        self.access_code = settings.BAMBU_ACCESS_CODE
        self.serial = settings.BAMBU_SERIAL_NUMBER
        self.username = "bblp"  # Standard Bambu user

    def upload_file(self, local_path: str, remote_filename: str) -> bool:
        """
        Uploads a .gcode.3mf file to the printer via FTPS (Implicit TLS on port 990).
        """
        logger.info(f"Uploading {local_path} to printer at {self.ip}...")

        try:
            ftps = ImplicitFTP_TLS()
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

    def send_print_command(self, filename: str, project_id: str = "0", plates: list | None = None) -> bool:
        """
        Sends the MQTT command to start printing the uploaded file.
        """
        if plates is None:
            plates = [1]
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
            client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
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
