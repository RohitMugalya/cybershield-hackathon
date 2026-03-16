"""
CyberShield - Police Officer Portal
AI-Based Integrated Video Analytics System

Area-based police portal with:
- Login with area assignment
- Area-specific alert dashboard
- Vehicle search (plate + characteristics)
- Person/face search
- CCTV feeds
- Incident history
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import random
from datetime import datetime, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from database.simulated_data import (
    CAMERAS, AREAS, POLICE_OFFICERS, CITIZENS, VEHICLES,
    CRIMINAL_RECORDS, WATCHLIST,
    generate_incidents, generate_vehicle_detections,
    search_vehicle_by_plate, search_vehicles_by_characteristics,
    track_vehicle_journey, get_system_metrics,
)
import pydeck as pdk

# ─── Page Configuration ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="CyberShield - Police Portal",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;900&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    .stApp {
        background: linear-gradient(135deg, #0a0a12 0%, #0d1117 50%, #0f1923 100%);
    }
    
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d1117 0%, #161b22 100%);
        border-right: 1px solid #21262d;
    }
    
    #MainMenu, footer, header { visibility: hidden; }
    
    .police-card {
        background: linear-gradient(135deg, rgba(22,27,34,0.95) 0%, rgba(13,17,23,0.98) 100%);
        border: 1px solid rgba(59,130,246,0.2);
        border-radius: 14px;
        padding: 20px;
        margin: 8px 0;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
    }
    
    .alert-critical {
        background: linear-gradient(135deg, rgba(239,68,68,0.15) 0%, rgba(239,68,68,0.03) 100%);
        border: 1px solid rgba(239,68,68,0.5);
        border-left: 4px solid #ef4444;
        border-radius: 10px;
        padding: 16px 20px;
        margin: 8px 0;
        animation: pulse-critical 2.5s infinite;
    }
    
    .alert-warning {
        background: linear-gradient(135deg, rgba(245,158,11,0.15) 0%, rgba(245,158,11,0.03) 100%);
        border: 1px solid rgba(245,158,11,0.4);
        border-left: 4px solid #f59e0b;
        border-radius: 10px;
        padding: 16px 20px;
        margin: 8px 0;
    }
    
    .alert-info {
        background: linear-gradient(135deg, rgba(59,130,246,0.15) 0%, rgba(59,130,246,0.03) 100%);
        border: 1px solid rgba(59,130,246,0.4);
        border-left: 4px solid #3b82f6;
        border-radius: 10px;
        padding: 16px 20px;
        margin: 8px 0;
    }
    
    @keyframes pulse-critical {
        0%, 100% { border-color: rgba(239,68,68,0.5); box-shadow: none; }
        50% { border-color: rgba(239,68,68,1); box-shadow: 0 0 20px rgba(239,68,68,0.25); }
    }
    
    .login-container {
        max-width: 480px;
        margin: 60px auto;
        background: linear-gradient(135deg, rgba(22,27,34,0.98) 0%, rgba(13,17,23,0.99) 100%);
        border: 1px solid rgba(59,130,246,0.3);
        border-radius: 20px;
        padding: 40px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.6);
        position: relative;
        overflow: hidden;
    }
    
    .login-container::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 4px;
        background: linear-gradient(90deg, #1d4ed8, #7c3aed, #ec4899);
    }
    
    .vehicle-result {
        background: linear-gradient(135deg, rgba(22,27,34,0.95) 0%, rgba(13,17,23,0.98) 100%);
        border: 1px solid rgba(99,179,237,0.3);
        border-radius: 14px;
        padding: 22px;
        margin: 12px 0;
    }
    
    .watchlist-badge {
        background: linear-gradient(90deg, #450a0a, #7f1d1d);
        color: #fca5a5;
        padding: 3px 12px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 700;
        border: 1px solid rgba(239,68,68,0.5);
    }
    
    .officer-header {
        background: linear-gradient(135deg, rgba(29,78,216,0.15) 0%, rgba(124,58,237,0.1) 100%);
        border: 1px solid rgba(59,130,246,0.3);
        border-radius: 14px;
        padding: 18px 24px;
        margin-bottom: 20px;
        position: relative;
        overflow: hidden;
    }
    
    .officer-header::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        background: linear-gradient(90deg, #1d4ed8, #7c3aed);
    }
    
    ::-webkit-scrollbar { width: 5px; }
    ::-webkit-scrollbar-track { background: #0d1117; }
    ::-webkit-scrollbar-thumb { background: #21262d; border-radius: 3px; }
    
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(22,27,34,0.8);
        border-radius: 10px;
        padding: 4px;
    }
    
    .stTabs [data-baseweb="tab"] { border-radius: 7px; color: #8b949e; }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #1d4ed8, #7c3aed);
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)


# ─── Authentication Logic ──────────────────────────────────────────────────────
VALID_CREDENTIALS = {
    "12345": {"password": "officer@123", "officer_id": 1},
    "12346": {"password": "officer@123", "officer_id": 2},
    "12347": {"password": "officer@123", "officer_id": 3},
    "12348": {"password": "officer@123", "officer_id": 4},
    "12349": {"password": "officer@123", "officer_id": 5},
}

# Registered accounts (in-memory for demo)
if "registered_accounts" not in st.session_state:
    st.session_state.registered_accounts = {}


def login_page():
    st.markdown("""
    <div style="text-align:center; padding: 40px 0 20px 0;">
        <div style="font-size:3.5rem; margin-bottom:12px;"></div>
        <div style="font-size:1.6rem; font-weight:800; color:#e2e8f0;">
            CyberShield Police Portal
        </div>
        <div style="font-size:0.85rem; color:#8b949e; margin-top:6px;">
            Secure Officer Authentication
        </div>
    </div>
    """, unsafe_allow_html=True)

    _, col_main, _ = st.columns([1, 2, 1])
    with col_main:
        login_tab, register_tab = st.tabs(["Login", "Create Account"])

        # ── LOGIN TAB ──────────────────────────────────────────────────────────
        with login_tab:
            st.markdown('<div class="login-container">', unsafe_allow_html=True)
            st.markdown("###  Officer Login")
            st.markdown("<div style='color:#8b949e; font-size:0.82rem; margin-bottom:20px;'>Use Badge ID and password to access the portal</div>", unsafe_allow_html=True)

            badge_id = st.text_input("Badge ID", placeholder="e.g. 12345", key="login_badge")
            password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_pass")

            area_options = {a["name"]: a["area_id"] for a in AREAS}
            selected_area_name = st.selectbox(" Assigned Area", list(area_options.keys()))

            st.markdown("<br>", unsafe_allow_html=True)
            col_b1, col_b2 = st.columns([1, 1])
            with col_b2:
                login_btn = st.button(" Login", width="stretch", type="primary", key="btn_login")

            if login_btn:
                # Check demo credentials
                all_credentials = {**VALID_CREDENTIALS, **st.session_state.registered_accounts}
                if badge_id in all_credentials and password == all_credentials[badge_id]["password"]:
                    officer_id = all_credentials[badge_id].get("officer_id", 99)
                    officer = next((o for o in POLICE_OFFICERS if o["officer_id"] == officer_id), None)
                    if not officer:  # New registered account
                        officer = {
                            "officer_id": officer_id,
                            "badge": badge_id,
                            "name": all_credentials[badge_id].get("name", "Officer"),
                            "area_id": area_options[selected_area_name],
                            "phone": all_credentials[badge_id].get("phone", ""),
                            "email": all_credentials[badge_id].get("email", ""),
                            "role": all_credentials[badge_id].get("role", "Officer"),
                        }
                    st.session_state.logged_in = True
                    st.session_state.officer = officer
                    st.session_state.current_area_id = area_options[selected_area_name]
                    st.success(f" Welcome, {officer['name']}!")
                    st.rerun()
                else:
                    st.error("❌ Invalid Badge ID or Password. Try badge 12345 with password: officer@123")

            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown("""
            <div style="text-align:center; margin-top:20px; color:#6b7280; font-size:0.8rem;">
                Demo: Badge ID: <b style="color:#63b3ed;">12345</b> · Password: <b style="color:#63b3ed;">officer@123</b>
            </div>
            """, unsafe_allow_html=True)

        # ── CREATE ACCOUNT TAB ─────────────────────────────────────────────────
        with register_tab:
            st.markdown('<div class="login-container">', unsafe_allow_html=True)
            st.markdown("###  Create Officer Account")
            st.info("New accounts require approval by senior officer within 24 hours. Demo accounts are approved instantly.")

            col_r1, col_r2 = st.columns(2)
            with col_r1:
                reg_name = st.text_input(" Full Name*", placeholder="Ravi Kumar", key="reg_name")
                reg_badge = st.text_input(" Badge ID*", placeholder="e.g. 99001", key="reg_badge")
                reg_phone = st.text_input(" Phone Number*", placeholder="+91-XXXXXXXXXX", key="reg_phone")
                reg_rank = st.selectbox("️ Rank / Role", ["Officer", "Sub-Inspector", "Assistant Inspector", "Inspector", "DSP"], key="reg_rank")
            with col_r2:
                reg_email = st.text_input(" Email*", placeholder="ravi.kumar@police.gov.in", key="reg_email")
                reg_password = st.text_input(" Password*", type="password", placeholder="Min 8 characters", key="reg_password")
                reg_confirm = st.text_input(" Confirm Password*", type="password", key="reg_confirm")
                reg_area = st.selectbox(" Assigned Area*", [a["name"] for a in AREAS], key="reg_area")

            reg_id_upload = st.file_uploader("Police ID Card (JPG/PDF)", type=["jpg", "jpeg", "png", "pdf"], key="reg_id")
            reg_agree = st.checkbox("I agree to the CyberShield Terms of Use and Privacy Policy", key="reg_agree")

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button(" Create Account", width="stretch", type="primary", key="btn_register"):
                if not all([reg_name, reg_badge, reg_phone, reg_email, reg_password, reg_confirm]):
                    st.error("❌ Please fill in all required fields (*)")
                elif reg_password != reg_confirm:
                    st.error("❌ Passwords do not match")
                elif len(reg_password) < 8:
                    st.error("❌ Password must be at least 8 characters")
                elif not reg_agree:
                    st.error("❌ Please agree to the Terms of Use")
                elif reg_badge in VALID_CREDENTIALS or reg_badge in st.session_state.registered_accounts:
                    st.error("❌ Badge ID already registered")
                else:
                    area_id_reg = next((a["area_id"] for a in AREAS if a["name"] == reg_area), 1)
                    new_id = 100 + len(st.session_state.registered_accounts) + 1
                    st.session_state.registered_accounts[reg_badge] = {
                        "password": reg_password,
                        "officer_id": new_id,
                        "name": reg_name,
                        "phone": reg_phone,
                        "email": reg_email,
                        "role": reg_rank,
                        "area_id": area_id_reg,
                    }
                    st.success(f" Account created for **{reg_name}** (Badge #{reg_badge}). You can now login!")
                    st.balloons()

            st.markdown('</div>', unsafe_allow_html=True)


# ─── Session Init ──────────────────────────────────────────────────────────────
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.officer = None
    st.session_state.current_area_id = 1

if not st.session_state.logged_in:
    login_page()
    st.stop()


# ─── Main Dashboard (post-login) ──────────────────────────────────────────────
officer = st.session_state.officer
area_id = st.session_state.current_area_id
area = next((a for a in AREAS if a["area_id"] == area_id), AREAS[0])
area_cameras = [c for c in CAMERAS if c["area_id"] == area_id]
area_incidents = [i for i in generate_incidents(30) if i.get("area_id") == area_id]
metrics = get_system_metrics()

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style="text-align:center; padding: 16px 0;">
        <div style="font-size:2.5rem; margin-bottom:8px;"></div>
        <div style="font-size:1.1rem; font-weight:700; color:#e2e8f0;">
            {officer['name']}
        </div>
        <div style="font-size:0.78rem; color:#63b3ed; margin-top:2px;">
            Badge #{officer['badge']}
        </div>
        <div style="font-size:0.75rem; color:#8b949e; margin-top:2px;">
            {officer['role']} · {area['name']}
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    page = st.radio(
        "Navigation",
        ["Alert Dashboard", "Vehicle Search", "Track Vehicle", "Person Search", "Incident History", "Live Feeds", "Area Summary"],
        label_visibility="collapsed",
    )

    st.markdown("---")
    active_alerts = [i for i in area_incidents if i["status"] == "Active"]
    st.markdown(f"""
    <div style="font-size:0.82rem; color:#8b949e; line-height:2.2;">
         Area: <b style="color:#63b3ed;">{area['name']}</b><br>
         Active Alerts: <b style="color:{'#ef4444' if active_alerts else '#34d399'};">{len(active_alerts)}</b><br>
         Cameras: <b style="color:#a78bfa;">{len(area_cameras)}</b><br>
         Vehicles Today: <b style="color:#34d399;">{random.randint(200, 400)}</b>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    if st.button(" Logout", width="stretch"):
        st.session_state.logged_in = False
        st.session_state.officer = None
        st.rerun()


