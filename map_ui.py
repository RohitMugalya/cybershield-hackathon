import streamlit as st
import pydeck as pdk
import pandas as pd
import numpy as np
import requests
import random
from config import CAMERAS, DEVICE_LABEL

@st.cache_data(ttl=86400, show_spinner=False)
def fetch_osm_buildings(lat_min, lon_min, lat_max, lon_max):
    query = f'[out:json][timeout:60];(way["building"]({lat_min},{lon_min},{lat_max},{lon_max}););out body geom;'
    try:
        r = requests.post("https://overpass-api.de/api/interpreter", data={"data": query}, timeout=90, headers={"User-Agent": "CyberShieldProfessional/2.0"})
        r.raise_for_status()
        buildings = []
        for el in r.json().get("elements", []):
            if el.get("type") != "way" or len(el.get("geometry", [])) < 3: continue
            coords = [[p["lon"], p["lat"]] for p in el.get("geometry", [])]
            tags = el.get("tags", {})
            h = tags.get("height", tags.get("building:levels", ""))
            try:
                if ":" in str(h): h = 10.5
                h = float(str(h).replace("m","").strip()) * 3.5 if h else 10.5
            except: h = 10.5
            
            h = max(3.5, min(float(h), 500.0))
            color = [20, 40, 60, 180] if h < 20 else [30, 80, 120, 200]
            buildings.append({"polygon": coords, "height": round(h,1), "color": color})
        return buildings, len(buildings)
    except Exception as e:
        print(f"OSM Error: {e}")
        return [], 0

def gen_fallback_buildings():
    hubs = [(13.0418,80.2341),(13.0012,80.2565),(13.0850,80.2101),(12.9815,80.2180),(13.0063,80.2006)]
    blds = []; step, sz = 0.0006, 0.0004; np.random.seed(42)
    for hub in hubs:
        for i in range(-5,5):
            for j in range(-5,5):
                if random.random() < 0.25: continue
                blat, blon = hub[0]+i*step, hub[1]+j*step
                h = np.random.exponential(40)+10
                c = [max(10,int(25-h*0.1)), min(200,int(h*1.2)), min(255,int(h*1.5+50)), 180]
                blds.append({"polygon":[[blon,blat],[blon+sz,blat],[blon+sz,blat+sz],[blon,blat+sz],[blon,blat]],"height":h,"color":c,"building_type":"procedural","name":"Block"})
    return blds

def render_map():
    buildings, bc = fetch_osm_buildings(13.00, 80.20, 13.08, 80.28)
    if bc == 0:
        buildings = gen_fallback_buildings()
    df_b = pd.DataFrame(buildings)

    alerts = st.session_state.get("cam_alerts", {})
    cam_data = []
    for c in CAMERAS:
        is_alert = alerts.get(c["id"], False)
        cam_data.append({
            "lat": c["lat"], "lon": c["lon"], "name": f"SITE: {c['name']}", "id": c["id"],
            "color": [255, 0, 0, 255] if is_alert else [0, 243, 255, 200],
            "radius": 45 if is_alert else 25
        })
    df_c = pd.DataFrame(cam_data)

    bld_layer = pdk.Layer('PolygonLayer', data=df_b, get_polygon='polygon', get_elevation='height',
                          elevation_scale=1, get_fill_color='color', extruded=True, pickable=False)
    
    cam_layer = pdk.Layer('ScatterplotLayer', data=df_c, get_position='[lon, lat]', get_radius='radius',
                          get_fill_color='color', pickable=True, auto_highlight=True, stroked=True,
                          get_line_color=[0, 243, 255, 255], line_width_min_pixels=2)

    view = pdk.ViewState(latitude=13.04, longitude=80.23, zoom=11.5, pitch=50, bearing=-10)
    tooltip = {"html": "<b>{name}</b><br/>Status: <span style='color:#00f3ff'>ONLINE</span>", 
               "style": {"backgroundColor": "#050a0f", "color": "#ffffff", "border": "1px solid #00f3ff"}}
    
    deck = pdk.Deck(layers=[bld_layer, cam_layer], initial_view_state=view, tooltip=tooltip, map_style=pdk.map_styles.DARK)
    st.pydeck_chart(deck, width="stretch")

    st.markdown(f"<div style='text-align:right; font-size:10px; color:#444;'>Nodes: 6 | City Mesh: {bc} segments | Engine: {DEVICE_LABEL}</div>", unsafe_allow_html=True)
