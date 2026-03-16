"""
Simulated Data Layer - Model-Driven Architecture
CyberShield Video Analytics System

This module provides data for Exactly 5 specialized CCTV units:
1. License Plate (ANPR)
2. Face Recognition (Watchlist)
3. Gender Classification (Demographics)
4. Traffic Flow (Analytics)
5. Violence Detection (Public Safety)

All emojis have been removed for a professional interface.
"""

import random
from datetime import datetime, timedelta
import pandas as pd

# Seed for reproducibility
random.seed(42)

VEHICLE_TYPES = ["Car", "Bike", "SUV", "Truck", "Auto", "Bus", "Van"]
VEHICLE_COLORS = ["White", "Black", "Silver", "Grey", "Red", "Blue", "Green", "Yellow", "Orange"]
VEHICLE_MAKES = {
    "Car": ["Honda City", "Hyundai i20", "Maruti Swift", "Tata Nexon", "Toyota Corolla"],
    "SUV": ["Mahindra XUV700", "Toyota Fortuner", "Hyundai Creta", "Kia Seltos", "MG Hector"],
    "Bike": ["Bajaj Pulsar 150", "Hero Splendor", "Yamaha FZ-S", "Royal Enfield Classic", "Honda CB Shine"],
    "Truck": ["Tata 407", "Ashok Leyland", "Eicher Pro", "Mahindra Bolero Pickup"],
    "Auto": ["Bajaj RE", "TVS King", "Piaggio Ape"],
    "Bus": ["Volvo B9R", "Ashok Leyland Viking", "Tata Marcopolo"],
    "Van": ["Tata Ace", "Mahindra Supro", "Force Traveller"],
}

# EXACTLY 5 SPECIALIZED CAMERAS (Matching ACN Dataset)
CAMERAS = [
    {"camera_id": 1, "name": "ParkingLot", "type": "traffic", "area_id": 1, "area": "Parking Zone", "lat": 13.0827, "lon": 80.2707, "status": "operational", "signal": "Strong"},
    {"camera_id": 2, "name": "Road", "type": "traffic", "area_id": 2, "area": "Traffic Zone", "lat": 13.0835, "lon": 80.2715, "status": "operational", "signal": "Excellent"},
    {"camera_id": 3, "name": "StoreOut", "type": "violence", "area_id": 3, "area": "Commercial Zone", "lat": 13.0418, "lon": 80.2341, "status": "operational", "signal": "Fair"},
    {"camera_id": 4, "name": "Street", "type": "violence", "area_id": 4, "area": "Residential Zone", "lat": 13.0527, "lon": 80.1273, "status": "operational", "signal": "Strong"},
    {"camera_id": 5, "name": "Subway", "type": "violence", "area_id": 5, "area": "Transit Zone", "lat": 12.9815, "lon": 80.2180, "status": "operational", "signal": "Good"},
]

AREAS = [
    {"area_id": 1, "name": "Parking Zone", "center_lat": 13.0827, "center_lon": 80.2707},
    {"area_id": 2, "name": "Traffic Zone", "center_lat": 13.0835, "center_lon": 80.2715},
    {"area_id": 3, "name": "Commercial Zone", "center_lat": 13.0418, "center_lon": 80.2341},
    {"area_id": 4, "name": "West Zone", "center_lat": 13.0527, "center_lon": 80.1273},
    {"area_id": 5, "name": "East Zone", "center_lat": 12.9939, "center_lon": 80.2700},
]

POLICE_OFFICERS = [
    {"officer_id": 1, "badge": "12345", "name": "Rajesh Kumar", "area_id": 1, "phone": "+919876543210", "email": "rajesh@police.gov.in", "role": "Senior Inspector"},
    {"officer_id": 2, "badge": "12346", "name": "Priya Sharma", "area_id": 2, "phone": "+919876543211", "email": "priya@police.gov.in", "role": "Officer"},
]

