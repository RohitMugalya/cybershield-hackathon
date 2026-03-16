"""
AI Models - Vehicle Detection (YOLOv8)
CyberShield Video Analytics System

Wraps YOLOv8 for vehicle and person detection.
Falls back to simulated results if model not available.
"""

import time
import random
import numpy as np
from datetime import datetime
from pathlib import Path


class VehicleDetector:
    """YOLOv8-based vehicle and person detector"""

    VEHICLE_CLASSES = {
        2: "Car", 3: "Bike", 5: "Bus", 7: "Truck",
        0: "Person", 1: "Bicycle"
    }
    COLORS = {
        "Car": (0, 255, 0),
        "Bike": (255, 165, 0),
        "Bus": (0, 0, 255),
        "Truck": (255, 0, 0),
        "Person": (0, 255, 255),
        "Bicycle": (255, 255, 0),
    }

    def __init__(self, model_path: str = "models/yolov8n.pt"):
        self.model_path = model_path
        self.model = None
        self.available = False
        self._load_model()

    def _load_model(self):
        try:
            from ultralytics import YOLO
            if Path(self.model_path).exists():
                self.model = YOLO(self.model_path)
                self.available = True
                print(f"✅ YOLOv8 model loaded: {self.model_path}")
            else:
                print(f"⚠️ Model not found at {self.model_path} — using simulation mode")
        except ImportError:
            print("⚠️ ultralytics not installed — using simulation mode")
        except Exception as e:
            print(f"⚠️ Error loading YOLO model: {e} — using simulation mode")

    def detect(self, frame: np.ndarray) -> dict:
        """
        Run detection on a frame.
        Returns dict with:
          - detections: list of {class, bbox, confidence}
          - vehicle_count: int
          - person_count: int
          - processing_time_ms: float
        """
        start = time.time()

        if self.available and self.model is not None:
            return self._real_detect(frame, start)
        else:
            return self._simulated_detect(start)

    def _real_detect(self, frame, start_time):
        import cv2
        results = self.model(frame, verbose=False)
        detections = []

        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                label = self.VEHICLE_CLASSES.get(cls_id, "Unknown")
                conf = float(box.conf[0])
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                detections.append({
                    "class": label,
                    "bbox": (x1, y1, x2 - x1, y2 - y1),
                    "confidence": conf,
                    "color": self.COLORS.get(label, (255, 255, 255)),
                })

        vehicles = [d for d in detections if d["class"] != "Person"]
        persons = [d for d in detections if d["class"] == "Person"]
        processing_ms = (time.time() - start_time) * 1000

        return {
            "detections": detections,
            "vehicle_count": len(vehicles),
            "person_count": len(persons),
            "vehicles": vehicles,
            "persons": persons,
            "processing_time_ms": round(processing_ms, 1),
            "fps": round(1000 / max(processing_ms, 1), 1),
        }

    def _simulated_detect(self, start_time):
        """Simulate detections for demo"""
        vehicle_types = ["Car", "Car", "Car", "Bike", "Bike", "SUV", "Bus", "Truck"]
        num_vehicles = random.randint(2, 8)
        num_persons = random.randint(1, 5)

        detections = []
        for _ in range(num_vehicles):
            vtype = random.choice(vehicle_types)
            detections.append({
                "class": vtype,
                "bbox": (random.randint(0, 800), random.randint(0, 400),
                         random.randint(80, 200), random.randint(60, 120)),
                "confidence": round(random.uniform(0.80, 0.99), 2),
                "color": self.COLORS.get(vtype, (255, 255, 255)),
            })
        for _ in range(num_persons):
            detections.append({
                "class": "Person",
                "bbox": (random.randint(0, 900), random.randint(0, 500),
                         random.randint(40, 80), random.randint(80, 160)),
                "confidence": round(random.uniform(0.75, 0.99), 2),
                "color": self.COLORS.get("Person", (255, 255, 255)),
            })

        processing_ms = random.uniform(15, 35)
        time.sleep(processing_ms / 1000)

        vehicles = [d for d in detections if d["class"] != "Person"]
        persons = [d for d in detections if d["class"] == "Person"]

        return {
            "detections": detections,
            "vehicle_count": len(vehicles),
            "person_count": len(persons),
            "vehicles": vehicles,
            "persons": persons,
            "processing_time_ms": round(processing_ms, 1),
            "fps": round(1000 / max(processing_ms, 1), 1),
            "simulated": True,
        }

    def get_vehicle_type_breakdown(self, detections: list) -> dict:
        """Count vehicles by type"""
        breakdown = {}
        for det in detections:
            vtype = det["class"]
            breakdown[vtype] = breakdown.get(vtype, 0) + 1
        return breakdown
