-- CyberShield Database Schema
-- PostgreSQL

-- ─── Drop existing tables (in reverse order) ─────────────────────────────────
DROP TABLE IF EXISTS face_access_log CASCADE;
DROP TABLE IF EXISTS watchlist CASCADE;
DROP TABLE IF EXISTS incidents CASCADE;
DROP TABLE IF EXISTS vehicle_detections CASCADE;
DROP TABLE IF EXISTS criminal_records CASCADE;
DROP TABLE IF EXISTS vehicles CASCADE;
DROP TABLE IF EXISTS citizens CASCADE;
DROP TABLE IF EXISTS alert_log CASCADE;
DROP TABLE IF EXISTS police_officers CASCADE;
DROP TABLE IF EXISTS cameras CASCADE;
DROP TABLE IF EXISTS areas CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- ─── Areas ────────────────────────────────────────────────────────────────────
CREATE TABLE areas (
    area_id SERIAL PRIMARY KEY,
    area_name VARCHAR(100) NOT NULL,
    zone_coordinates TEXT,  -- Polygon as WKT
    center_lat FLOAT,
    center_lon FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ─── Cameras ──────────────────────────────────────────────────────────────────
CREATE TABLE cameras (
    camera_id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    area_id INTEGER REFERENCES areas(area_id),
    lat FLOAT NOT NULL,
    lon FLOAT NOT NULL,
    signal_number VARCHAR(20),
    address TEXT,
    rtsp_url TEXT,
    status VARCHAR(20) DEFAULT 'operational', -- operational, offline, high_alert
    installed_at DATE,
    last_ping TIMESTAMP DEFAULT NOW()
);

-- ─── Users (Admin) ────────────────────────────────────────────────────────────
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'admin', -- admin, superadmin
    email VARCHAR(200),
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);

-- ─── Police Officers ──────────────────────────────────────────────────────────
CREATE TABLE police_officers (
    officer_id SERIAL PRIMARY KEY,
    badge_number VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    phone_number VARCHAR(20),
    email VARCHAR(200),
    telegram_chat_id VARCHAR(50),
    assigned_area INTEGER REFERENCES areas(area_id),
    role VARCHAR(100) DEFAULT 'Officer', -- Officer, Senior Inspector, Traffic Officer
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);

