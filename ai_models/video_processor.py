"""
Video Processor — Frame Extraction + Roboflow Inference
CyberShield AI Video Analytics

Extracts frames from uploaded video files and sends each frame
to the Roboflow workflow for AI analysis. Aggregates results
into structured analytics.
"""

import os
import cv2
import tempfile
import random
from pathlib import Path
from datetime import datetime
from typing import Generator
from collections import defaultdict

from ai_models.roboflow_client import roboflow_client

# ─── Config ───────────────────────────────────────────────────────────────────
UPLOAD_DIR = Path(__file__).parent.parent / "uploads" / "videos"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

SUPPORTED_FORMATS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
FRAME_SAMPLE_RATE = int(os.getenv("FRAME_SAMPLE_RATE", "30"))  # every Nth frame


# ─── Frame Extraction ─────────────────────────────────────────────────────────
def extract_frames(video_path: str, sample_rate: int = FRAME_SAMPLE_RATE) -> Generator:
    """
    Generator that yields (frame_number, frame_bytes, timestamp_sec) for every
    Nth frame in the video.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_number = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_number % sample_rate == 0:
            # Encode frame to JPEG bytes
            ret_enc, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if ret_enc:
                timestamp = frame_number / fps
                yield frame_number, buffer.tobytes(), timestamp, total_frames

        frame_number += 1

    cap.release()


def get_video_info(video_path: str) -> dict:
    """Get basic metadata from a video file."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return {}
    info = {
        "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        "fps": cap.get(cv2.CAP_PROP_FPS),
        "total_frames": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
        "duration_sec": int(cap.get(cv2.CAP_PROP_FRAME_COUNT) / max(cap.get(cv2.CAP_PROP_FPS), 1)),
    }
    cap.release()
    return info


# ─── Roboflow Video Analysis ──────────────────────────────────────────────────
def analyze_video(video_path: str, sample_rate: int = FRAME_SAMPLE_RATE,
                  max_frames: int = 50, progress_callback=None) -> dict:
    """
    Full video analysis pipeline:
    1. Extract frames from video
    2. Send each frame to Roboflow inference API
    3. Aggregate detections into analytics

    Returns:
        dict with frame_results, class_counts, confidence_timeline, summary
    """
    info = get_video_info(video_path)
    frame_results = []
    class_counts = defaultdict(int)
    total_frames_processed = 0
    total_detections = 0
    frames_with_detections = 0

    try:
        for frame_num, frame_bytes, timestamp, total_frames in extract_frames(video_path, sample_rate):
            if total_frames_processed >= max_frames:
                break

            result = roboflow_client.infer_image(frame_bytes)

            frame_data = {
                "frame_number": frame_num,
                "timestamp_sec": round(timestamp, 2),
                "timestamp_str": f"{int(timestamp // 60):02d}:{int(timestamp % 60):02d}",
                "success": result["success"],
                "predictions": result.get("predictions", []),
                "detection_count": len(result.get("predictions", [])),
                "simulated": result.get("simulated", False),
            }

            # Count classes
            for pred in result.get("predictions", []):
                class_counts[pred["class"]] += 1
                total_detections += 1

            if frame_data["detection_count"] > 0:
                frames_with_detections += 1

            frame_results.append(frame_data)
            total_frames_processed += 1

            if progress_callback:
                progress = total_frames_processed / min(max_frames, total_frames // sample_rate + 1)
                progress_callback(min(progress, 1.0))

    except Exception as e:
        return {"success": False, "error": str(e), "frame_results": [], "class_counts": {}, "summary": {}}

    # Build analytics summary
    summary = {
        "video_path": str(video_path),
        "filename": Path(video_path).name,
        "analyzed_at": datetime.now().isoformat(),
        "video_info": info,
        "frames_processed": total_frames_processed,
        "frames_with_detections": frames_with_detections,
        "total_detections": total_detections,
        "detection_rate": round(frames_with_detections / max(total_frames_processed, 1) * 100, 1),
        "unique_classes": len(class_counts),
        "top_class": max(class_counts, key=class_counts.get) if class_counts else "none",
        "roboflow_connected": roboflow_client.configured,
    }

    return {
        "success": True,
        "frame_results": frame_results,
        "class_counts": dict(class_counts),
        "summary": summary,
    }


# ─── Simulated fallback (when Roboflow is not configured) ─────────────────────
SIMULATED_CLASSES = [
    "person", "car", "motorcycle", "bus", "truck",
    "violence", "weapon", "suspicious_bag", "crowd",
]

def simulate_video_analysis(filename: str, duration_sec: int = 60) -> dict:
    """
    Generate realistic-looking simulated analysis results when
    Roboflow is not configured — useful for demo/hackathon.
    """
    total_frames = max(5, duration_sec // 2)
    frame_results = []
    class_counts = defaultdict(int)

    for i in range(total_frames):
        timestamp = i * (duration_sec / total_frames)
        num_detections = random.choices([0, 1, 2, 3, 4, 5], weights=[15, 30, 25, 15, 10, 5])[0]
        predictions = []
        for _ in range(num_detections):
            cls = random.choice(SIMULATED_CLASSES)
            conf = round(random.uniform(0.60, 0.99), 2)
            predictions.append({"class": cls, "confidence": conf,
                                 "x": random.randint(50, 900), "y": random.randint(50, 500),
                                 "width": random.randint(40, 200), "height": random.randint(40, 200)})
            class_counts[cls] += 1

        frame_results.append({
            "frame_number": i * 30,
            "timestamp_sec": round(timestamp, 2),
            "timestamp_str": f"{int(timestamp // 60):02d}:{int(timestamp % 60):02d}",
            "success": True,
            "predictions": predictions,
            "detection_count": num_detections,
            "simulated": True,
        })

    total_detections = sum(class_counts.values())
    frames_with_det = sum(1 for f in frame_results if f["detection_count"] > 0)

    summary = {
        "filename": filename,
        "analyzed_at": datetime.now().isoformat(),
        "video_info": {"width": 1920, "height": 1080, "fps": 30.0,
                       "total_frames": total_frames * 30, "duration_sec": duration_sec},
        "frames_processed": total_frames,
        "frames_with_detections": frames_with_det,
        "total_detections": total_detections,
        "detection_rate": round(frames_with_det / max(total_frames, 1) * 100, 1),
        "unique_classes": len(class_counts),
        "top_class": max(class_counts, key=class_counts.get) if class_counts else "none",
        "roboflow_connected": False,
        "simulated": True,
    }

    return {
        "success": True,
        "frame_results": frame_results,
        "class_counts": dict(class_counts),
        "summary": summary,
    }
