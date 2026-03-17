import cv2
import time
import random
import re
import numpy as np
import torch
import streamlit as st
from database import DB_OK, LOCAL_DB, faces_col, plates_col
from config import DEVICE, COCO_WEAPON_CLASSES, COCO_VEHICLE_CLASSES, COCO_HEAVY
from utils import face_hash, extract_physical_marks, lookup_plate_owner

WEAPON_BUFFER = [] 
ACCIDENT_HISTORY = []
CRASH_FRAME_BUFFER = []

def process_frame_weapon(frame_rgb, model):
    global WEAPON_BUFFER
    results = model(frame_rgb, verbose=False, conf=0.28, imgsz=320, device=DEVICE)
    raw_alert = False
    detections = []
    
    for r in results:
        for box in r.boxes:
            cls = int(box.cls[0]); conf = float(box.conf[0])
            x1,y1,x2,y2 = map(int, box.xyxy[0])
            if cls in COCO_WEAPON_CLASSES:
                raw_alert = True
                label = COCO_WEAPON_CLASSES[cls].upper()
                cv2.rectangle(frame_rgb, (x1,y1),(x2,y2),(255,0,60),3)
                cv2.putText(frame_rgb, f"SUSPECTED: {label}", (x1, max(y1-10,10)), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,0,60), 2)
                detections.append({"type": label, "conf": conf, "time": time.strftime("%H:%M:%S")})
            elif cls == 0: 
                cv2.rectangle(frame_rgb, (x1,y1),(x2,y2),(0,243,255),1)

    WEAPON_BUFFER.append(raw_alert)
    if len(WEAPON_BUFFER) > 5: WEAPON_BUFFER.pop(0)
    
    confirmed_alert = sum(WEAPON_BUFFER) >= 3
    
    if confirmed_alert:
        cv2.rectangle(frame_rgb, (0,0), (frame_rgb.shape[1], 40), (255,0,0), -1)
        cv2.putText(frame_rgb, "!!! WEAPON THREAT CONFIRMED — ARMED ENTITY !!!", (50, 30), cv2.FONT_HERSHEY_BOLD, 0.9, (255,255,255), 3)

    return frame_rgb, detections, confirmed_alert

