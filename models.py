import streamlit as st
import torch
import cv2
import os
from ultralytics import YOLO
from rfdetr import Inferencer
import easyocr
from config import HAS_CUDA, DEVICE


@st.cache_resource(show_spinner=False)
def load_rtdetr_light():
    return Inferencer(model="rfdetr-l", device=DEVICE)

@st.cache_resource(show_spinner=False)
def load_ocr():
    return easyocr.Reader(['en'], gpu=HAS_CUDA)

@st.cache_resource(show_spinner=False)
def load_face_cascade():
    return cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_alt2.xml")

@st.cache_resource(show_spinner=False)
def load_crash_model():
    m = torch.jit.load("edge_crash_classifier_scripted.pt", map_location=DEVICE)
    m.eval()
    return m

@st.cache_resource(show_spinner=False)
def load_gender_net():
    proto = cv2.data.haarcascades + "../gender_deploy.prototxt" if os.path.exists(cv2.data.haarcascades + "../gender_deploy.prototxt") else None
    if proto and os.path.exists(proto.replace(".prototxt", ".caffemodel")):
        net = cv2.dnn.readNetFromCaffe(proto, proto.replace(".prototxt", ".caffemodel"))
        return net
    return None
