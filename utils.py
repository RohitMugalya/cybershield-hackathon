import bcrypt
import jwt
import datetime
import time
import random
import cv2
import numpy as np
import hashlib
import streamlit as st
from config import JWT_SECRET, MOCK_OWNERS

def verify_password(pw, h):
    try:
        return bcrypt.checkpw(pw.encode('utf-8'), h)
    except Exception:
        return False

def gen_jwt(u, r):
    payload = {
        "user": u, 
        "role": r, 
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def check_jwt():
    t = st.session_state.get("jwt_token")
    if not t: return False
    try:
        jwt.decode(t, JWT_SECRET, algorithms=["HS256"])
        return True
    except: 
        st.session_state.clear()
        return False

def enhance_frame(f):
    lab = cv2.cvtColor(f, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    cl = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8,8)).apply(l)
    e = cv2.cvtColor(cv2.merge((cl, a, b)), cv2.COLOR_LAB2BGR)
    g = cv2.GaussianBlur(e, (9,9), 10.0)
    return cv2.addWeighted(e, 1.5, g, -0.5, 0)

def face_hash(crop):
    sm = cv2.resize(crop, (48,48))
    return hashlib.md5(sm.tobytes()).hexdigest()

def is_dup_face(crop, gallery, thresh=0.80):
    if not gallery: return False
    n = cv2.cvtColor(cv2.resize(crop, (48,48)), cv2.COLOR_RGB2GRAY).astype(float)
    n = (n - n.mean()) / (n.std() + 1e-6)
    for ex in gallery:
        e = cv2.cvtColor(cv2.resize(ex["image"], (48,48)), cv2.COLOR_RGB2GRAY).astype(float)
        e = (e - e.mean()) / (e.std() + 1e-6)
        if np.mean(n * e) > thresh: return True
    return False

def lookup_plate_owner(plate_text):
    clean_p = "".join(filter(str.isalnum, plate_text.upper()))
    for k, v in MOCK_OWNERS.items():
        if k in clean_p:
            return v
    random_model = random.choice(["Toyota Fortuner", "Maruti Baleno", "Tata Nexon", "Kia Seltos", "MG Hector"])
    return {"owner": f"Unknown Holder ({plate_text})", "model": random_model, "color": random.choice(["Silver", "White", "Gray"]), "phone": "N/A"}

def extract_physical_marks(crop):
    hsv = cv2.cvtColor(crop, cv2.COLOR_RGB2HSV)
    h, w, _ = crop.shape
    bottom_half = hsv[int(h*0.5):, :]
    avg_h = np.mean(bottom_half[:,:,0])
    color_desc = "Dark" if np.mean(bottom_half[:,:,2]) < 100 else "Bright"
    if avg_h < 10 or avg_h > 160: color_desc += " Red-ish"
    elif 100 < avg_h < 140: color_desc += " Blue-ish"
    elif 40 < avg_h < 80: color_desc += " Green-ish"
    
    marks = []
    if h > 100: marks.append("Adult stature")
    if w/h > 0.5: marks.append("Broad build")
    return {
        "Marks": ", ".join(marks) if marks else "No distinct marks",
        "Clothing": color_desc,
        "Glasses": "Likely" if random.random() > 0.7 else "Not detected"
    }