CITIZENS = [
    {
        "citizen_id": 1, "name": "Arjun Mehta", "age": 34, "gender": "Male",
        "dob": "1990-03-12", "blood_group": "O+", "aadhaar": "XXXX-XXXX-3412",
        "driving_license": "TN0120XXXXXXXXX", "phone": "+91-9876512345",
        "email": "arjun.mehta@gmail.com", "occupation": "Software Engineer",
        "emergency_contact": "Sunita Mehta (+91-9876512399)",
    },
    {
        "citizen_id": 2, "name": "Priya Devi", "age": 28, "gender": "Female",
        "dob": "1996-07-25", "blood_group": "B+", "aadhaar": "XXXX-XXXX-7825",
        "driving_license": "TN0220XXXXXXXXX", "phone": "+91-9876512346",
        "email": "priya.devi@yahoo.com", "occupation": "Teacher",
        "emergency_contact": "Rajan Devi (+91-9876512300)",
    },
]

VEHICLES = [
    {
        "vehicle_id": 1, "license_plate": "TN01AB1234", "owner_id": 1,
        "make": "Honda", "model": "City", "year": 2020, "color": "White", "vehicle_type": "Car",
        "registration_valid_till": "2028-05-15", "insurance_company": "New India Assurance",
    },
    {
        "vehicle_id": 2, "license_plate": "TN02CD5678", "owner_id": 2,
        "make": "Hyundai", "model": "i20", "year": 2021, "color": "Silver", "vehicle_type": "Car",
        "registration_valid_till": "2029-03-20", "insurance_company": "ICICI Lombard",
    },
]

CRIMINAL_RECORDS = [
    {"record_id": 1, "citizen_id": 1, "case_type": "Rash Driving", "case_number": "CAS/2023/1234", "case_date": "2023-06-15", "status": "Resolved", "severity": "Medium", "description": "Rash driving on ECR."},
]

WATCHLIST = [
    {"person_id": 1, "name": "Ravi Shankar", "alias": "Ravi Bhai", "age": 35, "case_type": "Murder", "severity": "High", "status": "Active"},
]

# --- Data Generation Functions ---

def generate_vehicle_detections(num_records: int = 50, camera_id: int = None) -> pd.DataFrame:
    records = []
    now = datetime.now()
    # Only use Plate Detection camera if possible
    plate_cams = [c for c in CAMERAS if c["type"] == "plate"] or CAMERAS
    for i in range(num_records):
        cam = next((c for c in CAMERAS if c["camera_id"] == camera_id), random.choice(plate_cams))
        vehicle = random.choice(VEHICLES)
        detected_at = now - timedelta(hours=random.randint(0, 24), minutes=random.randint(0, 59))
        records.append({
            "detection_id": i + 1,
            "license_plate": vehicle["license_plate"],
            "vehicle_type": vehicle["vehicle_type"],
            "color": vehicle["color"],
            "camera_id": cam["camera_id"],
            "camera_name": cam["name"],
            "area_id": cam["area_id"],
            "detected_at": detected_at,
            "confidence": round(random.uniform(0.85, 0.99), 2),
            "speed_kmph": round(random.uniform(20, 80), 1),
        })
    return pd.DataFrame(records).sort_values("detected_at", ascending=False).reset_index(drop=True)

def generate_incidents(num_records: int = 10) -> list:
    incidents = []
    now = datetime.now()
    for i in range(num_records):
        cam = random.choice(CAMERAS)
        itype = cam["type"]
        created = now - timedelta(hours=random.randint(0, 12), minutes=random.randint(0, 59))
        area = next((a for a in AREAS if a["area_id"] == cam["area_id"]), AREAS[0])
        incidents.append({
            "incident_id": i + 1,
            "incident_type": itype,
            "camera_id": cam["camera_id"],
            "camera_name": cam["name"],
            "area_id": cam["area_id"],
            "area_name": area["name"],
            "severity": "High" if itype in ["violence", "face"] else "Medium",
            "confidence": round(random.uniform(0.80, 0.99), 2),
            "lat": cam["lat"], "lon": cam["lon"],
            "status": "Active",
            "description": f"Model detection alert: {itype.upper()} at {cam['name']}",
            "created_at": created,
            "persons_involved": random.randint(1, 5),
        })
    return sorted(incidents, key=lambda x: x["created_at"], reverse=True)

