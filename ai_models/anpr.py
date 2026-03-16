"""
AI Models - ANPR (Automatic Number Plate Recognition)
CyberShield Video Analytics System

Uses EasyOCR to read license plates from vehicle detections.
Falls back to simulated results if not available.
"""

import re
import random
import numpy as np
from pathlib import Path


SIMULATED_PLATES = [
    "TN01AB1234", "TN02CD5678", "TN03EF9012", "TN04GH3456",
    "TN05IJ7890", "TN06KL2345", "TN07MN6789", "TN08OP1234",
    "TN09QR5678", "TN10ST9012", "KA01MF3456", "MH12DE1433",
]

INDIAN_PLATE_PATTERN = re.compile(
    r'^[A-Z]{2}\d{2}[A-Z]{1,2}\d{4}$'
)


class ANPRDetector:
    """Automatic Number Plate Recognition using EasyOCR"""

    def __init__(self, languages: list = None):
        self.languages = languages or ["en"]
        self.reader = None
        self.available = False
        self._load_reader()

    def _load_reader(self):
        try:
            import easyocr
            self.reader = easyocr.Reader(self.languages, gpu=False, verbose=False)
            self.available = True
            print("✅ EasyOCR ANPR reader loaded")
        except ImportError:
            print("⚠️ easyocr not installed — ANPR in simulation mode")
        except Exception as e:
            print(f"⚠️ Error loading EasyOCR: {e} — ANPR in simulation mode")

    def extract_plate(self, frame: np.ndarray, vehicle_bbox: tuple = None) -> dict:
        """
        Extract license plate from a frame or vehicle ROI.
        vehicle_bbox: (x, y, w, h)
        """
        if self.available and self.reader is not None:
            return self._real_extract(frame, vehicle_bbox)
        else:
            return self._simulated_extract()

    def _real_extract(self, frame, vehicle_bbox):
        import cv2
        try:
            if vehicle_bbox:
                x, y, w, h = vehicle_bbox
                roi = frame[max(0, y):y + h, max(0, x):x + w]
            else:
                roi = frame

            # Convert to grayscale for better OCR
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

            results = self.reader.readtext(gray)
            best_plate = None
            best_conf = 0

            for bbox, text, conf in results:
                # Clean text
                cleaned = re.sub(r'[^A-Z0-9]', '', text.upper())

                # Validate Indian plate format
                if INDIAN_PLATE_PATTERN.match(cleaned) and conf > best_conf:
                    best_plate = cleaned
                    best_conf = conf

            return {
                "plate": best_plate,
                "confidence": round(best_conf, 2),
                "raw_text": [r[1] for r in results],
                "detected": best_plate is not None,
            }
        except Exception as e:
            print(f"Error in ANPR extraction: {e}")
            return self._simulated_extract()

    def _simulated_extract(self):
        """Simulate ANPR detection"""
        # 80% chance of successful detection
        if random.random() < 0.80:
            plate = random.choice(SIMULATED_PLATES)
            return {
                "plate": plate,
                "confidence": round(random.uniform(0.82, 0.99), 2),
                "raw_text": [plate],
                "detected": True,
                "simulated": True,
            }
        return {
            "plate": None,
            "confidence": 0.0,
            "raw_text": [],
            "detected": False,
            "simulated": True,
        }

    def validate_plate(self, plate: str) -> bool:
        """Validate Indian license plate format"""
        if not plate:
            return False
        cleaned = re.sub(r'[^A-Z0-9]', '', plate.upper())
        return bool(INDIAN_PLATE_PATTERN.match(cleaned))

    def format_plate(self, plate: str) -> str:
        """Clean and format a license plate string"""
        cleaned = re.sub(r'[^A-Z0-9]', '', plate.upper())
        # Format: XX00XX0000
        if len(cleaned) == 10:
            return f"{cleaned[:2]}{cleaned[2:4]}{cleaned[4:6]}{cleaned[6:]}"
        return cleaned
