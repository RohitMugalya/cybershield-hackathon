"""
Roboflow Inference Client
CyberShield — AI Video Analytics

Sends frames / images to your Roboflow deployment workflow endpoint
and returns structured detection results.

Set these in your .env file:
    ROBOFLOW_API_KEY=your_key_here
    ROBOFLOW_WORKSPACE=your_workspace_slug
    ROBOFLOW_WORKFLOW_URL=https://detect.roboflow.com/infer/workflows/your_workspace/your_workflow
"""

import os
import base64
import json
import requests
from pathlib import Path
from typing import Optional


# ─── Load from environment ────────────────────────────────────────────────────
ROBOFLOW_API_KEY = os.getenv("ROBOFLOW_API_KEY", "")
ROBOFLOW_WORKSPACE = os.getenv("ROBOFLOW_WORKSPACE", "")
ROBOFLOW_WORKFLOW_URL = os.getenv(
    "ROBOFLOW_WORKFLOW_URL",
    ""  # e.g. https://detect.roboflow.com/infer/workflows/my-workspace/cybershield-workflow
)


class RoboflowClient:
    """
    Client for calling Roboflow hosted workflow inference API.
    The workflow URL is obtained from Roboflow → Deploy → Get Deployment Link.
    """

    def __init__(
        self,
        api_key: str = ROBOFLOW_API_KEY,
        workflow_url: str = ROBOFLOW_WORKFLOW_URL,
    ):
        self.api_key = api_key
        self.workflow_url = workflow_url
        self.configured = bool(api_key and workflow_url)

    def _encode_image(self, image_path: str) -> str:
        """Encode image file to base64 string."""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def _encode_image_bytes(self, image_bytes: bytes) -> str:
        """Encode raw image bytes to base64 string."""
        return base64.b64encode(image_bytes).decode("utf-8")

    def infer_image(self, image_source) -> dict:
        """
        Run inference on a single image.

        Args:
            image_source: Path string, Path object, or raw bytes of an image

        Returns:
            dict with keys: success, predictions, raw_response, error
        """
        if not self.configured:
            return {
                "success": False,
                "predictions": [],
                "raw_response": None,
                "error": "Roboflow not configured. Set ROBOFLOW_API_KEY and ROBOFLOW_WORKFLOW_URL in .env",
                "simulated": True,
            }

        try:
            # Encode image
            if isinstance(image_source, (str, Path)):
                image_b64 = self._encode_image(str(image_source))
            elif isinstance(image_source, bytes):
                image_b64 = self._encode_image_bytes(image_source)
            else:
                # Assume it's a file-like object (Streamlit UploadedFile etc.)
                image_b64 = self._encode_image_bytes(image_source.read())

            payload = {
                "api_key": self.api_key,
                "inputs": {
                    "image": {"type": "base64", "value": image_b64},
                },
            }

            response = requests.post(
                self.workflow_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()

            # Parse predictions from Roboflow response
            predictions = self._parse_predictions(result)
            return {
                "success": True,
                "predictions": predictions,
                "raw_response": result,
                "error": None,
                "simulated": False,
            }

        except requests.exceptions.ConnectionError:
            return {"success": False, "predictions": [], "error": "Cannot connect to Roboflow. Check your network.", "simulated": False}
        except requests.exceptions.Timeout:
            return {"success": False, "predictions": [], "error": "Roboflow request timed out.", "simulated": False}
        except requests.exceptions.HTTPError as e:
            return {"success": False, "predictions": [], "error": f"Roboflow API error: {e}", "simulated": False}
        except Exception as e:
            return {"success": False, "predictions": [], "error": str(e), "simulated": False}

    def _parse_predictions(self, result: dict) -> list:
        """
        Parse the Roboflow workflow response into a flat list of predictions.
        Handles both single-model and workflow (multi-step) response formats.
        """
        # Workflow response format
        if "outputs" in result:
            predictions = []
            for output in result.get("outputs", []):
                if isinstance(output, dict):
                    preds = output.get("predictions", {})
                    if isinstance(preds, dict):
                        for item in preds.get("predictions", []):
                            predictions.append({
                                "class": item.get("class", "unknown"),
                                "confidence": item.get("confidence", 0.0),
                                "x": item.get("x", 0),
                                "y": item.get("y", 0),
                                "width": item.get("width", 0),
                                "height": item.get("height", 0),
                            })
            return predictions

        # Direct model response format
        if "predictions" in result:
            preds = result["predictions"]
            if isinstance(preds, list):
                return [
                    {
                        "class": p.get("class", "unknown"),
                        "confidence": p.get("confidence", 0.0),
                        "x": p.get("x", 0),
                        "y": p.get("y", 0),
                        "width": p.get("width", 0),
                        "height": p.get("height", 0),
                    }
                    for p in preds
                ]

        return []

    def check_connection(self) -> dict:
        """Test if Roboflow is reachable and credentials are valid."""
        if not self.configured:
            return {"connected": False, "reason": "API key or Workflow URL not set in .env"}
        try:
            # Lightweight check using Roboflow API
            resp = requests.get(
                f"https://api.roboflow.com/?api_key={self.api_key}",
                timeout=5,
            )
            if resp.status_code == 200:
                return {"connected": True, "workspace": self.api_key[:8] + "..."}
            return {"connected": False, "reason": f"HTTP {resp.status_code}"}
        except Exception as e:
            return {"connected": False, "reason": str(e)}


# ─── Singleton instance ────────────────────────────────────────────────────────
roboflow_client = RoboflowClient()
