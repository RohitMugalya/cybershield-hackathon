"""
CyberShield - Admin Dashboard
AI-Based Integrated Video Analytics System

Main admin interface with:
- PyDeck 3D city visualization
- Real-time analytics
- CCTV feed viewer
- System monitoring
"""

import streamlit as st
import pydeck as pdk
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import random
import time
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from database.simulated_data import (
    CAMERAS, AREAS, POLICE_OFFICERS,
    generate_vehicle_detections, generate_incidents,
    generate_hourly_traffic, generate_crowd_density,
    get_system_metrics,
)
from config import config
try:
    from ai_models.roboflow_client import roboflow_client
    from ai_models.video_processor import simulate_video_analysis, get_video_info
    ROBOFLOW_AVAILABLE = True
except Exception:
    ROBOFLOW_AVAILABLE = False
    roboflow_client = None
    def simulate_video_analysis(name, dur=60): return {"success": False, "frame_results": [], "class_counts": {}, "summary": {}}
    def get_video_info(p): return {}

# ─── Page Configuration ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="CyberShield - Admin Dashboard",
    page_icon="️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;900&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background: linear-gradient(135deg, #0a0a0f 0%, #0d1117 50%, #111827 100%);
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d1117 0%, #161b22 100%);
        border-right: 1px solid #21262d;
    }

    /* Hide Streamlit branding */
    #MainMenu, footer, header { visibility: hidden; }

    /* Cards */
    .cybershield-card {
        background: linear-gradient(135deg, rgba(22,27,34,0.9) 0%, rgba(13,17,23,0.95) 100%);
        border: 1px solid rgba(99,179,237,0.2);
        border-radius: 16px;
        padding: 20px;
        margin: 8px 0;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
        box-shadow: 0 4px 24px rgba(0,0,0,0.4);
    }

    .cybershield-card:hover {
        border-color: rgba(99,179,237,0.5);
        box-shadow: 0 8px 32px rgba(99,179,237,0.15);
        transform: translateY(-2px);
    }

    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, rgba(22,27,34,0.95) 0%, rgba(13,17,23,0.98) 100%);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
        padding: 16px 20px;
        text-align: center;
        position: relative;
        overflow: hidden;
    }

    .metric-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 2px;
        background: linear-gradient(90deg, #00d4ff, #7c3aed, #ec4899);
    }

    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #63b3ed;
        line-height: 1;
    }

    .metric-label {
        font-size: 0.75rem;
        color: #8b949e;
        margin-top: 4px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .metric-delta-pos { color: #10b981; font-size: 0.8rem; }
    .metric-delta-neg { color: #ef4444; font-size: 0.8rem; }

    /* Alert badges */
    .alert-critical {
        background: linear-gradient(135deg, rgba(239,68,68,0.2) 0%, rgba(239,68,68,0.05) 100%);
        border: 1px solid rgba(239,68,68,0.5);
        border-radius: 10px;
        padding: 14px 18px;
        margin: 6px 0;
        border-left: 4px solid #ef4444;
        animation: pulse-red 2s infinite;
    }

    .alert-warning {
        background: linear-gradient(135deg, rgba(245,158,11,0.2) 0%, rgba(245,158,11,0.05) 100%);
        border: 1px solid rgba(245,158,11,0.4);
        border-radius: 10px;
        padding: 14px 18px;
        margin: 6px 0;
        border-left: 4px solid #f59e0b;
    }

    .alert-info {
        background: linear-gradient(135deg, rgba(59,130,246,0.2) 0%, rgba(59,130,246,0.05) 100%);
        border: 1px solid rgba(59,130,246,0.4);
        border-radius: 10px;
        padding: 14px 18px;
        margin: 6px 0;
        border-left: 4px solid #3b82f6;
    }

    @keyframes pulse-red {
        0%, 100% { border-color: rgba(239,68,68,0.5); }
        50% { border-color: rgba(239,68,68,1); box-shadow: 0 0 20px rgba(239,68,68,0.3); }
    }

    /* Status badges */
    .badge-online { background: #064e3b; color: #34d399; padding: 2px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
    .badge-offline { background: #450a0a; color: #f87171; padding: 2px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
    .badge-alert { background: #451a03; color: #fb923c; padding: 2px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }

    /* Header */
    .dashboard-header {
        background: linear-gradient(135deg, rgba(0,212,255,0.1) 0%, rgba(124,58,237,0.15) 50%, rgba(236,72,153,0.1) 100%);
        border: 1px solid rgba(99,179,237,0.2);
        border-radius: 16px;
        padding: 20px 28px;
        margin-bottom: 20px;
        position: relative;
        overflow: hidden;
    }

    .dashboard-header::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        background: linear-gradient(90deg, #00d4ff, #7c3aed, #ec4899, #10b981);
    }

    /* Camera feed placeholder */
    .camera-feed {
        background: linear-gradient(135deg, #0d0d1a 0%, #1a0d2e 100%);
        border: 1px solid rgba(99,179,237,0.3);
        border-radius: 12px;
        height: 200px;
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
        overflow: hidden;
    }

    .feed-scan-line {
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 2px;
        background: linear-gradient(90deg, transparent, #00d4ff, transparent);
        animation: scan 2s linear infinite;
    }

    @keyframes scan {
        0% { top: 0%; }
        100% { top: 100%; }
    }

    /* Table */
    .stDataFrame { border-radius: 12px; overflow: hidden; }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(22,27,34,0.8);
        border-radius: 12px;
        padding: 4px;
        gap: 4px;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        color: #8b949e;
        font-weight: 500;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #1d4ed8, #7c3aed);
        color: white !important;
    }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #0d1117; }
    ::-webkit-scrollbar-thumb { background: #21262d; border-radius: 3px; }
</style>
""", unsafe_allow_html=True)


# ─── Session State Initialization ─────────────────────────────────────────────
def init_session():
    defaults = {
        "selected_camera": None,
        "auto_refresh": True,
        "refresh_interval": 5,
        "incidents": generate_incidents(20),
        "last_refresh": datetime.now(),
        "simulated_alerts": [],
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

init_session()


# ─── Data Loaders ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=10)
def load_metrics():
    return get_system_metrics()

@st.cache_data(ttl=30)
def load_detections():
    return generate_vehicle_detections(150)

@st.cache_data(ttl=60)
def load_hourly_traffic():
    return generate_hourly_traffic()

def get_acn_video_pair(location_name: str):
    """
    Scans the ACN directory and returns a tuple of absolute paths to 
    (view1, view2) videos matching the location.
    Randomly chooses between normal, gun, or knife folders.
    """
    base_path = Path("ACN").resolve()
    if not base_path.exists():
        return None, None
    
    # Map high-level sensor names to file prefixes
    prefix_map = {
        "ParkingLot": "parkingLot",
        "Road": "road",
        "StoreOut": "storeOut",
        "Street": "street",
        "Subway": "subway"
    }
    
    # Try to find a match for the location name
    location_key = None
    for k, v in prefix_map.items():
        if v.lower() in location_name.lower():
            location_key = v
            break
    
    if not location_key:
        return None, None

    # Weighted random: 60% normal, 40% danger (gun/knife)
    scenario_folders = ["normal1", "normal2", "gun", "knife"]
    random.shuffle(scenario_folders)
    
    for folder in scenario_folders:
        dir_path = base_path / folder
        if not dir_path.exists(): continue
        
        # Look for files with matching location for view1
        pattern = f"{location_key}*view1.mp4"
        matches = list(dir_path.glob(pattern))
        if matches:
            view1_path = random.choice(matches)
            # Derive view2 path
            view2_name = view1_path.name.replace("view1", "view2")
            view2_path = dir_path / view2_name
            
            p1 = str(view1_path.absolute()) if view1_path.exists() else None
            p2 = str(view2_path.absolute()) if view2_path.exists() else None
            return p1, p2
            
    return None, None


# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 20px 0;">
        <div style="font-size: 2.5rem; margin-bottom: 8px;">️</div>
        <div style="font-size: 1.3rem; font-weight: 700; background: linear-gradient(90deg, #00d4ff, #7c3aed);
                    -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            CyberShield
        </div>
        <div style="font-size: 0.75rem; color: #8b949e; margin-top: 4px;">Admin Dashboard</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("###  Navigation")
    page = st.radio(
        "Select View",
        ["City Map", "Analytics", "Live Feeds", "AI Video Analysis", "Incidents", "System"],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("###  Controls")
    auto_refresh = st.toggle("Auto Refresh", value=True)
    refresh_interval = st.slider("Refresh (sec)", 5, 60, 10)

    st.markdown("---")
    # System Status in Sidebar
    metrics = load_metrics()
    online_pct = (metrics["cameras_online"] / metrics["cameras_total"]) * 100
    st.markdown("###  System Status")
    st.markdown(f"""
    <div style="font-size:0.82rem; color:#8b949e; line-height:2;">
         Cameras: <b style="color:#34d399">{metrics['cameras_online']}</b>/{metrics['cameras_total']} online<br>
         AI FPS: <b style="color:#63b3ed">{metrics['ai_fps']}</b><br>
         Storage: <b style="color:#a78bfa">{metrics['storage_used_gb']}</b>/{metrics['storage_total_gb']} GB<br>
         Active Alerts: <b style="color:#f87171">{metrics['active_alerts']}</b>
    </div>
    """, unsafe_allow_html=True)

    st.progress(online_pct / 100, text=f"Camera Health: {online_pct:.0f}%")

    st.markdown("---")
    st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
    if st.button(" Refresh Now", width="stretch"):
        st.cache_data.clear()
        st.rerun()


# ─── Header ───────────────────────────────────────────────────────────────────
now = datetime.now()
st.markdown(f"""
<div class="dashboard-header">
    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
        <div>
            <div style="font-size:1.5rem; font-weight:800; color:#e2e8f0;">
                ️ CyberShield Admin Dashboard
            </div>
            <div style="font-size:0.85rem; color:#8b949e; margin-top:4px;">
                AI-Based Integrated Video Analytics System
            </div>
        </div>
        <div style="text-align:right;">
            <div style="font-size:1.1rem; font-weight:600; color:#63b3ed;">
                {now.strftime('%A, %d %B %Y')}
            </div>
            <div style="font-size:0.85rem; color:#8b949e;">{now.strftime('%H:%M:%S')} IST</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# ─── Animated Top KPI Dashboard ───────────────────────────────────────────────
metrics = load_metrics()

# --- Professional Top KPI Dashboard ---
metrics = load_metrics()

# Row 1 - 8 KPI tiles
kpi_cols = st.columns(8)
kpi_items = [
    ("VEHICLES TODAY", metrics["total_vehicles_today"], "Total Volume", "+12% ↑", "#38bdf8"),
    ("ANPR CAPTURES", metrics["anpr_captures_today"], "Plates Identified", "+8% ↑", "#818cf8"),
    ("PEOPLE COUNT", metrics["people_count_today"], "Live Count", "Steady", "#34d399"),
    ("ACTIVE ALERTS", metrics["active_alerts"], "High Severity", "Real-time", "#f87171"),
    ("SYSTEM FPS", f"{metrics['ai_fps']}", "Processing Rate", "Nominal", "#fb923c"),
    ("MODEL ACCURACY", f"{metrics['alert_accuracy']}%", "Inference Confidence", "Validated", "#10b981"),
    ("CAMERA STATUS", f"{metrics['cameras_online']}/{metrics['cameras_total']}", "Sensors Active", "Online", "#a78bfa"),
    ("RESPONSE TIME", f"{metrics['response_time_avg_min']}m", "Avg Dispatch", "Optimal", "#f472b6"),
]

for col, (header, val, sublabel, trend, color) in zip(kpi_cols, kpi_items):
    with col:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,rgba(22,27,34,0.98),rgba(13,17,23,0.99));
                    border:1px solid {color}25; border-radius:14px; padding:14px 10px;
                    text-align:center; position:relative; overflow:hidden;
                    box-shadow:0 2px 12px {color}15; transition:all .3s;">
            <div style="position:absolute;top:0;left:0;right:0;height:3px;
                        background:linear-gradient(90deg,{color},{color}55);"></div>
            <div style="font-size:0.65rem;color:#8b949e;margin-bottom:8px;font-weight:600;text-transform:uppercase;letter-spacing:1px;">{header}</div>
            <div style="font-size:1.6rem;font-weight:800;color:{color};line-height:1;">{val}</div>
            <div style="font-size:0.62rem;color:#6b7280;margin-top:6px;">{sublabel}</div>
            <div style="font-size:0.6rem;color:{color}CC;margin-top:2px;font-weight:700;">{trend}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── Live Counters Row ────────────────────────────────────────────────────────
violence_24h = metrics["violence_incidents_24h"]
face_24h = metrics["face_matches_24h"]
cpu_pct = metrics["cpu_usage"]
gpu_pct = metrics["gpu_usage"]
storage_pct = round(metrics["storage_used_gb"] / metrics["storage_total_gb"] * 100, 1)

status_cols = st.columns([1, 1, 1, 1, 1])
status_items = [
    ("VIOLENCE EVENTS", f"{violence_24h}", "Aggregated", "#ef4444", violence_24h > 0),
    ("FACE MATCHES", f"{face_24h}", "Watchlist", "#f97316", face_24h > 0),
    ("CPU LOAD", f"{cpu_pct}%", "Compute", "#38bdf8", cpu_pct > 80),
    ("GPU LOAD", f"{gpu_pct}%", "Graphics", "#818cf8", gpu_pct > 85),
    ("STORAGE LOAD", f"{storage_pct}%", "Disk", "#34d399", storage_pct > 80),
]

for col, (header, val, sublabel, color, alert) in zip(status_cols, status_items):
    with col:
        bg = f"rgba(239,68,68,0.1)" if alert else "rgba(22,27,34,0.9)"
        border = f"rgba(239,68,68,0.4)" if alert else f"{color}22"
        st.markdown(f"""
        <div style="background:{bg}; border:1px solid {border}; border-radius:12px;
                    padding:12px 16px; display:flex; flex-direction:column; gap:4px;">
            <div style="font-size:0.6rem;color:#8b949e;text-transform:uppercase;letter-spacing:1px;font-weight:600;">{header}</div>
            <div style="display:flex; align-items:baseline; gap:8px;">
                <div style="font-size:1.4rem;font-weight:700;color:{color};">{val}</div>
                <div style="font-size:0.65rem;color:#6b7280;">{sublabel}</div>
            </div>
            {'<div style="color:#ef4444;font-size:0.6rem;font-weight:700;">ALERT: CAPACITY REACHED</div>' if alert else ''}
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: 3D CITY MAP
# ═══════════════════════════════════════════════════════════════════════════════
if "City Map" in page:
    st.markdown("## Interactive City Map - Chennai")
    st.caption("Select regions to view localized intelligence. Dynamic layers indicate incident density.")

    # Build camera data for map
    camera_df = pd.DataFrame(CAMERAS)
    camera_df["status_color"] = camera_df["status"].map({
        "operational": [0, 200, 255, 200],
        "offline": [255, 50, 50, 200],
        "high_alert": [255, 150, 0, 220],
    })
    camera_df["size"] = 80

    # Traffic density data
    traffic_data = []
    for cam in CAMERAS:
        if cam["status"] != "offline":
            count = random.randint(20, 150)
            traffic_data.append({
                "lat": cam["lat"] + random.uniform(-0.003, 0.003),
                "lon": cam["lon"] + random.uniform(-0.003, 0.003),
                "count": count,
                "color": [min(255, count * 2), max(0, 255 - count * 2), 50, 180],
            })

    traffic_df = pd.DataFrame(traffic_data)

    # Crowd density
    crowd_data = generate_crowd_density()
    crowd_df = pd.DataFrame(crowd_data)
    crowd_df["color"] = crowd_df["risk_level"].map({
        "High": [255, 50, 50, 160],
        "Medium": [255, 165, 0, 140],
        "Low": [50, 205, 100, 120],
    })

    # ─── PyDeck Layers ────────────────────────────────────────────────────────
    # 1. Hexagon traffic layer
    hexagon_layer = pdk.Layer(
        "HexagonLayer",
        data=traffic_df,
        get_position=["lon", "lat"],
        get_elevation_weight="count",
        elevation_scale=8,
        elevation_range=[0, 300],
        radius=300,
        pickable=True,
        extruded=True,
        coverage=0.85,
        color_range=[
            [0, 255, 200, 120],
            [0, 180, 255, 140],
            [50, 100, 255, 160],
            [150, 50, 255, 180],
            [255, 50, 150, 200],
            [255, 30, 30, 220],
        ],
    )

    # 2. Camera scatter/icon layer
    camera_layer = pdk.Layer(
        "ScatterplotLayer",
        data=camera_df,
        get_position=["lon", "lat"],
        get_fill_color="status_color",
        get_radius="size",
        pickable=True,
        auto_highlight=True,
        radiusScale=3,
        radiusMinPixels=8,
        radiusMaxPixels=25,
        stroked=True,
        get_line_color=[255, 255, 255, 100],
        line_width_min_pixels=1,
    )

    # 3. Camera text labels
    text_layer = pdk.Layer(
        "TextLayer",
        data=camera_df,
        get_position=["lon", "lat"],
        get_text="name",
        get_size=12,
        get_color=[200, 220, 255, 200],
        get_angle=0,
        get_alignment_baseline="'bottom'",
        pickable=True,
    )

    # 4. Arc layer (simulated vehicle flow)
    if len(CAMERAS) >= 2:
        arc_data = []
        for i in range(min(8, len(CAMERAS))):
            src = CAMERAS[i]
            dst = CAMERAS[(i + 1) % len(CAMERAS)]
            arc_data.append({
                "source_lat": src["lat"], "source_lon": src["lon"],
                "target_lat": dst["lat"], "target_lon": dst["lon"],
                "count": random.randint(10, 80),
            })
        arc_df = pd.DataFrame(arc_data)
        arc_layer = pdk.Layer(
            "ArcLayer",
            data=arc_df,
            get_source_position=["source_lon", "source_lat"],
            get_target_position=["target_lon", "target_lat"],
            get_source_color=[0, 212, 255, 120],
            get_target_color=[124, 58, 237, 120],
            auto_highlight=True,
            width_scale=0.5,
            get_width=2,
            tilt=15,
            pickable=True,
        )
        map_layers = [hexagon_layer, arc_layer, camera_layer, text_layer]
    else:
        map_layers = [hexagon_layer, camera_layer, text_layer]

    # Map view
    view_state = pdk.ViewState(
        latitude=config.MAP_CENTER_LAT,
        longitude=config.MAP_CENTER_LON,
        zoom=config.MAP_DEFAULT_ZOOM,
        pitch=50,
        bearing=10,
    )

    deck = pdk.Deck(
        layers=map_layers,
        initial_view_state=view_state,
        map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
        tooltip={
            "html": "<b> {name}</b><br>Area: {area}<br>Status: {status}<br>Signal: {signal}",
            "style": {
                "backgroundColor": "#0d1117",
                "color": "#63b3ed",
                "border": "1px solid #21262d",
                "borderRadius": "8px",
                "font": "14px Inter, sans-serif",
                "padding": "10px",
            },
        },
    )

    col_map, col_side = st.columns([2, 1])

    with col_map:
        st.pydeck_chart(deck)

        # Map legend
        st.markdown("""
        <div style="display:flex; gap:16px; padding:12px; background:rgba(22,27,34,0.8);
                    border-radius:10px; margin-top:8px; flex-wrap:wrap; font-size:0.75rem;">
            <span style="color:#00c8ff;">Operational</span>
            <span style="color:#ff3232;">Offline</span>
            <span style="color:#ff9600;">High Alert</span>
            <span style="color:#00d4ff;">Traffic Flow</span>
            <span style="color:#7c3aed;">Volume Density</span>
        </div>
        """, unsafe_allow_html=True)

    with col_side:
        st.markdown("### Areas")
        for cam in CAMERAS:
            status_text = cam["status"].replace("_", " ").title()
            with st.expander(f"{cam['name']}", expanded=False):
                st.markdown(f"""
                <div style="font-size:0.82rem; color:#8b949e; line-height:2;">
                    Type: <b style="color:#63b3ed;">{cam['type'].upper()}</b><br>
                    Status: <b style="color:{'#34d399' if cam['status']=='operational' else '#ef4444'};">{status_text}</b><br>
                    Throughput: <b style="color:#a78bfa;">{random.randint(5, 45)} units/min</b>
                </div>
                """, unsafe_allow_html=True)
                if st.button(" View Analytics", key=f"cam_btn_{cam['camera_id']}", width="stretch"):
                    st.session_state.selected_camera = cam["camera_id"]
                    st.rerun()

    # Camera Detail Panel
    if st.session_state.selected_camera:
        cam_id = st.session_state.selected_camera
        cam = next((c for c in CAMERAS if c["camera_id"] == cam_id), None)
        if cam:
            st.markdown("---")
            st.markdown(f"###  {cam['name']}")
            col_feed, col_analytics = st.columns([3, 2])

            with col_feed:
                # Select a synchronized video pair from ACN
                v1_path, v2_path = get_acn_video_pair(cam['name'])
                
                if v1_path:
                    try:
                        import base64
                        with open(v1_path, 'rb') as vf1:
                            video_bytes1 = vf1.read()
                        
                        # Display both videos side-by-side with synchronized playback and no controls
                        if v2_path:
                            with open(v2_path, 'rb') as vf2:
                                video_bytes2 = vf2.read()
                            
                            # Encode videos to base64
                            v1_b64 = base64.b64encode(video_bytes1).decode()
                            v2_b64 = base64.b64encode(video_bytes2).decode()
                            
                            st.markdown("""
                            <style>
                                .video-container {
                                    display: flex;
                                    gap: 10px;
                                    margin-bottom: 10px;
                                }
                                .video-wrapper {
                                    flex: 1;
                                    display: flex;
                                    flex-direction: column;
                                    gap: 8px;
                                }
                                .video-wrapper video {
                                    width: 100%;
                                    border-radius: 8px;
                                    border: 1px solid #21262d;
                                }
                                .video-label {
                                    font-size: 0.8rem;
                                    color: #8b949e;
                                    text-align: center;
                                }
                            </style>
                            """, unsafe_allow_html=True)
                            
                            st.markdown(f"""
                            <!-- Camera ID: {cam_id} -->
                            <div class="video-container">
                                <div class="video-wrapper">
                                    <video id="video1_{cam_id}" autoplay muted loop style="background: #0d0d1a;">
                                        <source src="data:video/mp4;base64,{v1_b64}" type="video/mp4">
                                    </video>
                                    <div class="video-label">Primary View</div>
                                </div>
                                <div class="video-wrapper">
                                    <video id="video2_{cam_id}" autoplay muted loop style="background: #0d0d1a;">
                                        <source src="data:video/mp4;base64,{v2_b64}" type="video/mp4">
                                    </video>
                                    <div class="video-label">Secondary View</div>
                                </div>
                            </div>
                            <script>
                                // Synchronize video playback
                                const video1 = document.getElementById('video1_{cam_id}');
                                const video2 = document.getElementById('video2_{cam_id}');
                                
                                if (video1 && video2) {{
                                    video1.addEventListener('play', () => video2.play());
                                    video1.addEventListener('pause', () => video2.pause());
                                    video1.addEventListener('seek', () => {{ video2.currentTime = video1.currentTime; }});
                                    video1.addEventListener('timeupdate', () => {{
                                        if (Math.abs(video1.currentTime - video2.currentTime) > 0.5) {{
                                            video2.currentTime = video1.currentTime;
                                        }}
                                    }});
                                }}
                            </script>
                            """, unsafe_allow_html=True)
                        else:
                            # Single video only
                            v1_b64 = base64.b64encode(video_bytes1).decode()
                            st.markdown(f"""
                            <!-- Camera ID: {cam_id} -->
                            <video autoplay muted loop style="width: 100%; border-radius: 8px; border: 1px solid #21262d; background: #0d0d1a;">
                                <source src="data:video/mp4;base64,{v1_b64}" type="video/mp4">
                            </video>
                            """, unsafe_allow_html=True)
                            st.caption(f"Source: {Path(v1_path).name} (Primary View)")
                    except Exception as e:
                        st.error(f"Error loading media: {e}")
                else:
                    st.markdown(f"""
                    <div class="camera-feed">
                        <div class="feed-scan-line"></div>
                        <div style="text-align:center; color:#8b949e;">
                            <div style="font-size:3rem;"></div>
                            <div style="font-size:1rem; font-weight:600; color:#63b3ed; margin-top:8px;">
                                 {cam['name']}
                            </div>
                            <div style="font-size:0.8rem; margin-top:4px;">
                                 LIVE · {cam['signal']}
                            </div>
                            <div style="font-size:0.75rem; color:#555; margin-top:8px;">
                                Connect RTSP stream for live feed
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            with col_analytics:
                vcount = random.randint(5, 40)
                pcount = random.randint(2, 15)
                speed = random.uniform(25, 65)
                traffic_level = "High" if vcount > 30 else ("Medium" if vcount > 15 else "Low")
                level_color = "#ef4444" if traffic_level == "High" else ("#f59e0b" if traffic_level == "Medium" else "#10b981")

                st.markdown(f"""
                <div class="cybershield-card">
                    <div style="font-size:0.9rem; font-weight:600; color:#e2e8f0; margin-bottom:12px;">
                         Live Metrics
                    </div>
                    <div style="font-size:0.82rem; color:#8b949e; line-height: 2.2;">
                         Vehicles/min: <b style="color:#63b3ed;">{vcount}</b><br>
                         People: <b style="color:#a78bfa;">{pcount}</b><br>
                         Avg Speed: <b style="color:#fb923c;">{speed:.1f} km/h</b><br>
                         Traffic: <b style="color:{level_color};">{traffic_level}</b>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Vehicle breakdown
                vtype_data = {"Car": random.randint(3, 15), "Bike": random.randint(2, 10),
                              "SUV": random.randint(1, 8), "Auto": random.randint(1, 5)}
                fig_pie = px.pie(
                    names=list(vtype_data.keys()),
                    values=list(vtype_data.values()),
                    title="Vehicle Types",
                    hole=0.55,
                    color_discrete_sequence=["#63b3ed", "#a78bfa", "#34d399", "#fb923c"],
                )
                fig_pie.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#8b949e",
                    title_font_color="#e2e8f0",
                    showlegend=True,
                    margin=dict(t=40, b=0, l=0, r=0),
                    height=200,
                )
                fig_pie.update_traces(textfont_size=10)
                st.plotly_chart(fig_pie, width="stretch")

            if st.button("Close Camera View"):
                st.session_state.selected_camera = None
                st.rerun()


# --- PAGE: ANALYTICS ---
elif "Analytics" in page:
    st.markdown("## System Intelligence Analytics")

    detections = load_detections()
    hourly_df = load_hourly_traffic()

    tab1, tab2, tab3 = st.tabs(["Traffic Analytics", "Security Analytics", "AI Performance"])

    with tab1:
        col_left, col_right = st.columns(2)

        with col_left:
            # Hourly traffic
            fig_hourly = go.Figure()
            fig_hourly.add_trace(go.Scatter(
                x=hourly_df["label"],
                y=hourly_df["vehicle_count"],
                mode="lines+markers",
                line=dict(color="#63b3ed", width=2.5, shape="spline"),
                marker=dict(size=6, color="#63b3ed"),
                fill="tozeroy",
                fillcolor="rgba(99,179,237,0.12)",
                name="Vehicles",
            ))
            fig_hourly.add_hrect(y0=100, y1=hourly_df["vehicle_count"].max() + 10,
                                  fillcolor="rgba(239,68,68,0.08)",
                                  line_color="rgba(239,68,68,0.4)",
                                  annotation_text="Alert Threshold", annotation_position="top left",
                                  annotation=dict(font_color="#ef4444", font_size=11))
            fig_hourly.update_layout(
                title="Hourly Vehicle Count (24h)", title_font_color="#e2e8f0",
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#8b949e", height=300,
                xaxis=dict(gridcolor="#21262d", tickfont_size=10),
                yaxis=dict(gridcolor="#21262d"),
                margin=dict(t=40, b=0, l=0, r=0),
            )
            st.plotly_chart(fig_hourly, width="stretch")

            # Vehicle type breakdown
            type_counts = detections["vehicle_type"].value_counts()
            fig_bar = px.bar(
                x=type_counts.index, y=type_counts.values,
                title="Vehicle Type Distribution",
                color=type_counts.values,
                color_continuous_scale="Viridis",
                labels={"x": "Type", "y": "Count"},
            )
            fig_bar.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#8b949e", title_font_color="#e2e8f0", height=280,
                xaxis=dict(gridcolor="#21262d"), yaxis=dict(gridcolor="#21262d"),
                showlegend=False, coloraxis_showscale=False,
                margin=dict(t=40, b=0, l=0, r=0),
            )
            st.plotly_chart(fig_bar, width="stretch")

        with col_right:
            # Area-wise vehicle count
            area_counts = detections.groupby("area_id")["detection_id"].count().reset_index()
            area_counts["area_name"] = area_counts["area_id"].map(
                {a["area_id"]: a["name"] for a in AREAS}
            )
            fig_area = px.bar(
                area_counts, x="area_name", y="detection_id",
                title="Detections by Area",
                color="detection_id",
                color_continuous_scale="Plasma",
                labels={"detection_id": "Count", "area_name": ""},
            )
            fig_area.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#8b949e", title_font_color="#e2e8f0", height=280,
                xaxis=dict(gridcolor="#21262d", tickangle=-20, tickfont_size=10),
                yaxis=dict(gridcolor="#21262d"),
                showlegend=False, coloraxis_showscale=False,
                margin=dict(t=40, b=0, l=0, r=0),
            )
            st.plotly_chart(fig_area, width="stretch")

            # Speed distribution
            fig_speed = go.Figure(go.Histogram(
                x=detections["speed_kmph"],
                nbinsx=20,
                marker_color="#a78bfa",
                opacity=0.85,
            ))
            fig_speed.add_vline(x=60, line_dash="dash", line_color="#ef4444",
                                annotation_text="Speed Limit (60 km/h)",
                                annotation_font_color="#ef4444")
            fig_speed.update_layout(
                title="Vehicle Speed Distribution",
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#8b949e", title_font_color="#e2e8f0", height=280,
                xaxis=dict(title="Speed (km/h)", gridcolor="#21262d"),
                yaxis=dict(title="Count", gridcolor="#21262d"),
                margin=dict(t=40, b=0, l=0, r=0),
            )
            st.plotly_chart(fig_speed, width="stretch")

        # ANPR Recent Detections Table
        st.markdown("###  Recent ANPR Detections")
        display_df = detections.head(15)[["detected_at", "license_plate", "vehicle_type", "color", "camera_name", "confidence", "speed_kmph"]].copy()
        display_df["detected_at"] = display_df["detected_at"].dt.strftime("%H:%M:%S")
        display_df.columns = ["Time", "Plate", "Type", "Color", "Camera", "Confidence", "Speed (km/h)"]
        st.dataframe(
            display_df,
            width="stretch",
            hide_index=True,
            column_config={
                "Confidence": st.column_config.ProgressColumn("Confidence", min_value=0, max_value=1),
                "Speed (km/h)": st.column_config.NumberColumn("Speed (km/h)", format="%.1f"),
            }
        )

    with tab2:
        incidents = generate_incidents(20)

        col_sec1, col_sec2 = st.columns(2)
        with col_sec1:
            # Incidents by type
            inc_types = {}
            for inc in incidents:
                t = inc["incident_type"]
                inc_types[t] = inc_types.get(t, 0) + 1

            fig_inc = px.pie(
                names=list(inc_types.keys()),
                values=list(inc_types.values()),
                title="Incidents by Type (24h)",
                hole=0.45,
                color_discrete_sequence=px.colors.sequential.Plasma,
            )
            fig_inc.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#8b949e", title_font_color="#e2e8f0", height=300,
                margin=dict(t=40, b=0, l=0, r=0),
            )
            st.plotly_chart(fig_inc, width="stretch")

        with col_sec2:
            # Incidents by severity
            sev_counts = {}
            for inc in incidents:
                s = inc["severity"]
                sev_counts[s] = sev_counts.get(s, 0) + 1

            colors_map = {"Critical": "#ef4444", "High": "#f97316", "Medium": "#f59e0b", "Low": "#10b981"}
            fig_sev = go.Figure(go.Bar(
                x=list(sev_counts.keys()),
                y=list(sev_counts.values()),
                marker_color=[colors_map.get(k, "#888") for k in sev_counts.keys()],
            ))
            fig_sev.update_layout(
                title="Incidents by Severity",
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#8b949e", title_font_color="#e2e8f0", height=300,
                xaxis=dict(gridcolor="#21262d"), yaxis=dict(gridcolor="#21262d"),
                margin=dict(t=40, b=0, l=0, r=0),
                showlegend=False,
            )
            st.plotly_chart(fig_sev, width="stretch")

        # Recent incidents
        st.markdown("###  Recent Security Incidents")
        for inc in incidents[:8]:
            sev_colors = {"Critical": "#ef4444", "High": "#f97316", "Medium": "#f59e0b", "Low": "#10b981"}
            alert_class = "alert-critical" if inc["severity"] in ["Critical"] else ("alert-warning" if inc["severity"] in ["High", "Medium"] else "alert-info")
            sev_col = sev_colors.get(inc["severity"], "#888")
            st.markdown(f"""
            <div class="{alert_class}">
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
                    <div>
                        <b style="color:#e2e8f0;">{inc['incident_type'].replace('_', ' ').title()}</b>
                        <span style="color:#8b949e; margin-left:8px; font-size:0.8rem;">
                             {inc['camera_name']} · {inc['area_name']}
                        </span>
                    </div>
                    <div style="text-align:right;">
                        <span style="color:{sev_col}; font-weight:600; font-size:0.82rem;">{inc['severity']}</span>
                        <span style="color:#8b949e; font-size:0.75rem; margin-left:8px;">
                            {inc['created_at'].strftime('%H:%M')}
                        </span>
                    </div>
                </div>
                <div style="color:#8b949e; font-size:0.8rem; margin-top:6px;">
                    {inc['description']} · Confidence: {inc['confidence']*100:.0f}%
                </div>
            </div>
            """, unsafe_allow_html=True)

    with tab3:
        st.markdown("###  AI Model Performance")
        col_ai1, col_ai2 = st.columns(2)

        models = [
            {"name": "YOLOv8 - Vehicle Detection", "fps": random.uniform(24, 30),
             "accuracy": random.uniform(92, 98), "status": "Running"},
            {"name": "EasyOCR - ANPR", "fps": random.uniform(10, 18),
             "accuracy": random.uniform(88, 95), "status": "Running"},
            {"name": "DeepFace - Recognition", "fps": random.uniform(5, 12),
             "accuracy": random.uniform(90, 97), "status": "Running"},
            {"name": "Violence Detection", "fps": random.uniform(20, 28),
             "accuracy": random.uniform(89, 96), "status": "Running"},
        ]

        with col_ai1:
            for model in models:
                st.markdown(f"""
                <div class="cybershield-card" style="margin-bottom:10px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <div style="font-weight:600; color:#e2e8f0; font-size:0.9rem;">{model['name']}</div>
                            <div style="color:#8b949e; font-size:0.75rem; margin-top:3px;">
                                 {model['fps']:.1f} FPS ·  {model['accuracy']:.1f}% Accuracy
                            </div>
                        </div>
                        <span class="badge-online">{model['status']}</span>
                    </div>
                    <div style="margin-top:10px;">
                        <div style="background:#21262d; border-radius:4px; height:4px;">
                            <div style="background: linear-gradient(90deg, #00d4ff, #7c3aed);
                                        width:{model['accuracy']}%; height:100%; border-radius:4px;"></div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        with col_ai2:
            # Radar chart for AI performance
            model_names = [m["name"].split(" - ")[0] for m in models]
            accuracy_vals = [m["accuracy"] for m in models]
            fps_normalized = [m["fps"] / 30 * 100 for m in models]

            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=accuracy_vals + [accuracy_vals[0]],
                theta=model_names + [model_names[0]],
                fill="toself",
                name="Accuracy (%)",
                line_color="#63b3ed",
                fillcolor="rgba(99,179,237,0.15)",
            ))
            fig_radar.add_trace(go.Scatterpolar(
                r=fps_normalized + [fps_normalized[0]],
                theta=model_names + [model_names[0]],
                fill="toself",
                name="Speed (normalized)",
                line_color="#a78bfa",
                fillcolor="rgba(167,139,250,0.15)",
            ))
            fig_radar.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, 100], gridcolor="#21262d", tickfont_color="#8b949e"),
                    angularaxis=dict(gridcolor="#21262d"),
                    bgcolor="rgba(0,0,0,0)",
                ),
                showlegend=True,
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#8b949e",
                height=320,
                title="AI Performance Radar",
                title_font_color="#e2e8f0",
                margin=dict(t=50, b=20, l=30, r=30),
            )
            st.plotly_chart(fig_radar, width="stretch")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: LIVE FEEDS
# ═══════════════════════════════════════════════════════════════════════════════
elif " Live Feeds" in page:
    st.markdown("##  Live CCTV Feed Monitor")

    # Filter controls
    col_f1, col_f2 = st.columns([1, 3])
    with col_f1:
        status_filter = st.selectbox("Status Filter", ["All", "Operational", "High Alert", "Offline"])
    with col_f2:
        st.markdown("<br>", unsafe_allow_html=True)

    # Filter cameras
    filtered_cams = CAMERAS
    if status_filter == "Operational":
        filtered_cams = [c for c in CAMERAS if c["status"] == "operational"]
    elif status_filter == "High Alert":
        filtered_cams = [c for c in CAMERAS if c["status"] == "high_alert"]
    elif status_filter == "Offline":
        filtered_cams = [c for c in CAMERAS if c["status"] == "offline"]

    # Camera grid
    cols_per_row = 3
    for row_start in range(0, len(filtered_cams), cols_per_row):
        row_cams = filtered_cams[row_start:row_start + cols_per_row]
        cols = st.columns(cols_per_row)

        for col, cam in zip(cols, row_cams):
            status_icon = "" if cam["status"] == "operational" else ("" if cam["status"] == "offline" else "")
            v_count = random.randint(3, 30) if cam["status"] != "offline" else 0
            p_count = random.randint(1, 10) if cam["status"] != "offline" else 0

            with col:
                st.markdown(f"""
                <div style="font-weight:600; color:#e2e8f0; font-size:0.85rem; margin-bottom:8px;">
                    {status_icon} Cam {cam['camera_id']} — {cam['name']}
                </div>
                """, unsafe_allow_html=True)
                
                # Try to get ACN video for the grid preview
                v1_path, _ = get_acn_video_pair(cam['name'])
                
                if v1_path:
                    try:
                        with open(v1_path, 'rb') as vf1:
                            st.video(vf1.read(), format="video/mp4", loop=True, autoplay=True, muted=True)
                    except Exception:
                        pass
                else:
                    st.markdown(f"""
                    <div class="camera-feed" style="height:140px;">
                        {'<div class="feed-scan-line"></div>' if cam['status'] != 'offline' else ''}
                        <div style="text-align:center; color:#8b949e;">
                            <div style="font-size:2rem;"></div>
                            <div style="font-size:0.75rem; margin-top:6px; color:{'#34d399' if cam['status']=='operational' else ('#f97316' if cam['status']=='high_alert' else '#ef4444')};">
                                {' LIVE' if cam['status'] != 'offline' else '⚫ OFFLINE'}
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div style="font-size:0.75rem; color:#8b949e; margin-top:8px; line-height:1.8; background:rgba(22,27,34,0.5); padding:8px; border-radius:8px;">
                     Signal: <b style="color:#63b3ed;">{cam['signal']}</b><br>
                     Activity: <b style="color:#e2e8f0;">{v_count} vehicles · {p_count} people</b>
                </div>
                """, unsafe_allow_html=True)


# --- PAGE: AI VIDEO ANALYSIS ---
elif "AI Video Analysis" in page:
    st.markdown("## AI Video Analysis Dispatch")
    st.caption("Upload video assets for automated model inference and categorical analysis.")

    uploaded_video = st.file_uploader("Upload Video File", type=["mp4", "avi", "mov", "mkv"])

    if uploaded_video:
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_video.name).suffix) as tf:
            tf.write(uploaded_video.read())
            temp_path = tf.name

        st.info(f"Processing asset: {uploaded_video.name}")
        progress_bar = st.progress(0, text="Extracting frames and performing inference...")

        # Model mapping based on filename or context
        model_type = "traffic"
        if any(w in uploaded_video.name.lower() for w in ["plate", "car", "vehicle"]): model_type = "plate"
        elif any(w in uploaded_video.name.lower() for w in ["face", "person"]): model_type = "face"
        elif any(w in uploaded_video.name.lower() for w in ["gender", "crowd"]): model_type = "gender"
        elif any(w in uploaded_video.name.lower() for w in ["violence", "fight"]): model_type = "violence"

        # Determine which Roboflow model ID to use
        conf_map = {
            "plate": os.getenv("ROBOFLOW_PLATE_ID"),
            "face": os.getenv("ROBOFLOW_FACE_ID"),
            "gender": os.getenv("ROBOFLOW_GENDER_ID"),
            "traffic": os.getenv("ROBOFLOW_TRAFFIC_ID"),
            "violence": os.getenv("ROBOFLOW_VIOLENCE_ID"),
        }
        active_model_id = conf_map.get(model_type, os.getenv("ROBOFLOW_WORKFLOW_URL"))

        # Run analysis (simulated if no key)
        if ROBOFLOW_AVAILABLE:
            results = simulate_video_analysis(uploaded_video.name) # Using simulation for demo stability
        else:
            results = simulate_video_analysis(uploaded_video.name)

        progress_bar.progress(1.0, text="Analysis complete.")

        if results["success"]:
            summary = results["summary"]
            st.success(f"Analysis complete for {summary['filename']}. Categorized as {model_type.upper()}.")

            # Metrics Row
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Detections", summary["total_detections"])
            m2.metric("Confidence", f"{random.randint(92,99)}%")
            m3.metric("Frames", summary["frames_processed"])
            m4.metric("Throughput", "30 FPS")

            # Visualization
            st.markdown("### Detection Timeline")
            df = pd.DataFrame(results["frame_results"])
            fig = px.line(df, x="timestamp_sec", y="detection_count", title="Inference Frequency Over Time")
            fig.update_layout(template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, width="stretch")

            st.markdown("### Class Distribution")
            class_df = pd.DataFrame(list(results["class_counts"].items()), columns=["Category", "Count"])
            fig2 = px.pie(class_df, values="Count", names="Category", hole=0.4)
            fig2.update_layout(template="plotly_dark")
            st.plotly_chart(fig2, width="stretch")
        else:
            st.error("Model inference failed. Please check configuration.")

# --- PAGE: INCIDENTS ---
elif "Incidents" in page:
    st.markdown("## Incident Management Console")

    col_inc1, col_inc2, col_inc3 = st.columns(3)
    with col_inc1:
        severity_filter = st.selectbox("Severity", ["All", "Critical", "High", "Medium", "Low"])
    with col_inc2:
        type_filter = st.selectbox("Type", ["All", "violence", "traffic", "face_match", "loitering", "speeding", "suspicious"])
    with col_inc3:
        status_filter_inc = st.selectbox("Status", ["All", "Active", "Responded", "Resolved"])

    incidents = generate_incidents(30)

    # Apply filters
    filtered = incidents
    if severity_filter != "All":
        filtered = [i for i in filtered if i["severity"] == severity_filter]
    if type_filter != "All":
        filtered = [i for i in filtered if i["incident_type"] == type_filter]
    if status_filter_inc != "All":
        filtered = [i for i in filtered if i["status"] == status_filter_inc]

    st.markdown(f"**{len(filtered)} incidents found**")

    for inc in filtered[:20]:
        sev_colors = {"Critical": "#ef4444", "High": "#f97316", "Medium": "#f59e0b", "Low": "#10b981"}
        alert_class = "alert-critical" if inc["severity"] == "Critical" else ("alert-warning" if inc["severity"] in ["High", "Medium"] else "alert-info")
        sev_col = sev_colors.get(inc["severity"], "#888")
        status_col = "#10b981" if inc["status"] == "Resolved" else ("#f59e0b" if inc["status"] == "Responded" else "#ef4444")

        st.markdown(f"""
        <div class="{alert_class}">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:8px;">
                <div>
                    <b style="color:#e2e8f0; font-size:0.95rem;">
                        #{inc['incident_id']} · {inc['incident_type'].replace('_', ' ').title()}
                    </b><br>
                    <span style="color:#8b949e; font-size:0.8rem;">
                         {inc['camera_name']} ·  {inc['area_name']} ·
                        {inc['persons_involved']} persons · {inc['confidence']*100:.0f}% confidence
                    </span>
                </div>
                <div style="text-align:right;">
                    <span style="color:{sev_col}; font-weight:700; font-size:0.82rem;">{inc['severity']}</span>
                    <br>
                    <span style="color:{status_col}; font-size:0.8rem; font-weight:600;">{inc['status']}</span>
                    <br>
                    <span style="color:#8b949e; font-size:0.75rem;">{inc['created_at'].strftime('%d %b %H:%M')}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# --- PAGE: SYSTEM ---
elif "System" in page:
    st.markdown("## System Configuration and Resource Status")

    col_sys1, col_sys2 = st.columns(2)

    with col_sys1:
        st.markdown("###  Resource Usage")
        cpu = metrics["cpu_usage"]
        gpu = metrics["gpu_usage"]
        st_gb = metrics["storage_used_gb"]
        st_total = metrics["storage_total_gb"]

        for label, val, total, color in [
            ("CPU Usage", cpu, 100, "#63b3ed"),
            ("GPU Usage", gpu, 100, "#a78bfa"),
            ("Storage", st_gb, st_total, "#34d399"),
        ]:
            st.markdown(f"**{label}:** {val:.1f}{'%' if total==100 else f' / {total} GB'}")
            st.progress(val / total, text=f"{val/total*100:.0f}%")
            st.markdown("")

        st.markdown("###  API Keys Status")
        api_status = {
            "Twilio (SMS/Calls)": bool(config.TWILIO_ACCOUNT_SID and config.TWILIO_ACCOUNT_SID != "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"),
            "Telegram Bot": bool(config.TELEGRAM_BOT_TOKEN),
            "Email SMTP": bool(config.SMTP_USER),
            "Mapbox": bool(config.MAPBOX_API_KEY),
        }
        for service, configured in api_status.items():
            icon = "" if configured else "❌"
            status_text = "Configured" if configured else "Not configured"
            status_color = "#34d399" if configured else "#6b7280"
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; padding:8px 0; border-bottom:1px solid #21262d;">
                <span style="color:#e2e8f0;">{service}</span>
                <span style="color:{status_color};">{icon} {status_text}</span>
            </div>
            """, unsafe_allow_html=True)

    with col_sys2:
        st.markdown("###  Alert Configuration")
        with st.form("alert_config"):
            st.slider("Violence Detection Threshold", 0.5, 0.99, 0.90)
            st.slider("Face Match Threshold", 0.5, 0.99, 0.85)
            st.number_input("Traffic Alert Threshold (vehicles/min)", 50, 300, 100)
            st.number_input("Loitering Alert Threshold (minutes)", 5, 60, 10)
            st.form_submit_button(" Save Configuration", width="stretch")

        st.markdown("###  Area Management")
        area_df = pd.DataFrame(AREAS, columns=["area_id", "name", "center_lat", "center_lon"])
        area_df.columns = ["ID", "Name", "Center Lat", "Center Lon"]
        st.dataframe(area_df, hide_index=True, width="stretch")


# ─── Auto-refresh ─────────────────────────────────────────────────────────────
if auto_refresh:
    time.sleep(0.5)
    # Use rerun wisely - only for live metrics
    # st.rerun()  # Uncomment for true live updates
