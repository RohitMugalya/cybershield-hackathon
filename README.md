# CyberShield - AI Command Center

CyberShield is a secure AI video analytics gateway capable of real-time monitoring and processing of 6 distinct video streams simultaneously. It incorporates advanced computer vision models to provide critical security insights.

## Features
- **Weapon Detection:** RT-DETR model to identify and track weapons.
- **Facial Recognition:** Cascades to detect and blur faces, while logging them in a biometric database.
- **Vehicle Counting:** YOLOv8n implementation to count and alert on heavy vehicles in real traffic streams.
- **ANPR Checkpoint:** Read license plates and look up associated mock owners.
- **Gender Analytics:** Analyzes live YouTube streams for demographic distributions.
- **Accident Prediction:** Uses custom HF models for erratic motion and crash risk modeling.
- **3D Topographic Mapping:** Real-time location tracking using PyDeck with simulated procedural fallback blocks.

## Setup
1. **Requirements**
   ```bash
   pip install -r requirements.txt
   ```
2. **Models**
   Ensure your models (e.g. `rtdetr-l.pt`, `yolov8n.pt`, `edge_crash_classifier_scripted.pt`) are downloaded and accessible in the root folder.
3. **Database**
   The application automatically initializes an SQLite database (`cybershield.db`) upon launch to store plates, faces, and logging. MongoDB is optional but supported explicitly.

## Running
```bash
streamlit run app.py
```
