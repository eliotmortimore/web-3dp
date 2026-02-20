from sqlalchemy import Column, Integer, String, Float, DateTime, Enum
from sqlalchemy.sql import func
from app.db.database import Base
import enum

class JobStatus(str, enum.Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    SLICING = "SLICING"
    PRINTING = "PRINTING"
    DONE = "DONE"
    FAILED = "FAILED"

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    filepath = Column(String)  # Path to stored STL
    status = Column(String, default=JobStatus.PENDING)
    material = Column(String)
    color = Column(String)
    volume_cm3 = Column(Float)
    price = Column(Float)
    quantity = Column(Integer, default=1)
    customer_email = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Material(Base):
    __tablename__ = "materials"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    type = Column(String)  # PLA, PETG, etc.
    brand = Column(String, default="Generic")
    color = Column(String)
    hex_color = Column(String) # For UI
    density = Column(Float) # g/cm3
    cost_per_g = Column(Float) # Cost per gram
    stock_weight_g = Column(Float, default=1000.0) # Remaining stock