# ─── Officer Header ───────────────────────────────────────────────────────────
now = datetime.now()
st.markdown(f"""
<div class="officer-header">
    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
        <div>
            <div style="font-size:1.3rem; font-weight:700; color:#e2e8f0;">
                 Officer Dashboard — {area['name']}
            </div>
            <div style="font-size:0.82rem; color:#8b949e; margin-top:3px;">
                Officer: {officer['name']} (#{officer['badge']}) · {officer['role']}
            </div>
        </div>
        <div style="text-align:right; font-size:0.82rem; color:#8b949e;">
             {now.strftime('%d %b %Y, %H:%M IST')}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: ALERT DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
if " Alert Dashboard" in page:
    active_alerts_list = [i for i in area_incidents if i["status"] == "Active"]
    responded_alerts = [i for i in area_incidents if i["status"] == "Responded"]

    # Summary metrics
    c1, c2, c3, c4 = st.columns(4)
    total_v = random.randint(200, 400)
    anpr_v = random.randint(150, 300)
    people_v = random.randint(80, 200)
    incidents_v = len(area_incidents)

    for col, header, val, label, color in [
        (c1, "ACTIVE ALERTS", len(active_alerts_list), "Priority Dispatch", "#ef4444"),
        (c2, "VEHICLES TODAY", total_v, "Total Flow", "#63b3ed"),
        (c3, "PEOPLE COUNT", people_v, "Live Presence", "#a78bfa"),
        (c4, "TOTAL INCIDENTS", incidents_v, "Historical Data", "#fb923c"),
    ]:
        with col:
            st.markdown(f"""
            <div style="background:rgba(22,27,34,0.95); border:1px solid rgba(255,255,255,0.07);
                        border-radius:12px; padding:16px; text-align:center; position:relative; overflow:hidden;">
                <div style="position:absolute; top:0; left:0; right:0; height:2px;
                            background: linear-gradient(90deg, {color}, transparent);"></div>
                <div style="font-size:0.65rem; color:#8b949e; text-transform:uppercase; margin-bottom:8px; font-weight:600;">{header}</div>
                <div style="font-size:1.8rem; font-weight:700; color:{color}; line-height:1;">{val}</div>
                <div style="font-size:0.72rem; color:#8b949e; margin-top:3px; text-transform:uppercase;">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Active alerts
    if active_alerts_list:
            st.markdown(f"### Priority Alerts ({len(active_alerts_list)})")
            for inc in active_alerts_list[:5]:
                sev_colors = {"Critical": "#ef4444", "High": "#f97316", "Medium": "#f59e0b"}
                alert_class = "alert-critical" if inc["severity"] == "Critical" else "alert-warning"
                sev_col = sev_colors.get(inc["severity"], "#f59e0b")
                itype_label = inc['incident_type'].replace('_', ' ').upper()

            st.markdown(f"""
            <div class="{alert_class}">
                <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:8px;">
                    <div>
                        <div style="font-size:1rem; font-weight:700; color:#e2e8f0; margin-bottom:6px;">
                            {itype_label} DETECTED
                        </div>
                        <div style="font-size:0.82rem; color:#8b949e; line-height:2;">
                             Camera: <b style="color:#e2e8f0;">{inc['camera_name']}</b><br>
                             Location: <b style="color:#63b3ed;">{inc['lat']:.4f}°N, {inc['lon']:.4f}°E</b><br>
                             Time: <b>{inc['created_at'].strftime('%I:%M %p')} ({int((datetime.now() - inc['created_at']).seconds / 60)} min ago)</b><br>
                             Persons Involved: <b style="color:#a78bfa;">{inc['persons_involved']}</b>
                            ·  Confidence: <b style="color:{sev_col};">{inc['confidence']*100:.0f}%</b>
                        </div>
                    </div>
                    <div>
                        <span style="background:{sev_col}20; color:{sev_col}; padding:4px 14px; border-radius:20px;
                                     font-size:0.78rem; font-weight:700; border: 1px solid {sev_col}50;">
                            {inc['severity'].upper()}
                        </span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            col_b1, col_b2, col_b3 = st.columns(3)
            with col_b1:
                st.button(" View Live Feed", key=f"feed_{inc['incident_id']}", width="stretch")
            with col_b2:
                st.button(" Mark Responded", key=f"respond_{inc['incident_id']}", width="stretch")
            with col_b3:
                st.button(" Dispatch Unit", key=f"dispatch_{inc['incident_id']}", width="stretch")

    else:
        st.markdown("""
        <div class="alert-info">
            <div style="font-size:1rem; color:#e2e8f0; font-weight:600;"> No Active Alerts</div>
            <div style="color:#8b949e; font-size:0.82rem; margin-top:4px;">
                Your area is clear. All systems nominal.
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Recent resolved
    if responded_alerts:
        st.markdown(f"###  Responded Alerts ({len(responded_alerts)})")
        for inc in responded_alerts[:3]:
            st.markdown(f"""
            <div class="alert-info">
                <div style="display:flex; justify-content:space-between; flex-wrap:wrap; gap:8px;">
                    <div>
                        <b style="color:#e2e8f0;">{inc['incident_type'].replace('_', ' ').title()}</b>
                        <span style="color:#8b949e; font-size:0.8rem; margin-left:8px;">
                             {inc['camera_name']} · {inc['created_at'].strftime('%H:%M')}
                        </span>
                    </div>
                    <span style="color:#3b82f6; font-size:0.8rem; font-weight:600;">Responded</span>
                </div>
            </div>
            """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: VEHICLE SEARCH
# ═══════════════════════════════════════════════════════════════════════════════
elif "Vehicle Search" in page:
    st.markdown("### National Vehicle Intelligence Search")

    search_tab1, search_tab2 = st.tabs([" Search by License Plate", " Search by Characteristics"])

    with search_tab1:
        st.markdown("#### Search by License Plate Number")
        col_s1, col_s2 = st.columns([3, 1])
        with col_s1:
            plate_input = st.text_input("License Plate", placeholder="e.g. TN01AB1234",
                                         label_visibility="collapsed")
        with col_s2:
            search_plate_btn = st.button(" Search", width="stretch", type="primary", key="btn_search_plate")

        if search_plate_btn and plate_input:
            result = search_vehicle_by_plate(plate_input.strip())

            if result:
                vehicle = result["vehicle"]
                owner = result["owner"]
                criminal_records = result.get("criminal_records", [])
                recent_detections = result.get("recent_detections", [])

                # ── Vehicle + Owner Result Card ──────────────────────────────
                has_records = bool(criminal_records)
                st.markdown(f"""
                <div class="vehicle-result">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
                        <div style="font-size:1.3rem; font-weight:700; color:#63b3ed;">
                             {vehicle['license_plate']} &nbsp;
                            <span style="font-size:0.85rem; color:#8b949e; font-weight:400;">
                                {vehicle['make']} {vehicle['model']} ({vehicle['year']}) · {vehicle['color']} {vehicle['vehicle_type']}
                            </span>
                        </div>
                        {('<span class="watchlist-badge">⚠️ HAS RECORDS</span>' if has_records else '<span style="background:#064e3b; color:#34d399; padding:3px 12px; border-radius:20px; font-size:0.78rem; font-weight:600;"> Clear</span>')}
                    </div>

                    <div style="display:grid; grid-template-columns: 1fr 1fr 1fr; gap:20px; margin-bottom:16px;">
                        <div>
                            <div style="font-size:0.82rem; font-weight:600; color:#63b3ed; margin-bottom:8px; border-bottom:1px solid rgba(99,179,237,0.2); padding-bottom:4px;">
                                 OWNER DETAILS
                            </div>
                            <div style="font-size:0.8rem; color:#8b949e; line-height:2.3;">
                                Name: <b style="color:#e2e8f0;">{owner['name'] if owner else 'Unknown'}</b><br>
                                Age / Gender: <b style="color:#e2e8f0;">{owner.get('age','N/A')} · {owner.get('gender','N/A')}</b><br>
                                DOB: <b style="color:#e2e8f0;">{owner.get('dob','N/A')}</b><br>
                                Blood Group: <b style="color:#ef4444;">{owner.get('blood_group','N/A')}</b><br>
                                Aadhaar: <b style="color:#e2e8f0;">{owner.get('aadhaar','XXXX-XXXX-••••')}</b><br>
                                DL Number: <b style="color:#e2e8f0;">{owner.get('driving_license','N/A')}</b>
                            </div>
                        </div>
                        <div>
                            <div style="font-size:0.82rem; font-weight:600; color:#a78bfa; margin-bottom:8px; border-bottom:1px solid rgba(167,139,250,0.2); padding-bottom:4px;">
                                 CONTACT & ADDRESS
                            </div>
                            <div style="font-size:0.8rem; color:#8b949e; line-height:2.3;">
                                Phone: <b style="color:#e2e8f0;">{owner.get('phone','N/A')}</b><br>
                                Alt Phone: <b style="color:#e2e8f0;">{owner.get('alt_phone','N/A')}</b><br>
                                Email: <b style="color:#e2e8f0;">{owner.get('email','N/A')}</b><br>
                                Address: <b style="color:#e2e8f0; font-size:0.75rem;">{owner.get('address','N/A')}</b><br>
                                Emergency: <b style="color:#fb923c; font-size:0.75rem;">{owner.get('emergency_contact','N/A')}</b><br>
                                Occupation: <b style="color:#e2e8f0;">{owner.get('occupation','N/A')}</b>
                            </div>
                        </div>
                        <div>
                            <div style="font-size:0.82rem; font-weight:600; color:#34d399; margin-bottom:8px; border-bottom:1px solid rgba(52,211,153,0.2); padding-bottom:4px;">
                                 VEHICLE REGISTRY
                            </div>
                            <div style="font-size:0.8rem; color:#8b949e; line-height:2.3;">
                                Make / Model: <b style="color:#e2e8f0;">{vehicle['make']} {vehicle['model']}</b><br>
                                Year: <b style="color:#e2e8f0;">{vehicle['year']}</b><br>
                                Color / Type: <b style="color:#e2e8f0;">{vehicle['color']} {vehicle['vehicle_type']}</b><br>
                                Reg. Valid: <b style="color:#34d399;">{vehicle.get('registration_valid_till','N/A')}</b><br>
                                Insurance: <b style="color:#e2e8f0; font-size:0.75rem;">{vehicle.get('insurance_company','N/A')}</b><br>
                                Policy: <b style="color:#e2e8f0; font-size:0.75rem;">{vehicle.get('insurance_policy','N/A')}</b>
                            </div>
                        </div>
                    </div>

                    <div style="font-size:0.78rem; color:#555; border-top:1px solid rgba(255,255,255,0.05); padding-top:10px; line-height:2;">
                        Chassis: <b style="color:#6b7280;">{vehicle.get('chassis_number','N/A')}</b> &nbsp;|
                        Engine: <b style="color:#6b7280;">{vehicle.get('engine_number','N/A')}</b> &nbsp;|
                        Emission: <b style="color:#6b7280;">{vehicle.get('emission_cert','N/A')}</b>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Criminal Records
                if criminal_records:
                    st.markdown("#### ⚠️ Criminal Records")
                    for rec in criminal_records:
                        sev_color = {"High": "#ef4444", "Medium": "#f59e0b", "Low": "#10b981"}.get(rec["severity"], "#888")
                        status_color = {"Pending": "#f59e0b", "Active": "#ef4444", "Resolved": "#10b981"}.get(rec["status"], "#888")
                        st.markdown(f"""
                        <div style="background:rgba(239,68,68,0.08); border:1px solid rgba(239,68,68,0.3);
                                    border-radius:10px; padding:14px; margin:6px 0;">
                            <div style="display:flex; justify-content:space-between; flex-wrap:wrap; gap:6px;">
                                <div>
                                    <b style="color:{sev_color};">⚠️ {rec['case_type']}</b>
                                    <span style="color:#8b949e; font-size:0.8rem; margin-left:8px;">
                                        Case #{rec['case_number']}
                                    </span>
                                </div>
                                <div>
                                    <span style="color:{status_color}; font-size:0.82rem; font-weight:600;">{rec['status']}</span>
                                    <span style="color:#8b949e; font-size:0.78rem; margin-left:8px;">{rec['case_date']}</span>
                                </div>
                            </div>
                            <div style="color:#8b949e; font-size:0.8rem; margin-top:6px;">
                                {rec['description']}<br>
                                <span style="color:#555;">Court: {rec.get('court','N/A')}</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.success(" No criminal records found for this vehicle owner.")

                # Detection History
                if recent_detections:
                    st.markdown("####  Recent Camera Sightings")
                    det_df = pd.DataFrame(recent_detections)
                    if "detected_at" in det_df.columns:
                        det_df["detected_at"] = pd.to_datetime(det_df["detected_at"]).dt.strftime("%d %b %H:%M")
                    display_cols = [c for c in ["detected_at", "camera_name", "area_name", "speed_kmph", "confidence"] if c in det_df.columns]
                    if display_cols:
                        det_df_display = det_df[display_cols].copy()
                        det_df_display.columns = ["Time", "Camera", "Area", "Speed (km/h)", "Confidence"][:len(display_cols)]
                        st.dataframe(det_df_display, hide_index=True, width="stretch")
            else:
                st.warning(f"Vehicle not found: **{plate_input.upper()}**")
                st.caption("Try: TN01AB1234, TN02CD5678, TN03EF9012, TN04GH3456, TN05IJ7890")

    with search_tab2:
        st.markdown("#### Search by Vehicle Characteristics (Hidden Plate Scenario)")
        st.info(" Only shows vehicles with owners who have previous criminal records — Privacy Protection Enabled")

        col_c1, col_c2, col_c3, col_c4 = st.columns(4)
        with col_c1:
            v_type = st.selectbox("Vehicle Type", ["All", "Car", "SUV", "Bike", "Truck", "Auto", "Bus"])
        with col_c2:
            v_color = st.selectbox("Color", ["All", "White", "Black", "Silver", "Grey", "Red", "Blue", "Green"])
        with col_c3:
            time_range = st.selectbox("Time Range", ["Last 24 hours", "Last 12 hours", "Last 6 hours"])
        with col_c4:
            v_area = st.selectbox("Area", ["All Areas"] + [a["name"] for a in AREAS])

        search_char_btn = st.button(" Search", width="stretch", type="primary", key="btn_search_char")

        if search_char_btn:
            area_id_filter = None
            if v_area != "All Areas":
                area_id_filter = next((a["area_id"] for a in AREAS if a["name"] == v_area), None)

            time_hours = {"Last 24 hours": 24, "Last 12 hours": 12, "Last 6 hours": 6}[time_range]
            results = search_vehicles_by_characteristics(
                vehicle_type=v_type if v_type != "All" else None,
                color=v_color if v_color != "All" else None,
                area_id=area_id_filter,
                time_range_hours=time_hours,
            )

            if results:
                st.markdown(f"###  {len(results)} Potential Matches (Only Suspicious Owners Shown)")
                for idx, res in enumerate(results, 1):
                    vehicle = res["vehicle"]
                    criminal_records = res["criminal_records"]
                    last_seen = res.get("last_seen_camera", {})
                    last_time = res.get("last_seen_time", datetime.now())

                    with st.expander(f"Match {idx}: {vehicle['color']} {vehicle['vehicle_type']} ({vehicle['make']} {vehicle['model']}) — {len(criminal_records)} record(s)", expanded=True):
                        col_r1, col_r2 = st.columns(2)
                        with col_r1:
                            st.markdown(f"""
                            **Vehicle:** {vehicle['make']} {vehicle['model']} ({vehicle['year']})  
                            **Color:** {vehicle['color']} · **Type:** {vehicle['vehicle_type']}  
                            **Plate:** {vehicle['license_plate']}  
                            **Last Seen:** Camera {last_seen.get('name', 'Unknown')} · {last_time.strftime('%H:%M')}
                            """)
                        with col_r2:
                            st.markdown("**⚠️ Previous Cases:**")
                            for rec in criminal_records:
                                sev_color = {"High": "", "Medium": "", "Low": ""}.get(rec["severity"], "⚪")
                                st.markdown(f"• {sev_color} **{rec['case_type']}** ({rec['status']}) — {rec['case_date']}")

                        if st.button(f"️ View Owner Details", key=f"view_owner_{idx}", width="stretch"):
                            owner = res.get("owner", {})
                            if owner:
                                st.markdown(f"""
                                **Name:** {owner.get('name', 'N/A')}  
                                **Age:** {owner.get('age', 'N/A')}  
                                **Phone:** {owner.get('phone', 'N/A')}  
                                **Address:** {owner.get('address', 'N/A')}
                                """)
            else:
                st.info("No suspicious vehicles found matching your criteria.")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: TRACK VEHICLE IN CITY
# ═══════════════════════════════════════════════════════════════════════════════
elif "Track Vehicle" in page:
    st.markdown("### Path Visualization - Tracking Mode")
    st.caption("Enter a license plate to track its path across all city cameras on the real map")

    col_t1, col_t2, col_t3 = st.columns([3, 1, 1])
    with col_t1:
        track_plate = st.text_input("License Plate Number", placeholder="e.g. TN01AB1234",
                                    label_visibility="collapsed", key="track_plate_input")
    with col_t2:
        hours_back = st.selectbox("Time Range", [24, 12, 6, 48], format_func=lambda x: f"Last {x}h",
                                  key="track_hours")
    with col_t3:
        track_btn = st.button(" Track", width="stretch", type="primary", key="btn_track")

    if track_btn and track_plate:
        vehicle_info = search_vehicle_by_plate(track_plate.strip())
        journey = track_vehicle_journey(track_plate.strip(), hours=hours_back)

        if journey:
            if vehicle_info:
                v = vehicle_info["vehicle"]
                o = vehicle_info["owner"]
                has_rec = bool(vehicle_info.get("criminal_records"))
                rec_badge = '<span style="background:rgba(239,68,68,0.2); color:#ef4444; padding:3px 12px; border-radius:20px; font-size:0.78rem; font-weight:700;">⚠️ HAS RECORDS</span>' if has_rec else '<span style="background:#064e3b; color:#34d399; padding:3px 10px; border-radius:20px; font-size:0.78rem;"> Clear</span>'
                st.markdown(f"""
                <div style="background:rgba(22,27,34,0.95); border:1px solid {'rgba(239,68,68,0.4)' if has_rec else 'rgba(52,211,153,0.3)'};
                            border-radius:12px; padding:14px 20px; margin-bottom:16px;
                            display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
                    <div>
                        <b style="color:#63b3ed; font-size:1.1rem;">{track_plate.upper()}</b>
                        &nbsp; {v['make']} {v['model']} · <b style="color:#e2e8f0;">{v['color']} {v['vehicle_type']}</b>
                        &nbsp;|&nbsp; Owner: <b style="color:#e2e8f0;">{o['name'] if o else 'N/A'}</b>
                        &nbsp;|&nbsp; <span style="color:#8b949e;">{o.get('occupation','') if o else ''}</span>
                    </div>
                    <div>{rec_badge}</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown(f"####  {len(journey)} Camera Sightings — Last {hours_back}h")

            journey_df = pd.DataFrame(journey)
            n = len(journey)
            colors = []
            for i in range(n):
                r = int(239 * i / max(n - 1, 1))
                g = int(99 + (100 * (1 - i / max(n - 1, 1))))
                b = int(237 * (1 - i / max(n - 1, 1)))
                colors.append([r, g, b, 220])
            journey_df["color"] = colors
            journey_df["radius"] = [60 + i * 10 for i in range(n)]
            journey_df["label"] = journey_df.apply(lambda r: f"#{r['seq']} {r['camera_name']}", axis=1)

            arc_data = []
            for i in range(len(journey) - 1):
                arc_data.append({
                    "src_lon": journey[i]["lon"], "src_lat": journey[i]["lat"],
                    "dst_lon": journey[i + 1]["lon"], "dst_lat": journey[i + 1]["lat"],
                })
            arc_df = pd.DataFrame(arc_data) if arc_data else pd.DataFrame()

            scatter_layer = pdk.Layer(
                "ScatterplotLayer", data=journey_df,
                get_position=["lon", "lat"], get_fill_color="color",
                get_radius="radius", pickable=True, auto_highlight=True,
                radiusMinPixels=10, radiusMaxPixels=30,
                stroked=True, get_line_color=[255, 255, 255, 150], line_width_min_pixels=2,
            )
            text_layer = pdk.Layer(
                "TextLayer", data=journey_df,
                get_position=["lon", "lat"], get_text="label",
                get_size=13, get_color=[220, 230, 255, 210],
                get_alignment_baseline="'bottom'", pickable=True,
            )
            layers = [scatter_layer, text_layer]
            if not arc_df.empty:
                arc_layer = pdk.Layer(
                    "ArcLayer", data=arc_df,
                    get_source_position=["src_lon", "src_lat"],
                    get_target_position=["dst_lon", "dst_lat"],
                    get_source_color=[99, 179, 237, 180],
                    get_target_color=[239, 68, 68, 200],
                    width_scale=0.5, get_width=3, tilt=15, pickable=True,
                )
                layers.insert(0, arc_layer)

            view_state = pdk.ViewState(
                latitude=journey_df["lat"].mean(), longitude=journey_df["lon"].mean(),
                zoom=12, pitch=35, bearing=5,
            )
            deck = pdk.Deck(
                layers=layers,
                initial_view_state=view_state,
                map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
                tooltip={
                    "html": "<b>#{seq} {camera_name}</b><br>Area: {area_name}<br>Speed: {speed_kmph} km/h · Dir: {direction}",
                    "style": {"backgroundColor": "#0d1117", "color": "#63b3ed",
                              "borderRadius": "8px", "fontSize": "13px", "padding": "10px"},
                },
            )
            st.pydeck_chart(deck)

            st.markdown("""
            <div style="display:flex; gap:16px; padding:10px 14px; background:rgba(22,27,34,0.8);
                        border-radius:10px; margin-top:4px; font-size:0.8rem; flex-wrap:wrap;">
                <span> First Sighting</span><span>→ Path Direction</span>
                <span> Latest Sighting</span>
                <span style="color:#8b949e;">Dots grow larger chronologically</span>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("####  Sighting Log")
            log_rows = [{
                "Seq": f"#{s['seq']}", "Time": s["seen_at"].strftime("%d %b %H:%M:%S"),
                "Camera": s["camera_name"], "Area": s["area_name"],
                "Speed": f"{s['speed_kmph']} km/h", "Direction": s["direction"],
                "Confidence": f"{s['confidence']*100:.0f}%",
            } for s in journey]
            st.dataframe(pd.DataFrame(log_rows), hide_index=True, width="stretch")
        else:
            st.warning(f"No sightings found for **{track_plate.upper()}** in the last {hours_back} hours.")
            st.caption("Try: TN01AB1234, TN02CD5678, TN03EF9012")
    else:
        st.markdown("""
        <div style="background:rgba(22,27,34,0.8); border:2px dashed rgba(99,179,237,0.3);
                    border-radius:14px; padding:40px; text-align:center; margin-top:10px;">
            <div style="font-size:3rem; margin-bottom:12px;"></div>
            <div style="font-size:1rem; color:#8b949e;">
                Enter a license plate number to track the vehicle's<br>
                journey across city cameras on the real map<br>
                <span style="font-size:0.8rem; color:#555; margin-top:8px; display:block;">
                    Shows camera sightings with path overlay on Chennai OpenStreetMap
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: PERSON SEARCH
# ═══════════════════════════════════════════════════════════════════════════════
elif "Person Search" in page:
    st.markdown("###  Person Search — Facial Recognition")
    st.warning(" Privacy Notice: Facial recognition uses homomorphic encryption. Non-watchlist faces are automatically blurred. All searches are logged for GDPR compliance.")

    tab_face1, tab_face2 = st.tabs([" Upload Photo Search", " Watchlist Management"])

    with tab_face1:
        uploaded_file = st.file_uploader("Upload Photo for Facial Recognition Search", type=["jpg", "jpeg", "png"])

        if uploaded_file:
            col_img, col_result = st.columns(2)
            with col_img:
                st.image(uploaded_file, caption="Uploaded Image", width=350)

            with col_result:
                with st.spinner(" Running privacy-preserving facial recognition..."):
                    import time as time_module
                    time_module.sleep(1.5)

                # Simulate result (30% chance of match)
                if random.random() < 0.30:
                    match = random.choice(WATCHLIST)
                    st.markdown(f"""
                    <div style="background:rgba(239,68,68,0.15); border:2px solid #ef4444; border-radius:14px; padding:20px;">
                        <div style="font-size:1.1rem; font-weight:700; color:#ef4444; margin-bottom:12px;">
                             WATCHLIST MATCH FOUND
                        </div>
                        <div style="font-size:0.85rem; color:#8b949e; line-height:2.5;">
                            Name: <b style="color:#e2e8f0;">{match['name']}</b><br>
                            Alias: <b style="color:#e2e8f0;">{match.get('alias', 'N/A')}</b><br>
                            Case Type: <b style="color:#ef4444;">{match['case_type']}</b><br>
                            Severity: <b style="color:#f97316;">{match['severity']}</b><br>
                            Court Order: <b style="color:#e2e8f0;">{match['court_order_number']}</b><br>
                            Match Confidence: <b style="color:#34d399;">{random.randint(88, 98)}%</b>
                        </div>
                        <div style="margin-top:12px; padding:10px; background:rgba(0,0,0,0.3); border-radius:8px;
                                    font-size:0.78rem; color:#8b949e;">
                             This access has been logged per GDPR Article 25 requirements.
                            Access logged at {datetime.now().strftime('%H:%M:%S')}.
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    st.button(" Alert Senior Officers", type="primary", width="stretch")
                else:
                    st.markdown("""
                    <div style="background:rgba(16,185,129,0.1); border:1px solid rgba(16,185,129,0.4);
                                border-radius:14px; padding:20px;">
                        <div style="font-size:1rem; font-weight:600; color:#34d399; margin-bottom:8px;">
                             No Watchlist Match
                        </div>
                        <div style="font-size:0.82rem; color:#8b949e;">
                            This person is not in the watchlist database.<br>
                            Face has been automatically blurred in system records.<br><br>
                             Search logged for audit compliance.
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background:rgba(22,27,34,0.8); border:2px dashed rgba(99,179,237,0.3); border-radius:14px;
                        padding:40px; text-align:center; margin-top:10px;">
                <div style="font-size:3rem; margin-bottom:12px;"></div>
                <div style="font-size:1rem; color:#8b949e;">
                    Upload a photo to run facial recognition<br>
                    <span style="font-size:0.8rem; color:#555; margin-top:8px; display:block;">
                        Supported: JPG, JPEG, PNG · Max 10MB
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with tab_face2:
        st.markdown("####  Active Watchlist Entries")
        st.caption("Only court-order mandated entries. All entries have automatic expiry.")

        for person in WATCHLIST:
            sev_color = "#ef4444" if person["severity"] == "High" else "#f59e0b"
            expires = person.get("valid_until", "N/A")

            st.markdown(f"""
            <div class="police-card">
                <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:10px;">
                    <div>
                        <div style="font-size:0.95rem; font-weight:700; color:#e2e8f0;">
                             {person['name']}
                            {f"<span style='color:#8b949e; font-size:0.82rem;'> · Alias: {person.get('alias', 'N/A')}</span>" if person.get('alias') else ''}
                        </div>
                        <div style="font-size:0.8rem; color:#8b949e; line-height:2.2; margin-top:6px;">
                            Case: <b style="color:{sev_color};">{person['case_type']}</b>
                            · Severity: <b style="color:{sev_color};">{person['severity']}</b><br>
                            Court Order: <b style="color:#63b3ed;">{person['court_order_number']}</b>
                            · Court: {person.get('issuing_court', 'N/A')}<br>
                            Valid Until: <b style="color:#a78bfa;">{expires}</b>
                            · Status: <b style="color:#34d399;">{person['status']}</b>
                        </div>
                    </div>
                    <div>
                        <span style="background:rgba(239,68,68,0.15); color:#ef4444; padding:4px 14px;
                                     border-radius:20px; font-size:0.78rem; font-weight:700;
                                     border:1px solid rgba(239,68,68,0.4);">
                             ACTIVE
                        </span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### ➕ Add New Watchlist Entry (Court-Order Required)")
        with st.form("add_watchlist"):
            col_w1, col_w2 = st.columns(2)
            with col_w1:
                court_order = st.text_input("Court Order Number*", placeholder="HCO/2024/XXXX")
                issuing_court = st.text_input("Issuing Court*", placeholder="Madras High Court")
                order_date = st.date_input("Order Date")
                person_name = st.text_input("Person Name*")
                alias = st.text_input("Alias/Nickname")
            with col_w2:
                case_type = st.selectbox("Case Type", ["Murder", "Drug Trafficking", "Robbery", "Terrorism", "Kidnapping", "Human Trafficking"])
                case_number = st.text_input("Case Number", placeholder="Case/2024/XXXX")
                severity = st.selectbox("Severity", ["High", "Critical", "Medium"])
                valid_from = st.date_input("Valid From")
                valid_until = st.date_input("Valid Until")
            photo_upload = st.file_uploader("Photos (Min 3 required)", accept_multiple_files=True, type=["jpg", "png"])
            submitted = st.form_submit_button(" Add to Watchlist (Encrypted)", width="stretch")
            if submitted:
                if court_order and person_name and len(photo_upload or []) >= 1:
                    st.success(f" '{person_name}' added to watchlist. Face embeddings encrypted and stored.")
                    st.info(" Homomorphic encryption applied. No raw facial data stored.")
                else:
                    st.error("Please fill in all required fields (*).")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: INCIDENT HISTORY
# ═══════════════════════════════════════════════════════════════════════════════
elif " Incident History" in page:
    st.markdown(f"###  Incident History — {area['name']}")

    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        date_filter = st.selectbox("Time Range", ["Last 24 hours", "Last 7 days", "Last 30 days"])
    with col_f2:
        type_filter = st.selectbox("Type", ["All", "violence", "traffic", "face_match", "loitering", "speeding"])
    with col_f3:
        status_filter = st.selectbox("Status", ["All", "Active", "Responded", "Resolved"])

    all_incidents = generate_incidents(25)
    area_incidents_all = [i for i in all_incidents if i.get("area_id") == area_id]

    filtered = area_incidents_all
    if type_filter != "All":
        filtered = [i for i in filtered if i["incident_type"] == type_filter]
    if status_filter != "All":
        filtered = [i for i in filtered if i["status"] == status_filter]

    st.markdown(f"**{len(filtered)} incidents in your area**")

    for inc in filtered:
        sev_colors = {"Critical": "#ef4444", "High": "#f97316", "Medium": "#f59e0b", "Low": "#10b981"}
        status_colors = {"Active": "#ef4444", "Responded": "#f59e0b", "Resolved": "#10b981"}
        sev_col = sev_colors.get(inc["severity"], "#888")
        status_col = status_colors.get(inc["status"], "#888")

        with st.expander(f"#{inc['incident_id']} · {inc['incident_type'].replace('_', ' ').title()} · {inc['created_at'].strftime('%d %b %H:%M')}", expanded=False):
            col_i1, col_i2 = st.columns(2)
            with col_i1:
                st.markdown(f"""
                **Type:** {inc['incident_type'].replace('_', ' ').title()}  
                **Camera:** {inc['camera_name']}  
                **Location:** {inc['lat']:.4f}°N, {inc['lon']:.4f}°E  
                **Persons:** {inc['persons_involved']}  
                **Confidence:** {inc['confidence']*100:.0f}%
                """)
            with col_i2:
                st.markdown(f"""
                **Severity:** <span style="color:{sev_col}">{inc['severity']}</span>  
                **Status:** <span style="color:{status_col}">{inc['status']}</span>  
                **Time:** {inc['created_at'].strftime('%d %b %Y, %H:%M')}  
                **Description:** {inc['description']}  
                """, unsafe_allow_html=True)

            col_ib1, col_ib2 = st.columns(2)
            with col_ib1:
                if inc["status"] != "Resolved":
                    st.button(" Mark Resolved", key=f"hist_resolve_{inc['incident_id']}", width="stretch")
            with col_ib2:
                st.button(" Generate Report", key=f"hist_report_{inc['incident_id']}", width="stretch")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: LIVE FEEDS
# ═══════════════════════════════════════════════════════════════════════════════
elif " Live Feeds" in page:
    st.markdown(f"###  Live CCTV Feeds — {area['name']}")
    st.caption(f"Showing {len(area_cameras)} cameras assigned to your area")

    if not area_cameras:
        st.info("No cameras assigned to this area.")
    else:
        cols_per_row = 2
        for i in range(0, len(area_cameras), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, cam in enumerate(area_cameras[i:i + cols_per_row]):
                with cols[j]:
                    status_icon = "" if cam["status"] == "operational" else ("" if cam["status"] == "high_alert" else "")
                    v_count = random.randint(5, 40) if cam["status"] != "offline" else 0
                    p_count = random.randint(1, 12) if cam["status"] != "offline" else 0

                    st.markdown(f"""
                    <div class="police-card">
                        <div style="display:flex; justify-content:space-between; margin-bottom:10px;">
                            <b style="color:#e2e8f0;">{status_icon} {cam['name']}</b>
                            <span style="color:#63b3ed; font-size:0.8rem;">{cam['signal']}</span>
                        </div>
                        <div style="background:#0d0d1a; border:1px solid rgba(99,179,237,0.2); border-radius:10px;
                                    height:160px; display:flex; align-items:center; justify-content:center;
                                    position:relative; overflow:hidden;">
                            {'<div style="position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,transparent,#00d4ff,transparent);animation:none;"></div>' if cam['status']!='offline' else ''}
                            <div style="text-align:center; color:#8b949e;">
                                <div style="font-size:2.5rem;">{'' if cam['status']!='offline' else ''}</div>
                                <div style="font-size:0.78rem; margin-top:6px;
                                            color:{'#34d399' if cam['status']=='operational' else ('#f97316' if cam['status']=='high_alert' else '#ef4444')};">
                                    {' LIVE' if cam['status']!='offline' else '⚫ OFFLINE'}
                                </div>
                            </div>
                        </div>
                        <div style="font-size:0.78rem; color:#8b949e; margin-top:8px; line-height:1.8;">
                             {v_count} vehicles ·  {p_count} people
                        </div>
                    </div>
                    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: AREA SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════
elif " Area Summary" in page:
    st.markdown(f"###  Today's Summary — {area['name']}")

    total_v = random.randint(200, 500)
    anpr_v = int(total_v * 0.75)
    people_v = random.randint(80, 300)
    incidents_today = len(area_incidents)
    resolved_today = sum(1 for i in area_incidents if i["status"] == "Resolved")
    active_today = sum(1 for i in area_incidents if i["status"] == "Active")

    cols = st.columns(3)
    summary_data = [
        ("", total_v, "Total Vehicles", "#63b3ed"),
        ("", anpr_v, "ANPR Captures", "#a78bfa"),
        ("", people_v, "People Counted", "#34d399"),
        ("", incidents_today, "Total Incidents", "#fb923c"),
        ("", resolved_today, "Incidents Resolved", "#10b981"),
        ("", active_today, "Active Incidents", "#ef4444"),
    ]
    cols = st.columns(3)
    for i, (icon, val, label, color) in enumerate(summary_data):
        with cols[i % 3]:
            st.markdown(f"""
            <div style="background:rgba(22,27,34,0.95); border:1px solid rgba(255,255,255,0.07);
                        border-radius:12px; padding:16px; text-align:center; margin:6px 0;
                        position:relative; overflow:hidden;">
                <div style="position:absolute; top:0; left:0; right:0; height:2px;
                            background:linear-gradient(90deg,{color},transparent);"></div>
                <div style="font-size:1.8rem;">{icon}</div>
                <div style="font-size:1.8rem; font-weight:700; color:{color};">{val}</div>
                <div style="font-size:0.72rem; color:#8b949e; text-transform:uppercase;">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Incident timeline for this area
    if area_incidents:
        st.markdown("####  Incident Timeline (Last 24h)")
        # Group by hour
        hour_counts = {}
        for inc in area_incidents:
            h = inc["created_at"].hour
            hour_counts[h] = hour_counts.get(h, 0) + 1

        hours = list(range(24))
        counts = [hour_counts.get(h, 0) for h in hours]
        fig_tl = go.Figure(go.Bar(
            x=[f"{h:02d}:00" for h in hours],
            y=counts,
            marker_color=["#ef4444" if c > 2 else "#63b3ed" for c in counts],
        ))
        fig_tl.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#8b949e", height=220,
            xaxis=dict(gridcolor="#21262d", tickfont_size=9),
            yaxis=dict(gridcolor="#21262d"),
            margin=dict(t=10, b=0, l=0, r=0),
            showlegend=False,
        )
        st.plotly_chart(fig_tl, width="stretch")

    # Camera status table for area
    st.markdown("####  Area Camera Status")
    cam_df = pd.DataFrame(area_cameras)[["camera_id", "name", "status", "signal"]]
    cam_df.columns = ["ID", "Name", "Status", "Signal"]
    st.dataframe(cam_df, hide_index=True, width="stretch")
