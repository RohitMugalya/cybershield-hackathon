"""
CyberShield - AI Video Analytics System
Configuration File
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # ─── Application ────────────────────────────────────────────────────────────
    APP_NAME = "CyberShield"
    APP_VERSION = "1.0.0"
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    SECRET_KEY = os.getenv("SECRET_KEY", "cybershield-secret-key-change-in-production")

    # ─── Database ────────────────────────────────────────────────────────────────
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:password@localhost:5432/video_analytics"
    )
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # ─── MinIO (Video/Image Storage) ─────────────────────────────────────────────
    MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    MINIO_BUCKET_VIDEO = "video-clips"
    MINIO_BUCKET_SNAPSHOTS = "snapshots"
    MINIO_SECURE = os.getenv("MINIO_SECURE", "False").lower() == "true"

    # ─── Twilio (Voice Calls & SMS) ───────────────────────────────────────────────
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "+1234567890")
    TWILIO_TWIML_URL = os.getenv("TWILIO_TWIML_URL", "")

    # ─── Telegram Bot ─────────────────────────────────────────────────────────────
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_ADMIN_CHAT_ID = os.getenv("TELEGRAM_ADMIN_CHAT_ID", "")

    # ─── Email (SMTP) ─────────────────────────────────────────────────────────────
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    SMTP_SENDER_NAME = os.getenv("SMTP_SENDER_NAME", "CyberShield Alerts")

    # ─── AI Models ────────────────────────────────────────────────────────────────
    YOLO_MODEL_PATH = os.getenv("YOLO_MODEL_PATH", "models/yolov8n.pt")
    VIOLENCE_MODEL_PATH = os.getenv("VIOLENCE_MODEL_PATH", "models/violence_detection.pt")
    FACE_MODEL_NAME = os.getenv("FACE_MODEL_NAME", "Facenet512")

    # ─── Privacy & Security ───────────────────────────────────────────────────────
    ENABLE_FACE_BLURRING = os.getenv("ENABLE_FACE_BLURRING", "True").lower() == "true"
    ENABLE_DIFFERENTIAL_PRIVACY = os.getenv("ENABLE_DIFFERENTIAL_PRIVACY", "True").lower() == "true"
    DIFFERENTIAL_PRIVACY_EPSILON = float(os.getenv("DP_EPSILON", "0.1"))
    ENABLE_HOMOMORPHIC_ENCRYPTION = os.getenv("ENABLE_HE", "True").lower() == "true"
    AUDIT_LOG_RETENTION_DAYS = int(os.getenv("AUDIT_LOG_RETENTION_DAYS", "90"))
    ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "")

    # ─── Alert Thresholds ─────────────────────────────────────────────────────────
    VIOLENCE_CONFIDENCE_THRESHOLD = float(os.getenv("VIOLENCE_THRESHOLD", "0.90"))
    FACE_MATCH_THRESHOLD = float(os.getenv("FACE_MATCH_THRESHOLD", "0.85"))
    TRAFFIC_ALERT_THRESHOLD = int(os.getenv("TRAFFIC_THRESHOLD", "100"))  # vehicles/min
    LOITERING_THRESHOLD_MINUTES = int(os.getenv("LOITERING_THRESHOLD", "10"))

    # ─── Celery ───────────────────────────────────────────────────────────────────
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

    # ─── FastAPI Backend ──────────────────────────────────────────────────────────
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

    # ─── Streamlit ────────────────────────────────────────────────────────────────
    ADMIN_DASHBOARD_PORT = int(os.getenv("ADMIN_PORT", "8501"))
    POLICE_PORTAL_PORT = int(os.getenv("POLICE_PORT", "8502"))

    # ─── Map Configuration ────────────────────────────────────────────────────────
    # Default center: Chennai, Tamil Nadu
    MAP_CENTER_LAT = float(os.getenv("MAP_CENTER_LAT", "13.0827"))
    MAP_CENTER_LON = float(os.getenv("MAP_CENTER_LON", "80.2707"))
    MAP_DEFAULT_ZOOM = int(os.getenv("MAP_ZOOM", "13"))
    MAPBOX_API_KEY = os.getenv("MAPBOX_API_KEY", "")

    # ─── Simulated Camera Locations (Chennai Areas) ───────────────────────────────
    CAMERA_LOCATIONS = [
        {"camera_id": 1, "name": "North Gate Signal", "area": "Area 1 - North Zone",
         "lat": 13.1125, "lon": 80.2348, "status": "operational", "signal": "Signal #1"},
        {"camera_id": 2, "name": "T. Nagar Junction", "area": "Area 2 - South Zone",
         "lat": 13.0418, "lon": 80.2341, "status": "operational", "signal": "Signal #2"},
        {"camera_id": 3, "name": "Anna Salai Junction", "area": "Area 1 - North Zone",
         "lat": 13.0674, "lon": 80.2572, "status": "high_alert", "signal": "Signal #3"},
        {"camera_id": 4, "name": "Velachery Main Road", "area": "Area 3 - East Zone",
         "lat": 12.9815, "lon": 80.2180, "status": "operational", "signal": "Signal #4"},
        {"camera_id": 5, "name": "Perambur Signal", "area": "Area 1 - North Zone",
         "lat": 13.1152, "lon": 80.2459, "status": "operational", "signal": "Signal #5"},
        {"camera_id": 6, "name": "Mylapore Temple", "area": "Area 2 - South Zone",
         "lat": 13.0335, "lon": 80.2680, "status": "operational", "signal": "Signal #6"},
        {"camera_id": 7, "name": "East Coast Road", "area": "Area 3 - East Zone",
         "lat": 12.9939, "lon": 80.2700, "status": "offline", "signal": "Signal #7"},
        {"camera_id": 8, "name": "Guindy Industrial", "area": "Area 4 - West Zone",
         "lat": 13.0067, "lon": 80.2206, "status": "operational", "signal": "Signal #8"},
        {"camera_id": 9, "name": "Poonamallee Highway", "area": "Area 4 - West Zone",
         "lat": 13.0527, "lon": 80.1273, "status": "operational", "signal": "Signal #9"},
        {"camera_id": 10, "name": "Central Station", "area": "Area 5 - Central Zone",
         "lat": 13.0827, "lon": 80.2707, "status": "high_alert", "signal": "Signal #10"},
    ]

    # ─── Areas ────────────────────────────────────────────────────────────────────
    AREAS = [
        {"area_id": 1, "name": "Area 1 - North Zone", "center_lat": 13.1125, "center_lon": 80.2348},
        {"area_id": 2, "name": "Area 2 - South Zone", "center_lat": 13.0418, "center_lon": 80.2341},
        {"area_id": 3, "name": "Area 3 - East Zone", "center_lat": 12.9939, "center_lon": 80.2700},
        {"area_id": 4, "name": "Area 4 - West Zone", "center_lat": 13.0527, "center_lon": 80.1273},
        {"area_id": 5, "name": "Area 5 - Central Zone", "center_lat": 13.0827, "center_lon": 80.2707},
    ]


config = Config()
