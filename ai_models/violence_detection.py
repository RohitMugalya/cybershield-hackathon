"""
AI Models - Violence Detection
CyberShield Video Analytics System

Detects violent activity in video frames using a pretrained CNN model.
Falls back to simulation mode if model not available.
"""

import time
import random
import numpy as np
from pathlib import Path
from datetime import datetime


class ViolenceDetector:
    """Violence detection using pretrained CNN model"""

    VIOLENCE_LABELS = ["Non-Violence", "Violence"]
    THRESHOLD = 0.90

    def __init__(self, model_path: str = "models/violence_detection.pt"):
        self.model_path = model_path
        self.model = None
        self.available = False
        self._load_model()

    def _load_model(self):
        try:
            import torch
            if Path(self.model_path).exists():
                self.model = torch.load(self.model_path, map_location="cpu")
                self.model.eval()
                self.available = True
                print(f"✅ Violence detection model loaded: {self.model_path}")
            else:
                print(f"⚠️ Violence model not found at {self.model_path} — using simulation mode")
        except ImportError:
            print("⚠️ PyTorch not installed — violence detection in simulation mode")
        except Exception as e:
            print(f"⚠️ Error loading violence model: {e} — using simulation mode")

    def detect(self, frame: np.ndarray) -> dict:
        """
        Detect violence in a single frame.
        Returns:
          - is_violent: bool
          - confidence: float
          - label: str
          - processing_time_ms: float
        """
        start = time.time()

        if self.available and self.model is not None:
            return self._real_detect(frame, start)
        else:
            return self._simulated_detect(start)

    def _real_detect(self, frame, start_time):
        import torch
        import torchvision.transforms as transforms
        from PIL import Image

        transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

        img = Image.fromarray(frame)
        tensor = transform(img).unsqueeze(0)

        with torch.no_grad():
            output = self.model(tensor)
            probs = torch.softmax(output, dim=1).squeeze().numpy()

        violence_conf = float(probs[1])
        is_violent = violence_conf >= self.THRESHOLD
        processing_ms = (time.time() - start_time) * 1000

        return {
            "is_violent": is_violent,
            "confidence": round(violence_conf, 3),
            "label": "Violence" if is_violent else "Non-Violence",
            "processing_time_ms": round(processing_ms, 1),
        }

    def _simulated_detect(self, start_time):
        """Simulate violence detection for demo"""
        processing_ms = random.uniform(10, 30)
        time.sleep(processing_ms / 1000)

        # 5% chance of detecting violence in simulation
        if random.random() < 0.05:
            conf = round(random.uniform(0.90, 0.99), 3)
            return {
                "is_violent": True,
                "confidence": conf,
                "label": "Violence",
                "persons_involved": random.randint(2, 5),
                "processing_time_ms": round(processing_ms, 1),
                "simulated": True,
            }
        return {
            "is_violent": False,
            "confidence": round(random.uniform(0.01, 0.15), 3),
            "label": "Non-Violence",
            "persons_involved": 0,
            "processing_time_ms": round(processing_ms, 1),
            "simulated": True,
        }

    def analyze_sequence(self, frames: list) -> dict:
        """
        Analyze a sequence of frames for violence detection.
        Returns aggregated result across the sequence.
        """
        results = [self.detect(f) for f in frames]
        max_conf = max(r["confidence"] for r in results)
        violent_frames = sum(1 for r in results if r["is_violent"])

        return {
            "is_violent": violent_frames > len(frames) * 0.3,
            "max_confidence": max_conf,
            "violent_frames": violent_frames,
            "total_frames": len(frames),
            "results": results,
        }
