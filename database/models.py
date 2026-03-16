"""
Database Models - SQLAlchemy ORM
CyberShield Video Analytics System
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Text, Date,
    DateTime, ForeignKey, LargeBinary, create_engine
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.pool import StaticPool

Base = declarative_base()


class Area(Base):
    __tablename__ = "areas"

    area_id = Column(Integer, primary_key=True)
    area_name = Column(String(100), nullable=False)
    zone_coordinates = Column(Text)
    center_lat = Column(Float)
    center_lon = Column(Float)
    created_at = Column(DateTime, default=datetime.now)

    cameras = relationship("Camera", back_populates="area")
    officers = relationship("PoliceOfficer", back_populates="area")


class Camera(Base):
    __tablename__ = "cameras"

    camera_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    area_id = Column(Integer, ForeignKey("areas.area_id"))
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    signal_number = Column(String(20))
    address = Column(Text)
    rtsp_url = Column(Text)
    status = Column(String(20), default="operational")
    installed_at = Column(Date)
    last_ping = Column(DateTime, default=datetime.now)

    area = relationship("Area", back_populates="cameras")


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="admin")
    email = Column(String(200))
    created_at = Column(DateTime, default=datetime.now)
    last_login = Column(DateTime)


class PoliceOfficer(Base):
    __tablename__ = "police_officers"

    officer_id = Column(Integer, primary_key=True)
    badge_number = Column(String(20), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    phone_number = Column(String(20))
    email = Column(String(200))
    telegram_chat_id = Column(String(50))
    assigned_area = Column(Integer, ForeignKey("areas.area_id"))
    role = Column(String(100), default="Officer")
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    last_login = Column(DateTime)

    area = relationship("Area", back_populates="officers")


class Citizen(Base):
    __tablename__ = "citizens"

    citizen_id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    aadhar_number = Column(String(64))  # Hashed
    age = Column(Integer)
    phone = Column(String(20))
    address = Column(Text)
    photo_url = Column(Text)
    created_at = Column(DateTime, default=datetime.now)

    vehicles = relationship("Vehicle", back_populates="owner")
    criminal_records = relationship("CriminalRecord", back_populates="citizen")


class Vehicle(Base):
    __tablename__ = "vehicles"

    vehicle_id = Column(Integer, primary_key=True)
    license_plate = Column(String(30), unique=True, nullable=False)
    owner_id = Column(Integer, ForeignKey("citizens.citizen_id"))
    make = Column(String(100))
    model = Column(String(100))
    year = Column(Integer)
    color = Column(String(50))
    vehicle_type = Column(String(50))
    registration_valid_till = Column(Date)
    insurance_valid_till = Column(Date)
    created_at = Column(DateTime, default=datetime.now)

    owner = relationship("Citizen", back_populates="vehicles")
    detections = relationship("VehicleDetection", back_populates="vehicle")


class CriminalRecord(Base):
    __tablename__ = "criminal_records"

    record_id = Column(Integer, primary_key=True)
    citizen_id = Column(Integer, ForeignKey("citizens.citizen_id"))
    case_type = Column(String(100))
    case_number = Column(String(100))
    case_date = Column(Date)
    status = Column(String(50), default="Pending")
    description = Column(Text)
    severity = Column(String(20), default="Low")

    citizen = relationship("Citizen", back_populates="criminal_records")


class VehicleDetection(Base):
    __tablename__ = "vehicle_detections"

    detection_id = Column(Integer, primary_key=True)
    license_plate = Column(String(30))
    vehicle_id = Column(Integer, ForeignKey("vehicles.vehicle_id"))
    camera_id = Column(Integer, ForeignKey("cameras.camera_id"))
    detected_at = Column(DateTime, default=datetime.now)
    vehicle_type = Column(String(50))
    color = Column(String(50))
    confidence = Column(Float)
    speed_kmph = Column(Float)
    snapshot_url = Column(Text)
    video_clip_url = Column(Text)
    area_id = Column(Integer, ForeignKey("areas.area_id"))

    vehicle = relationship("Vehicle", back_populates="detections")


class Incident(Base):
    __tablename__ = "incidents"

    incident_id = Column(Integer, primary_key=True)
    incident_type = Column(String(100), nullable=False)
    camera_id = Column(Integer, ForeignKey("cameras.camera_id"))
    area_id = Column(Integer, ForeignKey("areas.area_id"))
    severity = Column(String(20), default="Medium")
    confidence = Column(Float)
    description = Column(Text)
    lat = Column(Float)
    lon = Column(Float)
    persons_involved = Column(Integer)
    snapshot_url = Column(Text)
    video_clip_url = Column(Text)
    status = Column(String(50), default="Active")
    responded_by = Column(Integer, ForeignKey("police_officers.officer_id"))
    responded_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)


class AlertLog(Base):
    __tablename__ = "alert_log"

    alert_id = Column(Integer, primary_key=True)
    incident_id = Column(Integer, ForeignKey("incidents.incident_id"))
    officer_id = Column(Integer, ForeignKey("police_officers.officer_id"))
    channel = Column(String(50))
    status = Column(String(50), default="Sent")
    message = Column(Text)
    sent_at = Column(DateTime, default=datetime.now)
    delivered_at = Column(DateTime)


class Watchlist(Base):
    __tablename__ = "watchlist"

    person_id = Column(Integer, primary_key=True)
    name = Column(String(255))
    alias = Column(String(255))
    age = Column(Integer)
    last_known_address = Column(Text)
    court_order_number = Column(String(100), nullable=False)
    issuing_court = Column(String(200))
    order_date = Column(Date)
    case_type = Column(String(100))
    case_number = Column(String(100))
    severity = Column(String(20), default="High")
    officer_in_charge = Column(Integer, ForeignKey("police_officers.officer_id"))
    encrypted_embedding = Column(LargeBinary)
    valid_from = Column(Date, default=datetime.now)
    valid_until = Column(Date)
    status = Column(String(20), default="Active")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)


class FaceAccessLog(Base):
    __tablename__ = "face_access_log"

    log_id = Column(Integer, primary_key=True)
    officer_id = Column(Integer, ForeignKey("police_officers.officer_id"))
    person_id = Column(Integer, ForeignKey("watchlist.person_id"))
    access_type = Column(String(50))
    justification = Column(Text)
    ip_address = Column(String(50))
    timestamp = Column(DateTime, default=datetime.now)


def get_engine(database_url: str):
    return create_engine(database_url)


def get_session(engine):
    Session = sessionmaker(bind=engine)
    return Session()


def create_all_tables(engine):
    Base.metadata.create_all(engine)
    print("✅ All database tables created successfully")
