import os
import torch
import streamlit as st

# ─── Hardware Detection ───
HAS_CUDA = torch.cuda.is_available()
DEVICE = 'cuda' if HAS_CUDA else 'cpu'
DEVICE_LABEL = "CUDA GPU" if HAS_CUDA else "CPU"

# ─── Constants ───
JWT_SECRET = "cybershield_super_secret_key_2026"
VIDEO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "videos")


COCO_WEAPON_CLASSES = {
    42: "fork",        
    43: "knife", 
    76: "scissors",
    80: "weapon-like"  
}
COCO_VEHICLE_CLASSES = {2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}
COCO_HEAVY = {5: "bus", 7: "truck"}

MOCK_OWNERS = {
    "TN01AB1234": {"owner": "Rajesh Kumar", "model": "Honda City 2020", "color": "White", "phone": "+91-98XXX-12345"},
    "TN02CD5678": {"owner": "Priya Sharma", "model": "Hyundai Creta 2022", "color": "Red", "phone": "+91-87XXX-67890"},
    "KA03EF9012": {"owner": "Vikram Singh", "model": "Maruti Swift 2021", "color": "Blue", "phone": "+91-76XXX-34567"},
     "TN05GH4321": {"owner": "Anjali Devi", "model": "Mahindra Thar 2023", "color": "Black", "phone": "+91-99XXX-11122"},
    "TN06IJ1122": {"owner": "Suresh Raina", "model": "Mahindra Scorpio-N 2023", "color": "White", "phone": "+91-90XXX-55566"},
}

# ─── 6 Camera Definitions ───
CAMERAS = [
    {"id": "CAM-01", "name": "Weapon Detection Zone",       "lat": 13.0523, "lon": 80.2205, "video": "cam1_weapon.mp4",   "task": "weapon",   "icon": "🔫", "desc": "RT-DETR weapon detection (knife/gun)"},
    {"id": "CAM-02", "name": "Facial Recognition Gate",     "lat": 13.0418, "lon": 80.2341, "video": "cam2_faces.mp4",    "task": "faces",    "icon": "🎭", "desc": "Face detect → blur + store in DB"},
    {"id": "CAM-03", "name": "Vehicle Count Highway",       "lat": 13.0012, "lon": 80.2565, "video": "cam3_vehicles.mp4", "task": "vehicles", "icon": "🚗", "desc": "YOLOv8n vehicle count + heavy vehicle alert"},
    {"id": "CAM-04", "name": "ANPR Checkpoint",             "lat": 13.0850, "lon": 80.2101, "video": "cam4_plates.mp4",   "task": "plates",   "icon": "🏷️", "desc": "Number plate OCR + owner lookup"},
    {"id": "CAM-05", "name": "Gender Analytics Corridor",   "lat": 12.9815, "lon": 80.2180, "video": "https://www.youtube.com/watch?v=UemFRPrl1hk", "is_stream": True, "task": "gender",   "icon": "👥", "desc": "Live YouTube Stream + Gender classification"},
    {"id": "CAM-06", "name": "Accident Prediction Junction","lat": 13.0063, "lon": 80.2006, "video": "cam6_accident.mp4", "task": "accident", "icon": "💥", "desc": "Crash prediction model"},
]

def apply_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Inter:wght@300;400;600&display=swap');
        
        html, body, [class*="st-"] { font-family: 'Inter', sans-serif; }
        h1, h2, h3, .cyber-title { font-family: 'Orbitron', sans-serif; }

        .main { background-color: #050a0f; }
        
        .cyber-card {
            background: rgba(10, 25, 41, 0.7);
            border: 1px solid rgba(0, 243, 255, 0.2);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5);
            margin-bottom: 20px;
        }
        
        .cyber-title {
            color: #00f3ff;
            text-shadow: 0 0 15px rgba(0, 243, 255, 0.6);
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 5px;
        }
        
        .alert-badge {
            background: rgba(255, 30, 30, 0.15);
            color: #ff1e1e;
            border: 1px solid #ff1e1e;
            padding: 4px 12px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.75rem;
            text-transform: uppercase;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }

        .ok-badge {
            background: rgba(0, 255, 102, 0.1);
            color: #00ff66;
            border: 1px solid #00ff66;
            padding: 4px 12px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.75rem;
            text-transform: uppercase;
        }
        
        .gpu-badge {
            background: rgba(0, 243, 255, 0.1);
            color: #00f3ff;
            border: 1px solid #00f3ff;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.7rem;
        }

        /* Professional Dashboard Container */
        .dashboard-panel {
            background: #0d1117;
            border-left: 4px solid #00f3ff;
            padding: 15px;
            margin: 10px 0;
        }
    </style>
    """, unsafe_allow_html=True)