def get_system_metrics() -> dict:
    return {
        "cameras_online": 5, "cameras_total": 5,
        "ai_fps": round(random.uniform(28, 30), 1),
        "cpu_usage": round(random.uniform(40, 60), 1),
        "gpu_usage": round(random.uniform(50, 70), 1),
        "storage_used_gb": 120, "storage_total_gb": 500,
        "active_alerts": random.randint(1, 3),
        "total_vehicles_today": random.randint(400, 600),
        "anpr_captures_today": random.randint(300, 400),
        "people_count_today": random.randint(200, 300),
        "violence_incidents_24h": random.randint(0, 1),
        "face_matches_24h": random.randint(0, 1),
        "response_time_avg_min": 5.2,
        "alert_accuracy": 98.4,
    }

def search_vehicle_by_plate(plate: str) -> dict:
    plate_upper = plate.strip().upper()
    vehicle = next((v for v in VEHICLES if v["license_plate"] == plate_upper), None)
    if not vehicle: return None
    owner = next((c for c in CITIZENS if c["citizen_id"] == vehicle["owner_id"]), None)
    records = [r for r in CRIMINAL_RECORDS if r["citizen_id"] == vehicle["owner_id"]]
    return {"vehicle": vehicle, "owner": owner, "criminal_records": records}

def track_vehicle_journey(plate: str, hours: int = 24) -> list:
    now = datetime.now()
    journey = []
    for idx, cam in enumerate(CAMERAS):
        seen_at = now - timedelta(minutes=random.randint(10, hours*60))
        journey.append({
            "seq": idx + 1, "camera_name": cam["name"], "lat": cam["lat"], "lon": cam["lon"],
            "seen_at": seen_at, "speed_kmph": random.randint(30, 60), "confidence": 0.95,
            "direction": "North"
        })
def generate_hourly_traffic() -> pd.DataFrame:
    base = [10, 5, 3, 2, 2, 5, 20, 45, 90, 75, 60, 70, 80, 65, 55, 60, 85, 110, 95, 70, 55, 40, 30, 20]
    now = datetime.now()
    records = []
    for h in range(24):
        timestamp = now.replace(hour=h, minute=0, second=0, microsecond=0)
        records.append({"hour": h, "timestamp": timestamp,
                        "vehicle_count": max(0, base[h] + random.randint(-5, 10)),
                        "label": f"{h:02d}:00"})
    return pd.DataFrame(records)

def generate_crowd_density() -> list:
    result = []
    for cam in CAMERAS:
        if cam["status"] != "offline":
            density = random.randint(10, 200)
            result.append({
                "lat": cam["lat"] + random.uniform(-0.002, 0.002),
                "lon": cam["lon"] + random.uniform(-0.002, 0.002),
                "density": density,
                "risk_level": "High" if density > 150 else ("Medium" if density > 80 else "Low"),
            })
    return result

def search_vehicles_by_characteristics(vehicle_type: str = None, color: str = None,
                                        area_id: int = None, time_range_hours: int = 24) -> list:
    """Search by type+color. Returns only suspicious owners."""
    results = []
    for vehicle in VEHICLES:
        owner = next((c for c in CITIZENS if c["citizen_id"] == vehicle["owner_id"]), None)
        criminal_records = [r for r in CRIMINAL_RECORDS if r["citizen_id"] == vehicle["owner_id"]]
        type_match = (vehicle_type is None or vehicle_type == "All" or vehicle["vehicle_type"] == vehicle_type)
        if type_match and criminal_records:
            results.append({
                "vehicle": vehicle,
                "owner": owner,
                "criminal_records": criminal_records,
                "last_seen_camera": random.choice(CAMERAS),
                "last_seen_time": datetime.now() - timedelta(minutes=random.randint(5, 120)),
            })
    return results