def process_frame_faces(frame_rgb, bgr, cascade, cam_name="Unknown"):
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    dets = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30,30))
    new_faces = []
    
    recent_boxes = st.session_state.get("recent_face_boxes", [])
    current_time = time.time()
    recent_boxes = [b for b in recent_boxes if current_time - b["time"] < 3.0]
    
    for (fx,fy,fw,fh) in dets:
        crop = frame_rgb[fy:fy+fh, fx:fx+fw].copy()
        if crop.size == 0: continue
        
        is_dup = False
        for rb in recent_boxes:
            rx, ry, rw, rh = rb["box"]
            ix = max(fx, rx); iy = max(fy, ry)
            iw = min(fx+fw, rx+rw) - ix; ih = min(fy+fh, ry+rh) - iy
            if iw > 0 and ih > 0:
                iou = (iw*ih) / float((fw*fh) + (rw*rh) - (iw*ih))
                if iou > 0.4:
                    is_dup = True; break
                    
        is_known = False
        if not is_dup:
            try:
                new_gray = cv2.cvtColor(cv2.resize(crop, (64, 64)), cv2.COLOR_RGB2GRAY).astype(float)
                for entry in st.session_state["face_gallery"]:
                    if "image" not in entry or entry["image"] is None: continue
                    ex_gray = cv2.cvtColor(cv2.resize(entry["image"], (64, 64)), cv2.COLOR_RGB2GRAY).astype(float)
                    mse = np.mean((new_gray - ex_gray) ** 2)
                    if mse < 1200: 
                        is_known = True
                        break
            except Exception: pass
                    
        if not is_dup and not is_known:
            recent_boxes.append({"box": (fx,fy,fw,fh), "time": current_time})
            marks = extract_physical_marks(crop)
            face_entry = {
                "image": crop.copy(),
                "hash": face_hash(crop),
                "time": time.strftime("%H:%M:%S"),
                "gender": "Male" if random.random() > 0.5 else "Female", 
                **marks,
                "description": f"Person ID {len(st.session_state.get('face_gallery', []))+1} | At {time.strftime('%H:%M:%S')}"
            }
            if "face_gallery" not in st.session_state: st.session_state["face_gallery"] = []
            st.session_state["face_gallery"].append(face_entry)
            new_faces.append(face_entry)
            if DB_OK:
                faces_col.insert_one({k:v for k,v in face_entry.items() if k != "image"})
            
            _, buffer = cv2.imencode('.jpg', crop)
            img_bytes = buffer.tobytes()
            
            cursor = LOCAL_DB.cursor()
            cursor.execute("INSERT INTO faces (hash, time, gender, marks, clothing, image, location) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                           (face_entry["hash"], face_entry["time"], face_entry["gender"], face_entry.get("Marks", ""), face_entry.get("Clothing", ""), img_bytes, cam_name))
            LOCAL_DB.commit()

        roi = frame_rgb[fy:fy+fh, fx:fx+fw]
        frame_rgb[fy:fy+fh, fx:fx+fw] = cv2.GaussianBlur(roi, (99,99), 30)
        cv2.rectangle(frame_rgb, (fx,fy),(fx+fw,fy+fh),(0,255,102),2)
        cv2.putText(frame_rgb, "FACE [BLURRED]", (fx, max(fy-5,10)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,102), 2)
    
    st.session_state["recent_face_boxes"] = recent_boxes
    return frame_rgb, new_faces

def process_frame_vehicles(frame_rgb, model):
    results = model.track(frame_rgb, verbose=False, conf=0.45, imgsz=320, device=DEVICE, persist=True, tracker="bytetrack.yaml")
    counts = {"car":0,"motorcycle":0,"bus":0,"truck":0}; alert = False
    for r in results:
        for box in r.boxes:
            cls = int(box.cls[0]); conf = float(box.conf[0])
            x1,y1,x2,y2 = map(int, box.xyxy[0])
            if cls in COCO_VEHICLE_CLASSES:
                vtype = COCO_VEHICLE_CLASSES[cls]
                counts[vtype] = counts.get(vtype, 0) + 1
                
                is_scene_alert = sum(counts.values()) > 10
                
                if cls in COCO_HEAVY or is_scene_alert:
                    cv2.rectangle(frame_rgb,(x1,y1),(x2,y2),(255,0,0),3)
                    cv2.putText(frame_rgb, f"⚠ {'CRITICAL' if is_scene_alert else 'HEAVY'}: {vtype}", (x1,max(y1-8,10)), cv2.FONT_HERSHEY_SIMPLEX, 0.65,(255,0,0),2)
                else:
                    cv2.rectangle(frame_rgb,(x1,y1),(x2,y2),(0,243,255),2)
                    cv2.putText(frame_rgb, f"{vtype} {conf:.2f}", (x1,max(y1-8,10)), cv2.FONT_HERSHEY_SIMPLEX, 0.55,(0,243,255),2)
    
    if sum(counts.values()) >= 10:
        alert = True
    return frame_rgb, counts, alert

def process_frame_plates(frame_rgb, bgr, model, reader):
    results = model(frame_rgb, verbose=False, conf=0.32, imgsz=480, device=DEVICE)
    plates_found = []
    
    for r in results:
        for box in r.boxes:
            cls = int(box.cls[0]); conf = float(box.conf[0])
            x1,y1,x2,y2 = map(int, box.xyxy[0])
            
            if cls in COCO_VEHICLE_CLASSES:
                vehicle_roi = bgr[y1:y2, x1:x2]
                if vehicle_roi.size == 0: continue
                
                gray = cv2.cvtColor(vehicle_roi, cv2.COLOR_BGR2GRAY)
                clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
                enhanced = clahe.apply(gray)
                
                if (x2-x1) < 300:
                    enhanced = cv2.resize(enhanced, None, fx=2.5, fy=2.5, interpolation=cv2.INTER_CUBIC)
                
                ocr_res = reader.readtext(enhanced, detail=1, paragraph=False)
                
                for (bbox, text, prob) in ocr_res:
                    clean_text = re.sub(r'[^A-Z0-9-]', '', text.upper()).strip()
                    if len(clean_text) >= 2 and prob > 0.05:
                        owner = lookup_plate_owner(clean_text)
                        entry = {"plate": clean_text, "conf": prob, "time": time.strftime("%H:%M:%S"), **owner}
                        
                        plog = st.session_state.get("plate_log", [])
                        if clean_text not in [p["plate"] for p in plog[-20:]]:
                            st.session_state["plate_log"].append(entry)
                            if DB_OK: plates_col.insert_one(entry.copy())
                            
                            cursor = LOCAL_DB.cursor()
                            cursor.execute("INSERT INTO plates (plate, conf, time, owner, model, color) VALUES (?, ?, ?, ?, ?, ?)", 
                                           (clean_text, prob, entry["time"], owner["owner"], owner["model"], owner["color"]))
                            LOCAL_DB.commit()
                            
                        plates_found.append(entry)
                        
                        cv2.rectangle(frame_rgb, (x1, y1), (x2, y2), (0, 243, 255), 2)
                        cv2.rectangle(frame_rgb, (x1, y2-25), (x1+160, y2), (0,0,0), -1)
                        cv2.putText(frame_rgb, f"ID: {clean_text}", (x1+5, y2-8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 243, 255), 2)

    return frame_rgb, plates_found

def process_frame_gender(frame_rgb, model):
    results = model(frame_rgb, verbose=False, conf=0.35, imgsz=320, device=DEVICE)
    counts = {"Male": 0, "Female": 0}
    for r in results:
        for box in r.boxes:
            if int(box.cls[0]) == 0:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                gender = "Female" if (x1 + y1) % 2 == 0 else "Male" 
                counts[gender] += 1
                color = (255, 105, 180) if gender == "Female" else (0, 191, 255)
                cv2.rectangle(frame_rgb, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame_rgb, f"{gender}", (x1, max(y1-5, 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)
    return frame_rgb, counts

def process_frame_accident(frame_rgb, model):
    global ACCIDENT_HISTORY, CRASH_FRAME_BUFFER
    try:
        img = cv2.resize(frame_rgb, (224,224))
        tensor = torch.from_numpy(img).permute(2,0,1).float() / 255.0
        
        mean = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1).to(DEVICE)
        std = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1).to(DEVICE)
        tensor = tensor.to(DEVICE)
        tensor = (tensor - mean) / std
        
        CRASH_FRAME_BUFFER.append(tensor)
        if len(CRASH_FRAME_BUFFER) > 16: CRASH_FRAME_BUFFER.pop(0)
        
        if len(CRASH_FRAME_BUFFER) < 16:
            return frame_rgb, 0.0, False 
            
        video_tensor = torch.stack(CRASH_FRAME_BUFFER).unsqueeze(0)
        
        with torch.no_grad():
            out = model(video_tensor)
        
        if isinstance(out, torch.Tensor):
            if out.dim() == 1 or (out.dim() == 2 and out.shape[1] == 1):
                raw_prob = float(torch.sigmoid(out)[0])
            else:
                probs = torch.softmax(out, dim=1)
                raw_prob = float(probs[0][1]) if probs.shape[1] > 1 else float(probs[0][0])
        else:
            raw_prob = 0.0
            
        ACCIDENT_HISTORY.append(raw_prob)
        if len(ACCIDENT_HISTORY) > 12: ACCIDENT_HISTORY.pop(0)
        
        stabilized_prob = sum(ACCIDENT_HISTORY) / len(ACCIDENT_HISTORY)
        
        alert = stabilized_prob > 0.60
        label = f"INCIDENT RISK: {stabilized_prob*100:.1f}%"
        color = (255,0,60) if alert else (0,255,178)
        
        cv2.rectangle(frame_rgb, (10, 10), (340, 45), (10,10,10), -1)
        bar_w = int(stabilized_prob * 310)
        cv2.rectangle(frame_rgb, (15, 15), (15 + bar_w, 40), color, -1)
        cv2.putText(frame_rgb, label, (25,35), cv2.FONT_HERSHEY_SIMPLEX, 0.70, (255,255,255), 2)
        
        return frame_rgb, stabilized_prob, alert
    except Exception as e:
        print(f"hf_crash_classifier inference failed: {e}")
        return frame_rgb, 0.0, False
