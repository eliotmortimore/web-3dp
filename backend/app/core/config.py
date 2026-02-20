from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "Web3DP"
    API_V1_STR: str = "/api/v1"
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",  # Vite default port
    ]
    
    # Database (SQLite)
    DATABASE_URL: str = "sqlite:///./web3dp.db"

    # Bambu Lab Printer Config
    BAMBU_PRINTER_IP: str = "192.168.1.100"  # Example IP
    BAMBU_ACCESS_CODE: str = "12345678"
    BAMBU_SERIAL_NUMBER: str = "01S00A123456789"
    BAMBU_MQTT_USER: str = "bblp"  # Default username

    # Slicer Config (macOS Default)
    SLICER_PATH: str = "/Applications/BambuStudio.app/Contents/MacOS/BambuStudio"
    SLICER_CONFIG_DIR: str = "./slicer_profiles" # Directory to store configs

    class Config:
        env_file = ".env"

settings = Settings()
