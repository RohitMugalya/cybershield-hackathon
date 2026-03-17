import sqlite3
import streamlit as st
import datetime
import cv2
import numpy as np

audit_col = None
faces_col = None
plates_col = None

try:
    from pymongo import MongoClient
    _mc = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=1000)
    _mc.server_info()
    db = _mc["cybershield"]
    audit_col = db["audit_logs"]
    faces_col = db["detected_faces"]
    plates_col = db["detected_plates"]
    DB_OK = True
except Exception:
    DB_OK = False

def init_sqlite():
    conn = sqlite3.connect("cybershield.db", check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS faces (id INTEGER PRIMARY KEY AUTOINCREMENT, hash TEXT, time TEXT, gender TEXT, marks TEXT, clothing TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS plates (id INTEGER PRIMARY KEY AUTOINCREMENT, plate TEXT, conf REAL, time TEXT, owner TEXT, model TEXT, color TEXT)''')
    
    # Secure Auth Table Migration
    c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, name TEXT, role TEXT, hash_pw TEXT)''')

    # Insert default Admin if users table is empty
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        import bcrypt
        default_hash = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode()
        c.execute("INSERT INTO users (username, name, role, hash_pw) VALUES (?, ?, ?, ?)", ("admin", "System Administrator", "Admin", default_hash))

    # Safely migrate schema to include image blobs for older DBs
    try: c.execute('''ALTER TABLE faces ADD COLUMN image BLOB''')
    except: pass
    
    # Safely migrate schema to include geographical location
    try: c.execute('''ALTER TABLE faces ADD COLUMN location TEXT''')
    except: pass
    
    conn.commit()
    return conn

LOCAL_DB = init_sqlite()

def log_audit(uid, action, status):
    ev = {"Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "User": uid, "Action": action, "Status": status}
    if DB_OK:
        audit_col.insert_one(ev.copy())
    else:
        if "audit_log" not in st.session_state:
            st.session_state["audit_log"] = []
        st.session_state["audit_log"].insert(0, ev)

def load_db_faces_to_session():
    if "db_faces_loaded" not in st.session_state:
        st.session_state["db_faces_loaded"] = True
        if "face_gallery" not in st.session_state:
            st.session_state["face_gallery"] = []
        try:
            cursor = LOCAL_DB.cursor()
            cursor.execute("SELECT hash, time, gender, marks, clothing, image, location FROM faces WHERE image IS NOT NULL")
            for row in cursor.fetchall():
                nparr = np.frombuffer(row[5], np.uint8)
                crp = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if crp is not None:
                    st.session_state["face_gallery"].append({
                        "hash": row[0],
                        "time": row[1] if row[1] else "Unknown",
                        "gender": row[2] if row[2] else "N/A",
                        "Marks": row[3] if row[3] else "None",
                        "Clothing": row[4] if row[4] else "Unknown",
                        "image": crp,
                        "location": row[6] if len(row) > 6 and row[6] else "Unknown",
                        "description": f"Archived Face | {row[1]}"
                    })
        except Exception: pass