-- ─── Citizens Metadata ────────────────────────────────────────────────────────
CREATE TABLE citizens (
    citizen_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    aadhar_number VARCHAR(64),  -- Encrypted hash
    age INTEGER,
    phone VARCHAR(20),
    address TEXT,
    photo_url TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ─── Vehicles ─────────────────────────────────────────────────────────────────
CREATE TABLE vehicles (
    vehicle_id SERIAL PRIMARY KEY,
    license_plate VARCHAR(30) UNIQUE NOT NULL,
    owner_id INTEGER REFERENCES citizens(citizen_id),
    make VARCHAR(100),
    model VARCHAR(100),
    year INTEGER,
    color VARCHAR(50),
    vehicle_type VARCHAR(50),  -- Car, Bike, SUV, Truck, Auto
    registration_valid_till DATE,
    insurance_valid_till DATE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ─── Criminal Records ─────────────────────────────────────────────────────────
CREATE TABLE criminal_records (
    record_id SERIAL PRIMARY KEY,
    citizen_id INTEGER REFERENCES citizens(citizen_id),
    case_type VARCHAR(100),   -- Theft, Rash driving, Violence, etc.
    case_number VARCHAR(100),
    case_date DATE,
    status VARCHAR(50) DEFAULT 'Pending', -- Active, Resolved, Pending
    description TEXT,
    severity VARCHAR(20) DEFAULT 'Low' -- Low, Medium, High
);

-- ─── Vehicle Detections ───────────────────────────────────────────────────────
CREATE TABLE vehicle_detections (
    detection_id SERIAL PRIMARY KEY,
    license_plate VARCHAR(30),
    vehicle_id INTEGER REFERENCES vehicles(vehicle_id),
    camera_id INTEGER REFERENCES cameras(camera_id),
    detected_at TIMESTAMP DEFAULT NOW(),
    vehicle_type VARCHAR(50),
    color VARCHAR(50),
    confidence FLOAT,
    speed_kmph FLOAT,
    snapshot_url TEXT,
    video_clip_url TEXT,
    area_id INTEGER REFERENCES areas(area_id)
);

-- ─── Incidents ────────────────────────────────────────────────────────────────
CREATE TABLE incidents (
    incident_id SERIAL PRIMARY KEY,
    incident_type VARCHAR(100) NOT NULL, -- violence, traffic, loitering, face_match
    camera_id INTEGER REFERENCES cameras(camera_id),
    area_id INTEGER REFERENCES areas(area_id),
    severity VARCHAR(20) DEFAULT 'Medium', -- Low, Medium, High, Critical
    confidence FLOAT,
    description TEXT,
    lat FLOAT,
    lon FLOAT,
    persons_involved INTEGER,
    snapshot_url TEXT,
    video_clip_url TEXT,
    status VARCHAR(50) DEFAULT 'Active', -- Active, Responded, Resolved, Dismissed
    responded_by INTEGER REFERENCES police_officers(officer_id),
    responded_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ─── Alert Log ────────────────────────────────────────────────────────────────
CREATE TABLE alert_log (
    alert_id SERIAL PRIMARY KEY,
    incident_id INTEGER REFERENCES incidents(incident_id),
    officer_id INTEGER REFERENCES police_officers(officer_id),
    channel VARCHAR(50), -- sms, call, telegram, email, dashboard
    status VARCHAR(50) DEFAULT 'Sent', -- Sent, Delivered, Failed
    message TEXT,
    sent_at TIMESTAMP DEFAULT NOW(),
    delivered_at TIMESTAMP
);

-- ─── Watchlist ────────────────────────────────────────────────────────────────
CREATE TABLE watchlist (
    person_id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    alias VARCHAR(255),
    age INTEGER,
    last_known_address TEXT,
    court_order_number VARCHAR(100) NOT NULL,
    issuing_court VARCHAR(200),
    order_date DATE,
    case_type VARCHAR(100),
    case_number VARCHAR(100),
    severity VARCHAR(20) DEFAULT 'High',
    officer_in_charge INTEGER REFERENCES police_officers(officer_id),
    encrypted_embedding BYTEA,  -- Encrypted 512D face embedding
    valid_from DATE DEFAULT CURRENT_DATE,
    valid_until DATE,
    status VARCHAR(20) DEFAULT 'Active', -- Active, Expired, Resolved
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ─── Face Access Log (GDPR Audit) ─────────────────────────────────────────────
CREATE TABLE face_access_log (
    log_id SERIAL PRIMARY KEY,
    officer_id INTEGER REFERENCES police_officers(officer_id),
    person_id INTEGER REFERENCES watchlist(person_id),
    access_type VARCHAR(50),  -- View, Search, auto_match
    justification TEXT,
    ip_address VARCHAR(50),
    timestamp TIMESTAMP DEFAULT NOW()
);

-- ─── Sample Data ──────────────────────────────────────────────────────────────

-- Areas
INSERT INTO areas (area_name, center_lat, center_lon) VALUES
    ('Area 1 - North Zone', 13.1125, 80.2348),
    ('Area 2 - South Zone', 13.0418, 80.2341),
    ('Area 3 - East Zone', 12.9939, 80.2700),
    ('Area 4 - West Zone', 13.0527, 80.1273),
    ('Area 5 - Central Zone', 13.0827, 80.2707);

-- Cameras
INSERT INTO cameras (name, area_id, lat, lon, signal_number, address, status) VALUES
    ('North Gate Signal', 1, 13.1125, 80.2348, 'Signal #1', 'North Gate, Chennai', 'operational'),
    ('T. Nagar Junction', 2, 13.0418, 80.2341, 'Signal #2', 'T. Nagar, Chennai', 'operational'),
    ('Anna Salai Junction', 1, 13.0674, 80.2572, 'Signal #3', 'Anna Salai, Chennai', 'high_alert'),
    ('Velachery Main Road', 3, 12.9815, 80.2180, 'Signal #4', 'Velachery, Chennai', 'operational'),
    ('Perambur Signal', 1, 13.1152, 80.2459, 'Signal #5', 'Perambur, Chennai', 'operational'),
    ('Mylapore Temple', 2, 13.0335, 80.2680, 'Signal #6', 'Mylapore, Chennai', 'operational'),
    ('East Coast Road', 3, 12.9939, 80.2700, 'Signal #7', 'ECR, Chennai', 'offline'),
    ('Guindy Industrial', 4, 13.0067, 80.2206, 'Signal #8', 'Guindy, Chennai', 'operational'),
    ('Poonamallee Highway', 4, 13.0527, 80.1273, 'Signal #9', 'Poonamallee, Chennai', 'operational'),
    ('Central Station', 5, 13.0827, 80.2707, 'Signal #10', 'Central Station, Chennai', 'high_alert');

-- Admin user (password: admin@123)
INSERT INTO users (username, password_hash, role, email) VALUES
    ('admin', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'superadmin', 'admin@cybershield.gov.in');

-- Police Officers (password: officer@123)
INSERT INTO police_officers (badge_number, name, phone_number, email, assigned_area, role, password_hash) VALUES
    ('12345', 'Rajesh Kumar', '+919876543210', 'rajesh@police.gov.in', 1, 'Senior Inspector', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW'),
    ('12346', 'Priya Sharma', '+919876543211', 'priya@police.gov.in', 2, 'Officer', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW'),
    ('12347', 'Arun Krishnan', '+919876543212', 'arun@police.gov.in', 3, 'Traffic Officer', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW'),
    ('12348', 'Sunita Pillai', '+919876543213', 'sunita@police.gov.in', 4, 'Officer', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW'),
    ('12349', 'Vikram Nair', '+919876543214', 'vikram@police.gov.in', 5, 'Senior Inspector', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW');

-- Citizens
INSERT INTO citizens (name, age, phone, address) VALUES
    ('Rajesh Kumar', 34, '+91-9876512345', 'Chennai, Tamil Nadu'),
    ('Priya Devi', 28, '+91-9876512346', 'Madurai, Tamil Nadu'),
    ('Suresh Babu', 45, '+91-9876512347', 'Trichy, Tamil Nadu'),
    ('Kavitha Rajan', 32, '+91-9876512348', 'Coimbatore, Tamil Nadu'),
    ('Mohammed Ali', 29, '+91-9876512349', 'Chennai, Tamil Nadu'),
    ('Anitha Sundaram', 38, '+91-9876512350', 'Chennai, Tamil Nadu'),
    ('Deepan Chandra', 52, '+91-9876512351', 'Chennai, Tamil Nadu'),
    ('Meena Ganesan', 41, '+91-9876512352', 'Chennai, Tamil Nadu');

-- Vehicles
INSERT INTO vehicles (license_plate, owner_id, make, model, year, color, vehicle_type, registration_valid_till) VALUES
    ('TN01AB1234', 1, 'Honda', 'City 2020', 2020, 'White', 'Car', '2028-05-15'),
    ('TN02CD5678', 2, 'Hyundai', 'i20', 2021, 'Silver', 'Car', '2029-03-20'),
    ('TN03EF9012', 3, 'Mahindra', 'XUV700', 2022, 'Black', 'SUV', '2030-07-10'),
    ('TN04GH3456', 4, 'Toyota', 'Fortuner', 2019, 'Black', 'SUV', '2027-01-25'),
    ('TN05IJ7890', 5, 'Bajaj', 'Pulsar 150', 2023, 'Red', 'Bike', '2026-11-08'),
    ('TN06KL2345', 6, 'Yamaha', 'FZ-S', 2022, 'Blue', 'Bike', '2029-06-14'),
    ('TN07MN6789', 7, 'Tata', 'Nexon', 2021, 'Orange', 'Car', '2028-09-30'),
    ('TN08OP1234', 8, 'Maruti', 'Swift', 2020, 'Grey', 'Car', '2027-12-05');

-- Criminal Records (for suspicious owners)
INSERT INTO criminal_records (citizen_id, case_type, case_number, case_date, status, severity, description) VALUES
    (3, 'Rash Driving', 'CAS/2023/1234', '2023-06-15', 'Resolved', 'Medium', 'Rash driving on ECR, caused minor accident'),
    (3, 'Minor Accident', 'CAS/2022/5678', '2022-03-20', 'Resolved', 'Low', 'Minor road accident, no injuries'),
    (4, 'Suspected Theft', 'CAS/2024/9012', '2024-01-10', 'Pending', 'High', 'Suspected involvement in jewelry theft case'),
    (5, 'Traffic Violation', 'CAS/2023/3456', '2023-09-05', 'Resolved', 'Low', 'Multiple traffic signal violations');
