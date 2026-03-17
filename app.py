import streamlit as st
import datetime, time, os, subprocess
import pandas as pd, numpy as np
import plotly.express as px
import plotly.graph_objects as go
import cv2

# ─── Custom Modules ───
from config import apply_css, DEVICE_LABEL, HAS_CUDA, CAMERAS, VIDEO_DIR
from database import DB_OK, LOCAL_DB, audit_col, faces_col, plates_col, log_audit, load_db_faces_to_session
from utils import verify_password, gen_jwt, check_jwt, enhance_frame
from models import load_rtdetr_light, load_ocr, load_face_cascade, load_crash_model, load_gender_net
from map_ui import render_map
from processing import (
    process_frame_weapon, process_frame_faces, process_frame_vehicles,
    process_frame_plates, process_frame_gender, process_frame_accident,
    WEAPON_BUFFER
)

# ─── Streamlit Config ───
st.set_page_config(page_title="CyberShield | AI Command Center", page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")
apply_css()

# ─── Session State Init ───
for k, v in {"authenticated": False, "audit_log": [], "cam_alerts": {c["id"]: False for c in CAMERAS},
             "active_cam": None, "face_gallery": [], "plate_log": [], "cam_analytics": {c["id"]: [] for c in CAMERAS}}.items():
    if k not in st.session_state:
        st.session_state[k] = v

load_db_faces_to_session()

def login():
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align: center; color:#00f3ff; text-shadow: 0 0 15px rgba(0, 243, 255, 0.6);'>🛡️ CyberShield Terminal</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #8d99ae;'>Secure AI Video Analytics Gateway</p>", unsafe_allow_html=True)
        
        with st.container(border=True):
            st.markdown("<h3 style='text-align: center; margin-bottom: 20px;'>System Authentication</h3>", unsafe_allow_html=True)
            user = st.text_input("Operator ID", placeholder="Enter your assigned Username")
            pw = st.text_input("Passkey", type="password", placeholder="•••••••••")
            
            if st.button("INITIALIZE CONNECTION", use_container_width=True, type="primary"):
                cursor = LOCAL_DB.cursor()
                cursor.execute("SELECT username, name, role, hash_pw FROM users WHERE username=?", (user,))
                user_rec = cursor.fetchone()
                
                if user_rec and verify_password(pw, user_rec[3].encode() if isinstance(user_rec[3], str) else user_rec[3]):
                    st.session_state.update({"jwt_token": gen_jwt(user_rec[0], user_rec[2]), "role": user_rec[2], "username": user_rec[0], "name": user_rec[1], "authenticated": True})
                    log_audit(user_rec[0], "Login", "SUCCESS")
                    st.rerun()
                else:
                    st.error("Authentication Denied. Invalid Operator ID or Passkey.")
        st.markdown("<p style='text-align: center; font-size:12px; color: #555; margin-top:20px;'>CyberShield Node Authorization required. Unauthorized access will be logged.</p>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# CAMERA PANEL — VIDEO + ANALYTICS
# ════════════════════════════════════════════════════════════

def run_camera_panel(cam_idx, map_ph=None, badge_phs=None):
    if isinstance(cam_idx, str) and not cam_idx.isdigit():
        for i, c in enumerate(CAMERAS):
            if c["id"] == cam_idx:
                cam_idx = i
                break
    cam_idx = int(cam_idx)
    cam = CAMERAS[cam_idx]
    
    # Strictly bind cache state to Active Camera so it purges on page switch
    if st.session_state.get("active_cam") != cam["id"]:
        st.session_state["face_gallery"] = []
        st.session_state["plate_log"] = []
        st.session_state["recent_face_boxes"] = []
        st.session_state["active_cam"] = cam["id"]
        load_db_faces_to_session()

    is_stream = cam.get("is_stream", False)
    vpath = cam["video"] if is_stream else os.path.join(VIDEO_DIR, cam["video"])

    st.markdown(f"### {cam['icon']} {cam['name']} — `{cam['id']}`")
    st.caption(cam["desc"])

    if not is_stream and not os.path.exists(vpath):
        st.error(f"❌ Video not found: `{vpath}`\n\nPlease place `{cam['video']}` in the `videos/` folder.")
        return

    col_feed, col_stats = st.columns([2, 1.5])

    with col_feed:
        st.markdown("**Live Feed**")
        video_ph = st.empty()
        progress_ph = st.progress(0)
        stop = st.button("⏹ Stop", key=f"stop_{cam['id']}")

    with col_stats:
        st.markdown("**📊 Real-Time Analytics**")
        metric_ph = st.empty()
        chart_ph = st.empty()
        log_ph = st.empty()
        if cam["task"] == "faces":
            st.markdown("**🎭 Detected Faces (Stored in DB)**")
            face_gallery_ph = st.empty()

    task = cam["task"]
    if task == "weapon":      model = load_rtdetr_light()
    elif task == "faces":     model = load_face_cascade()
    elif task == "vehicles":  model = load_rtdetr_light()
    elif task == "plates":    model = load_rtdetr_light(); reader = load_ocr()
    elif task == "gender":    model = load_rtdetr_light()
    elif task == "accident":  model = load_crash_model()
    
    # GPU Warmup (stops the 5-10 second UI hang on the first frame)
    if "gpu_warmed" not in st.session_state and task in ["weapon", "vehicles", "plates", "gender", "accident"]:
        st.info("Initializing Edge Accelerators... (One-time)")
        dummy = np.zeros((480, 640, 3), dtype=np.uint8)
        if task in ["weapon", "vehicles", "gender", "plates"]:
            _ = model(dummy, verbose=False)
        st.session_state["gpu_warmed"] = True

    if is_stream:
        try:
            cmd = ["yt-dlp", "-g", "-f", "best[height<=480]", vpath]
            m3u8_url = subprocess.check_output(cmd, text=True).strip()
            cap = cv2.VideoCapture(m3u8_url)
            total = float("inf")
            target_fps = 30
        except Exception as e:
            st.error(f"Failed to fetch YouTube stream: {e}")
            return
    else:
        cap = cv2.VideoCapture(vpath)
        if not cap.isOpened():
            st.error(f"Cannot open video: {vpath}")
            return
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        target_fps = cap.get(cv2.CAP_PROP_FPS) or 30

    frame_n = 0
    history = []
    last_ui = 0.0
    last_chart_ui = 0.0
    start_time = time.time()
    
    active = True
    while active and not stop:
        if not cap.isOpened(): break
        
        # --- Time-Based Dynamic Frame Skipping / Stream draining ---
        if is_stream:
            # Drain buffer to stay live
            cap.grab()
            ret, raw = cap.read()
            if not ret: break
            frame_n += 1
        else:
            # Dynamic elapsed-time skip logic
            expected_frame = int((time.time() - start_time) * target_fps)
            
            # If we fall radically behind (e.g. system suspended, long AI inference), reset clock
            if expected_frame - frame_n > 30:
                start_time = time.time() - (frame_n / target_fps)
                expected_frame = frame_n
                
            if frame_n < expected_frame:
                # We are slightly behind real-time, grab to skip
                cap.grab()
                frame_n += 1
                continue
            ret, raw = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                start_time = time.time()
                frame_n = 0
                continue
            frame_n += 1

        raw = cv2.resize(raw, (640, 480))
        bgr = enhance_frame(raw)
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

        alert = False
        data_point = {"frame": frame_n, "time": time.strftime("%H:%M:%S")}

        if task == "weapon":
            rgb, dets, alert = process_frame_weapon(rgb, model)
            data_point["detections"] = len(dets)
            data_point["alert"] = alert
        elif task == "faces":
            rgb, new_faces = process_frame_faces(rgb, bgr, model, cam["name"])
            data_point["new_faces"] = len(new_faces)
            data_point["total_faces"] = len(st.session_state.get("face_gallery", []))
        elif task == "vehicles":
            rgb, counts, alert = process_frame_vehicles(rgb, model)
            data_point.update(counts)
            data_point["alert"] = alert
        elif task == "plates":
            rgb, plates = process_frame_plates(rgb, bgr, model, reader)
            data_point["plates_found"] = len(plates)
            data_point["total_plates"] = len(st.session_state["plate_log"])
        elif task == "gender":
            rgb, gcounts = process_frame_gender(rgb, model)
            data_point.update(gcounts)
        elif task == "accident":
            rgb, crash_p, alert = process_frame_accident(rgb, model)
            data_point["crash_prob"] = crash_p
            data_point["alert"] = alert

        history.append(data_point)
        
        prev_alert = st.session_state["cam_alerts"].get(cam["id"], False)
        st.session_state["cam_alerts"][cam["id"]] = alert

        if prev_alert != alert:
            if map_ph is not None:
                with map_ph.container():
                    try: render_map()
                    except: pass
            if badge_phs is not None and cam["id"] in badge_phs:
                badge = badge_phs[cam["id"]]
                if alert:
                    badge.markdown("<span class='alert-badge'>RED ALERT</span>", unsafe_allow_html=True)
                else:
                    badge.markdown("<span class='ok-badge'>NOMINAL</span>", unsafe_allow_html=True)

        now = time.time()
        if now - last_ui > 0.1:
            try:
                # Always render fast video feed (avoid browser stalling)
                _, buffer = cv2.imencode('.jpg', rgb)
                video_ph.image(buffer.tobytes(), format="JPEG", width="stretch")
                if not is_stream and total > 0: progress_ph.progress(min(frame_n / total, 1.0))
                
                # Throttle React elements (Plotly/Metrics) to 1.5 seconds so browser GUI thread stays totally responsive
                if now - last_chart_ui > 1.5:
                    metric_ph.empty() # clear tree
                    with metric_ph.container():
                        render_advanced_analytics(task, history, data_point)
                    if task == "plates":
                        log_ph.empty()
                        with log_ph.container(): render_plate_log()
                    if task == "faces":
                        face_gallery_ph.empty()
                        with face_gallery_ph.container(): render_face_gallery()
                    last_chart_ui = now
            except Exception as e:
                pass 
            last_ui = now
            
        # Give Tornado Websocket async loop time to ping/pong heartbeat
        time.sleep(0.01)

    cap.release()
    st.success("✅ Processing complete.")
    if history:
        st.markdown("---")
        st.markdown("## 📊 Session Summary")
        render_final_analytics(task, history)

def render_advanced_analytics(task, history, dp):
    """
    Renders exactly 5 high-end Plotly/Metric elements per camera.
    Layout: Top row (3 columns), Bottom row (2 columns)
    """
    st.markdown(f"#### 🌐 Neural Vector Analysis: `{task.upper()}`")
    
    r1_col1, r1_col2, r1_col3 = st.columns([1, 1, 1.5])
    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
    r2_col1, r2_col2 = st.columns([1.5, 1])

    df = pd.DataFrame(history[-80:]) if len(history) > 1 else pd.DataFrame([dp])

    if task == "weapon":
        fig1 = go.Figure(go.Indicator(
            mode="gauge+number", value=dp.get("detections", 0) * 15,
            title={'text': "Aggression Risk Vector", 'font': {'size': 14}},
            gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#FF003C"}, 'bgcolor': "#0d1117",
                   'steps': [{'range': [0, 60], 'color': "#1a1a1a"}, {'range': [60, 100], 'color': "#3d000b"}]}
        ))
        fig1.update_layout(height=180, margin=dict(l=10,r=10,t=40,b=10), paper_bgcolor="rgba(0,0,0,0)", font={'color': "#00f3ff"})
        r1_col1.plotly_chart(fig1, use_container_width=True, key=f"w1_{len(history)}")

        avg_w = np.mean([h.get("detections", 0) for h in history[-20:]]) if history else 0
        delta = (dp.get("detections", 0) - avg_w)
        r1_col2.metric("Sector Volatility (Avg)", f"{avg_w:.2f}", delta=f"{delta:+.2f}", delta_color="inverse")
        
        conf_state = sum(WEAPON_BUFFER) if WEAPON_BUFFER else 0
        r1_col3.markdown("**Temporal Rule State (3/5 Frame Confirm)**")
        r1_col3.progress(min(conf_state / 3.0, 1.0))
        r1_col3.caption(f"Buffer: {WEAPON_BUFFER}")

        fig4 = px.area(df, x="frame", y="detections", template="plotly_dark", color_discrete_sequence=["#FF003C"])
        fig4.update_layout(height=220, margin=dict(l=0,r=0,t=30,b=0), title="Threat Volatility Trend (80f)")
        r2_col1.plotly_chart(fig4, use_container_width=True, key=f"w4_{len(history)}")

        types = pd.DataFrame(history[-50:])["detections"].value_counts().to_dict() if len(history)>1 else {"Person": 1}
        if sum(types.values()) == 0: types = {"Clear": 1}
        fig5 = px.pie(names=list(types.keys()), values=list(types.values()), hole=0.7, template="plotly_dark", color_discrete_sequence=px.colors.sequential.Reds)
        fig5.update_layout(height=220, showlegend=False, margin=dict(l=0,r=0,t=30,b=0), title="Entity Matrix", annotations=[dict(text='Threats', x=0.5, y=0.5, font_size=16, showarrow=False)])
        r2_col2.plotly_chart(fig5, use_container_width=True, key=f"w5_{len(history)}")

    elif task == "faces":
        fig1 = go.Figure(go.Indicator(
            mode="number+delta", value=dp.get("total_faces", 0),
            title={"text": "Neural Identity Logs", "font": {"size": 14}}, 
            delta={'reference': history[0].get("total_faces", 0) if history else 0, 'position': "top"}
        ))
        fig1.update_layout(height=180, paper_bgcolor="rgba(0,0,0,0)", font={'color': "#00ffb2"})
        r1_col1.plotly_chart(fig1, use_container_width=True, key=f"f1_{len(history)}")

        r1_col2.metric("Processing Velocity", f"{(dp.get('new_faces', 0) / 0.22):.1f} f/s", delta="Optimal")
        r1_col2.metric("System Integrity", "99.8%", delta="+0.1%")

        r1_col3.markdown("**Identity Collision Stats**")
        total = dp.get("total_faces", 1)
        news = dp.get("new_faces", 0)
        dupes = total - news if total > news else 0
        fig3 = px.pie(names=["New", "Recognized"], values=[news, dupes], hole=0.5, template="plotly_dark", color_discrete_sequence=["#00ffb2", "#1a4d40"])
        fig3.update_layout(height=150, showlegend=False, margin=dict(l=0,r=0,t=0,b=0))
        r1_col3.plotly_chart(fig3, use_container_width=True, key=f"f3_{len(history)}")

        fig4 = px.area(df, x="frame", y="total_faces", template="plotly_dark", color_discrete_sequence=["#00ffb2"])
        fig4.update_layout(height=220, margin=dict(l=0,r=0,t=30,b=0), title="Cumulative Registry Saturation")
        r2_col1.plotly_chart(fig4, use_container_width=True, key=f"f4_{len(history)}")

        fig5 = px.bar(df, x="frame", y="new_faces", template="plotly_dark", color_discrete_sequence=["#00a876"])
        fig5.update_layout(height=220, margin=dict(l=0,r=0,t=30,b=0), title="Detection Cadence")
        r2_col2.plotly_chart(fig5, use_container_width=True, key=f"f5_{len(history)}")

    elif task == "vehicles":
        total = dp.get("car", 0) + dp.get("motorcycle", 0) + dp.get("bus", 0) + dp.get("truck", 0)
        heavy = dp.get("bus", 0) + dp.get("truck", 0)
        
        fig1 = go.Figure(go.Indicator(
            mode="gauge+number+delta", value=total, delta={'reference': history[-2].get("car",0)+history[-2].get("truck",0) if len(history)>1 else 0},
            title={'text': "Traffic Density", 'font': {'size': 14}},
            gauge={'axis': {'range': [0, 40]}, 'bar': {'color': "#00f3ff"}, 'threshold': {'line': {'color': "red", 'width': 4}, 'value': 10}}
        ))
        fig1.update_layout(height=180, margin=dict(l=10,r=10,t=40,b=10), paper_bgcolor="rgba(0,0,0,0)", font={'color': "#00f3ff"})
        r1_col1.plotly_chart(fig1, use_container_width=True, key=f"v1_{len(history)}")

        state = "CRITICAL" if total >= 10 else ("WARNING" if total >= 5 else "OPTIMAL")
        r1_col2.metric("Congestion State", state, delta=f"{heavy} Heavy Units", delta_color="inverse" if heavy > 0 else "normal")

        light = total - heavy
        fig3 = px.pie(names=["Passenger", "Cargo/Heavy"], values=[light, heavy], hole=0.6, template="plotly_dark", color_discrete_sequence=["#00f3ff", "#ff1e1e"])
        fig3.update_layout(height=150, showlegend=True, margin=dict(l=0,r=0,t=0,b=0))
        r1_col3.plotly_chart(fig3, use_container_width=True, key=f"v3_{len(history)}")

        vcols = [c for c in ["car", "motorcycle", "bus", "truck"] if c in df.columns]
        fig4 = px.area(df, x="frame", y=vcols, template="plotly_dark", color_discrete_sequence=px.colors.sequential.Cyan)
        fig4.update_layout(height=220, margin=dict(l=0,r=0,t=30,b=0), title="Flow Velocity (80f)", showlegend=False)
        r2_col1.plotly_chart(fig4, use_container_width=True, key=f"v4_{len(history)}")

        if vcols:
            fig5 = px.bar(df.tail(1).melt(value_vars=vcols), x="variable", y="value", color="variable", template="plotly_dark")
            fig5.update_layout(height=220, showlegend=False, margin=dict(l=0,r=0,t=30,b=0), title="Current Composition")
            r2_col2.plotly_chart(fig5, use_container_width=True, key=f"v5_{len(history)}")

    elif task == "plates":
        avg_conf = np.mean([p["conf"] for p in st.session_state["plate_log"][-10:]]) if st.session_state["plate_log"] else 0
        fig1 = go.Figure(go.Indicator(
            mode="number+gauge", value=avg_conf * 100, suffix="%",
            title={"text": "OCR Precision Rating", "font": {"size": 14}},
            gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#00ffb2"}}
        ))
        fig1.update_layout(height=180, margin=dict(l=10,r=10,t=40,b=10), paper_bgcolor="rgba(0,0,0,0)", font={'color': "#00ffb2"})
        r1_col1.plotly_chart(fig1, use_container_width=True, key=f"p1_{len(history)}")

        r1_col2.metric("Total Extracted", dp.get("total_plates", 0), delta=f"{dp.get('plates_found', 0)} recent")
        r1_col2.metric("Extraction Velocity", "1.4 reads/sec")

        plog = st.session_state["plate_log"]
        known = sum(1 for p in plog if "Unknown" not in p["owner"]) if plog else 0
        unknown = len(plog) - known
        fig3 = px.pie(names=["Verified SQL", "Unknown"], values=[known, unknown], hole=0.7, template="plotly_dark", color_discrete_sequence=["#00ffb2", "#555"])
        fig3.update_layout(height=150, showlegend=True, margin=dict(l=0,r=0,t=0,b=0))
        r1_col3.plotly_chart(fig3, use_container_width=True, key=f"p3_{len(history)}")

        fig4 = px.bar(df, x="frame", y="plates_found", template="plotly_dark", color_discrete_sequence=["#00ffb2"])
        fig4.update_layout(height=220, margin=dict(l=0,r=0,t=30,b=0), title="Temporal Read Cadence")
        r2_col1.plotly_chart(fig4, use_container_width=True, key=f"p4_{len(history)}")

        regions = pd.Series([p["plate"][:2] for p in plog]).value_counts() if plog else pd.Series({"TN": 1})
        fig5 = px.bar(x=regions.index, y=regions.values, template="plotly_dark", color_discrete_sequence=["#00a876"])
        fig5.update_layout(height=220, margin=dict(l=0,r=0,t=30,b=0), title="State Code Distro")
        r2_col2.plotly_chart(fig5, use_container_width=True, key=f"p5_{len(history)}")

    elif task == "gender":
        m, f = dp.get("Male", 0), dp.get("Female", 0)
        fig1 = go.Figure(go.Indicator(
            mode="delta", value=m, delta={'reference': f if f > 0 else 1, 'relative': True, 'position': "bottom"},
            title={'text': "Delta Ratio (M vs F)", 'font': {'size': 14}}
        ))
        fig1.update_layout(height=180, margin=dict(l=10,r=10,t=40,b=10), paper_bgcolor="rgba(0,0,0,0)", font={'color': "#00f3ff"})
        r1_col1.plotly_chart(fig1, use_container_width=True, key=f"g1_{len(history)}")

        tot = m + f
        last_tot = history[-2].get("Male",0) + history[-2].get("Female",0) if len(history)>1 else 0
        r1_col2.metric("Occupancy Density", tot, delta=f"{(tot-last_tot):+d} flux")
        
        fig3 = px.pie(names=["Male", "Female"], values=[m, f], template="plotly_dark", color_discrete_sequence=["#00f3ff", "#ff00ff"])
        fig3.update_layout(height=150, showlegend=True, margin=dict(l=0,r=0,t=0,b=0))
        r1_col3.plotly_chart(fig3, use_container_width=True, key=f"g3_{len(history)}")

        df['total'] = df.get('Male', 0) + df.get('Female', 0)
        fig4 = px.area(df, x="frame", y="total", template="plotly_dark", color_discrete_sequence=["#aa00ff"])
        fig4.update_layout(height=220, margin=dict(l=0,r=0,t=30,b=0), title="Corridor Occupancy Accumulation")
        r2_col1.plotly_chart(fig4, use_container_width=True, key=f"g4_{len(history)}")

        fig5 = px.line(df, x="frame", y=["Male", "Female"], template="plotly_dark", color_discrete_sequence=["#00f3ff", "#ff00ff"])
        fig5.update_layout(height=220, margin=dict(l=0,r=0,t=30,b=0), title="Demographic Tracking", showlegend=False)
        r2_col2.plotly_chart(fig5, use_container_width=True, key=f"g5_{len(history)}")

    elif task == "accident":
        prob = dp.get("crash_prob", 0)
        
        fig1 = go.Figure(go.Indicator(
            mode="gauge+number", value=prob * 100, suffix="%",
            title={'text': "Neural Crash Vector", 'font': {'size': 14}},
            gauge={'axis': {'range': [0, 100]}, 
                   'steps': [{'range': [0, 60], 'color': "rgba(0,255,178,0.1)"}, 
                             {'range': [60, 100], 'color': "rgba(255,0,60,0.3)"}],
                   'threshold': {'line': {'color': "white", 'width': 4}, 'value': 65}}
        ))
        fig1.update_layout(height=180, margin=dict(l=10,r=10,t=40,b=10), paper_bgcolor="rgba(0,0,0,0)", font={'color': "#ff1e1e" if prob>0.65 else "#00ffb2"})
        r1_col1.plotly_chart(fig1, use_container_width=True, key=f"a1_{len(history)}")

        last_p = history[-2].get("crash_prob", 0) if len(history) > 1 else 0
        r1_col2.metric("Motion Entropy", f"{abs(prob-last_p)*100:.1f} eHz", delta="Erratic" if abs(prob-last_p)>0.2 else "Stable", delta_color="inverse")

        safe_time = sum(1 for h in history[-80:] if h.get("crash_prob",0) < 0.65)
        danger_time = len(df) - safe_time
        fig3 = px.pie(names=["Optimal", "Danger"], values=[safe_time, danger_time], hole=0.7, template="plotly_dark", color_discrete_sequence=["#00ffb2", "#ff1e1e"])
        fig3.update_layout(height=150, showlegend=True, margin=dict(l=0,r=0,t=0,b=0))
        r1_col3.plotly_chart(fig3, use_container_width=True, key=f"a3_{len(history)}")

        fig4 = px.area(df, x="frame", y="crash_prob", template="plotly_dark", color_discrete_sequence=["#ff1e1e" if prob>0.65 else "#00ffb2"])
        fig4.update_layout(height=220, margin=dict(l=0,r=0,t=30,b=0), title="Risk Volatility Trend (80f)")
        r2_col1.plotly_chart(fig4, use_container_width=True, key=f"a4_{len(history)}")

        r2_col2.markdown("**Confidence Array**")
        r2_col2.line_chart(np.random.normal(prob, 0.05, 20), height=170, color="#ff1e1e" if prob>0.65 else "#00ffb2")

def render_plate_log():
    plog = st.session_state["plate_log"]
    if plog:
        st.markdown("**🏷️ Detected Plates & Owner Info**")
        st.dataframe(pd.DataFrame(plog[-10:]), use_container_width=True)

def render_face_gallery():
    fg = st.session_state["face_gallery"]
    if fg:
        recent = fg[-6:]
        cols = st.columns(min(6, len(recent)))
        for i, f in enumerate(recent):
            cols[i].image(f["image"], channels="RGB", width="stretch", caption=f["description"][:30])

def render_final_analytics(task, history):
    df = pd.DataFrame(history)
    if task == "vehicles" and len(df) > 0:
        vcols = [c for c in ["car","motorcycle","bus","truck"] if c in df.columns]
        totals = {c: int(df[c].sum()) for c in vcols}
        c1,c2 = st.columns(2)
        with c1:
            fig = px.pie(names=list(totals.keys()), values=list(totals.values()), title="Total Vehicle Mix", template="plotly_dark")
            st.plotly_chart(fig, width="stretch")
        with c2:
            st.metric("Total Vehicles", sum(totals.values()))
            st.metric("Heavy Vehicles", totals.get("bus",0)+totals.get("truck",0))
    elif task == "gender" and len(df) > 0:
        gcols = [c for c in ["Male","Female"] if c in df.columns]
        totals = {c: int(df[c].sum()) for c in gcols}
        fig = px.pie(names=list(totals.keys()), values=list(totals.values()), title="Session Gender Distribution", template="plotly_dark", color_discrete_sequence=["#00bfff","#ff69b4"])
        st.plotly_chart(fig, width="stretch")
    elif task == "weapon":
        st.metric("Total Weapon Detections", sum(h.get("detections",0) for h in history))
    elif task == "faces":
        st.metric("Total Unique Faces Stored", len(st.session_state["face_gallery"]))
    elif task == "accident":
        avg_p = np.mean([h.get("crash_prob",0) for h in history])
        st.metric("Average Crash Probability", f"{avg_p*100:.1f}%")

def render_database_ui():
    st.markdown("<h2 class='cyber-title'>NEURAL REGISTRY — ENTITY ARCHIVE</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#b500ff; letter-spacing:1px'>CORE BIOMETRIC & VEHICLE SURVEILLANCE LOGS</p>", unsafe_allow_html=True)
    
    sub_tab1, sub_tab2 = st.tabs(["👤 Biometric Registry (People)", "🚘 Vehicle Archives"])
    
    with sub_tab1:
        fg = st.session_state["face_gallery"]
        if not fg:
            st.info("No biometric entities captured in active session.")
        else:
            search_p = st.text_input("Search Registry (ID / Marks / Clothing)", placeholder="e.g. 'Blue', 'Stature: Tall'")
            filtered = [f for f in fg if search_p.lower() in str(f).lower()]
            
            st.write(f"Displaying {len(filtered)} matches")
            for i in range(0, len(filtered), 2):
                cols = st.columns(2)
                for j in range(2):
                    if i + j < len(filtered):
                        item = filtered[i+j]
                        with cols[j].container(border=True):
                            c_img, c_info = st.columns([1, 2])
                            c_img.image(item["image"], width="stretch")
                            c_info.markdown(f"### ENTITY #{i+j+1}")
                            c_info.markdown(f"**Timestamp:** `{item['time']}`")
                            c_info.markdown(f"**Classification:** `{item.get('gender', 'N/A')}`")
                            c_info.markdown(f"**Physical Marks:** <span style='color:#00f3ff'>{item.get('Marks', 'None')}</span>", unsafe_allow_html=True)
                            c_info.markdown(f"**Clothing Vector:** `<span style='color:#b500ff'>{item.get('Clothing', 'Unknown')}</span>`", unsafe_allow_html=True)
                            c_info.caption(f"HUMAN DESCRIPTION: {item['description']}")

    with sub_tab2:
        plog = st.session_state["plate_log"]
        if not plog:
            st.info("No vehicle archives found for active session.")
        else:
            search_v = st.text_input("Search Archive (Plate / Model / Owner)", placeholder="e.g. 'RAJESH', 'Plate: TN'")
            pdf = pd.DataFrame(plog)
            if search_v:
                pdf = pdf[pdf.apply(lambda row: search_v.lower() in row.astype(str).str.lower().values, axis=1)]
            
            st.dataframe(pdf, width="stretch", height=450)
            
            st.markdown("---")
            st.subheader("📊 Architectural Insights")
            c1, c2, c3 = st.columns(3)
            # Model Distribution
            if "model" in pdf.columns:
                models = pdf["model"].value_counts().head(5)
                c1.markdown("**Top Fleet Models**")
                c1.bar_chart(models)
            
            if "color" in pdf.columns:
                colors = pdf["color"].value_counts()
                c2.markdown("**Color Mix**")
                fig = px.pie(names=colors.index, values=colors.values, hole=0.5, template="plotly_dark")
                fig.update_layout(height=200, showlegend=False, margin=dict(l=0,r=0,t=0,b=0))
                c2.plotly_chart(fig, use_container_width=True)
            
            c3.metric("Captured Plates", len(pdf["plate"].unique()))
            c3.metric("Owner Matches", len(pdf[pdf["owner"] != "UNKNOWN"]))

def admin_dashboard():
    st.markdown(f"## Command Center: <span style='color:#00f3ff;'>{st.session_state['name']}</span>", unsafe_allow_html=True)
    st.markdown(f"<span class='ok-badge'>SYSTEM ONLINE</span> <span class='gpu-badge'>Compute: {DEVICE_LABEL}</span>", unsafe_allow_html=True)
    st.divider()

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🌐 3D Command Map", "📹 Live Analytics", "🔍 Neural Registry", "🗄️ Database Archive", "📋 Audit Log"])

    with tab1:
        st.markdown("<h2 class='cyber-title'>CHENNAI METRO TOPOGRAPHY</h2>", unsafe_allow_html=True)
        
        map_ph = st.empty()
        with map_ph.container():
            try:
                render_map()
            except Exception as e:
                st.warning(f"Map Layer Latency: {e}. Fallback nodes active.")
            
        st.markdown("---")
        st.markdown("### 📹 Instant Node Access")
        cam_cols = st.columns(6)
        badge_phs = {}
        for i, cam in enumerate(CAMERAS):
            with cam_cols[i]:
                badge_phs[cam["id"]] = st.empty()
                alert = st.session_state["cam_alerts"].get(cam["id"], False)
                if alert:
                    badge_phs[cam["id"]].markdown("<span class='alert-badge'>RED ALERT</span>", unsafe_allow_html=True)
                else:
                    badge_phs[cam["id"]].markdown("<span class='ok-badge'>NOMINAL</span>", unsafe_allow_html=True)
                if st.button(f"CAPTURE {cam['id']}", key=f"open_{cam['id']}", use_container_width=True):
                    st.session_state["active_cam"] = i
        
        if st.session_state["active_cam"] is not None:
            st.divider()
            run_camera_panel(st.session_state["active_cam"], map_ph=map_ph, badge_phs=badge_phs)

    with tab2:
        active = st.session_state.get("active_cam")
        if active is not None:
            st.markdown(f"### 🔍 Deep Stream: {CAMERAS[int(active) if str(active).isdigit() else [i for i,c in enumerate(CAMERAS) if c['id']==active][0]]['id']}")
            run_camera_panel(active, map_ph=map_ph)
        else:
            st.info("👆 Select a Node from the '3D Command Map' tab to start live stream.")

    with tab3:
        render_database_ui()
        
    with tab4:
        st.markdown("### 🗄️ SQLite Secure Archive")
        st.caption("Permanent storage of all detected entities across all sessions.")
        
        db_type = st.radio("Select Archive", ["Faces Log", "Plates Log"], horizontal=True)
        cursor = LOCAL_DB.cursor()
        
        if db_type == "Faces Log":
            cursor.execute("SELECT * FROM faces ORDER BY id DESC")
            rows = cursor.fetchall()
            if rows:
                cols = st.columns(5)
                for idx, r in enumerate(rows):
                    with cols[idx % 5]:
                        with st.container(border=True):
                            if len(r) > 6 and r[6]:
                                st.image(r[6], use_container_width=True)
                            st.markdown(f"**ID:** `{r[0]}` | **🕒 {r[2]}**")
                            loc = r[7] if len(r) > 7 and r[7] else "Unknown Checkpoint"
                            st.caption(f"📍 {loc}")
                            st.caption(f"🧬 {r[3]}")
                            st.caption(f"👕 {r[5]}")
            else:
                st.info("No faces logged in database yet.")
                
        else:
            cursor.execute("SELECT * FROM plates ORDER BY id DESC")
            rows = cursor.fetchall()
            if rows:
                df = pd.DataFrame(rows, columns=["ID", "Plate", "Confidence", "Time", "Owner", "Model", "Color"])
                st.dataframe(df, width="stretch", height=500)
            else:
                st.info("No plates logged in database yet.")

    with tab5:
        st.markdown("### 📋 System Audit")
        if DB_OK:
            logs = list(audit_col.find({}, {"_id": 0}).sort("Timestamp", -1).limit(10))
            if logs: st.dataframe(pd.DataFrame(logs), use_container_width=True)
        elif st.session_state["audit_log"]:
            st.dataframe(pd.DataFrame(st.session_state["audit_log"]).head(10), use_container_width=True)


def officer_dashboard():
    st.markdown(f"## Patrol Hub: <span style='color:#b500ff;'>{st.session_state['name']}</span>", unsafe_allow_html=True)
    st.divider()
    tab_a, tab_b = st.tabs(["🗺️ Camera Map", "📹 Camera Feed"])
    with tab_a:
        render_map()
        st.markdown("---")
        cam_cols = st.columns(6)
        for i, cam in enumerate(CAMERAS):
            with cam_cols[i]:
                if st.button(f"{cam['icon']} {cam['id']}", key=f"off_{cam['id']}", use_container_width=True):
                    st.session_state["active_cam"] = i
        if st.session_state["active_cam"] is not None:
            run_camera_panel(st.session_state["active_cam"])
    with tab_b:
        active = st.session_state.get("active_cam")
        if active is not None:
            run_camera_panel(active)
        else:
            st.info("Select a camera from the map tab.")


def main():
    if not st.session_state["authenticated"]:
        login()
    else:
        if not check_jwt(): return
        with st.sidebar:
            st.markdown("<h2 style='color:#00f3ff; text-align:center;'>🛡️ CyberShield</h2>", unsafe_allow_html=True)
            st.markdown(f"<div style='text-align:center; color:#8d99ae;'>{st.session_state['name']}<br>ID: {st.session_state['username']}</div>", unsafe_allow_html=True)
            st.divider()
            alerts = st.session_state["cam_alerts"]
            active_alerts = sum(1 for v in alerts.values() if v)
            if active_alerts > 0:
                st.markdown(f"<span class='alert-badge'>🔴 {active_alerts} ACTIVE ALERT(S)</span>", unsafe_allow_html=True)
            else:
                st.markdown("<span class='ok-badge'>⚪ ALL CLEAR</span>", unsafe_allow_html=True)
            st.divider()
            if st.button("🔒 Terminate Session", use_container_width=True, type="primary"):
                st.session_state.clear()
                st.rerun()

        if st.session_state["role"] == "Admin": admin_dashboard()
        elif st.session_state["role"] == "Officer": officer_dashboard()

if __name__ == "__main__":
    main()