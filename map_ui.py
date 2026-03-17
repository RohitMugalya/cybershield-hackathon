import streamlit as st
import pydeck as pdk
import pandas as pd
import numpy as np
import requests
import random
from config import CAMERAS, DEVICE_LABEL

# ─── Chennai Zone Name Pools ───────────────────────────────────────────────────

ZONE_NAMES = {
    "anna_nagar": [
        "Anna Nagar Tower Block", "Shanthi Colony Complex", "Thirumangalam Plaza",
        "KK Nagar Civic Centre", "Arumbakkam Trade Hub", "Vadapalani Signal Block",
        "Anna Nagar West Residency", "Aminjikarai Commercial Block", "Choolaimedu Market Tower",
        "Shenoy Nagar Junction Block", "Anna Arch Annex", "Ayyapanthangal IT Park"
    ],
    "perungudi": [
        "Sholinganallur Tech Corridor", "Perungudi OMR Tower", "Karapakkam Business Hub",
        "Kandanchavadi Complex", "Neelankarai Residential Block", "Pallikaranai Marshland View",
        "Thoraipakkam IT Spine", "Kottivakkam Shoreline Tower", "Perumbakkam Housing Block",
        "Navalur Software Park", "Siruseri SIPCOT Block", "Sholinganallur Junction Plaza"
    ],
    "ambattur": [
        "Ambattur Industrial Estate Block", "Padi Junction Complex", "Villivakkam Trade Tower",
        "Kolathur Residential Hub", "Madhavaram Market Block", "Redhills Reservoir View",
        "Ambattur OT Signal Block", "Purasawalkam Commercial Strip", "Korattur Civic Hall",
        "Ayapakkam Agri Hub", "Thiruvottiyur Port Block", "Manali Refinery View Tower"
    ],
    "guindy": [
        "Guindy Industrial Estate Block", "Ashok Nagar Civil Complex", "St. Thomas Mount View",
        "Chromepet Hub Tower", "Pallavaram Commercial Block", "Nanganallur Residential Annex",
        "Alandur Metro Exchange", "Saidapet Bridge Complex", "Ekkatuthangal Trade Block",
        "Velachery Signal Tower", "Adambakkam Market Block", "Kathipara Junction Plaza"
    ],
    "vadapalani": [
        "Vadapalani Film Chamber", "Kodambakkam Studio Block", "Virugambakkam Commercial Hub",
        "Koyambedu CMBT Complex", "Nerkundram Residential Block", "Valasaravakkam Township",
        "Porur IT Corridor Tower", "Alwarthirunagar Civic Block", "Mugalivakkam SEZ Annex",
        "Kundrathur Village Gate", "Kolapakkam Gated Tower", "Mangadu Temple View Block"
    ]
}

ZONE_HUBS = [
    ((13.0418, 80.2341), "anna_nagar"),
    ((13.0012, 80.2565), "perungudi"),
    ((13.0850, 80.2101), "ambattur"),
    ((12.9815, 80.2180), "guindy"),
    ((13.0063, 80.2006), "vadapalani"),
]

def get_zone_for_coord(lat, lon):
    """Return zone key for the nearest hub to given coordinates."""
    min_dist = float("inf")
    zone = "anna_nagar"
    for (hlat, hlon), zname in ZONE_HUBS:
        dist = (lat - hlat) ** 2 + (lon - hlon) ** 2
        if dist < min_dist:
            min_dist = dist
            zone = zname
    return zone

def assign_building_name(lat, lon, index, used_names):
    """Pick a unique name from the zone pool closest to this building."""
    zone = get_zone_for_coord(lat, lon)
    pool = ZONE_NAMES[zone]
    # Cycle through pool with index offset to avoid always picking first
    for i in range(len(pool)):
        candidate = pool[(index + i) % len(pool)]
        key = f"{zone}:{candidate}"
        if key not in used_names:
            used_names.add(key)
            return candidate
    # Fallback: zone label + index
    return f"{zone.replace('_', ' ').title()} Block {index}"


# ─── OSM Building Fetch ────────────────────────────────────────────────────────

@st.cache_data(ttl=86400, show_spinner=False)
def fetch_osm_buildings(lat_min, lon_min, lat_max, lon_max):
    query = f'[out:json][timeout:60];(way["building"]({lat_min},{lon_min},{lat_max},{lon_max}););out body geom;'
    try:
        r = requests.post(
            "https://overpass-api.de/api/interpreter",
            data={"data": query}, timeout=90,
            headers={"User-Agent": "CyberShieldProfessional/2.0"}
        )
        r.raise_for_status()
        buildings = []
        used_names = set()
        for idx, el in enumerate(r.json().get("elements", [])):
            if el.get("type") != "way" or len(el.get("geometry", [])) < 3:
                continue
            coords = [[p["lon"], p["lat"]] for p in el.get("geometry", [])]
            tags = el.get("tags", {})

            # Height
            h = tags.get("height", tags.get("building:levels", ""))
            try:
                if ":" in str(h): h = 10.5
                h = float(str(h).replace("m", "").strip()) * 3.5 if h else 10.5
            except:
                h = 10.5
            h = max(3.5, min(float(h), 500.0))

            color = [20, 40, 60, 180] if h < 20 else [30, 80, 120, 200]

            # Centroid for zone detection
            lats = [p["lat"] for p in el.get("geometry", [])]
            lons = [p["lon"] for p in el.get("geometry", [])]
            clat, clon = sum(lats) / len(lats), sum(lons) / len(lons)

            # Use OSM name tag if available, else assign from zone pool
            name = tags.get("name") or tags.get("addr:housename") or assign_building_name(clat, clon, idx, used_names)

            buildings.append({
                "polygon": coords,
                "height": round(h, 1),
                "color": color,
                "name": name
            })
        return buildings, len(buildings)
    except Exception as e:
        print(f"OSM Error: {e}")
        return [], 0


# ─── Fallback Buildings ────────────────────────────────────────────────────────

def gen_fallback_buildings():
    hubs = [
        (13.0418, 80.2341, "anna_nagar"),
        (13.0012, 80.2565, "perungudi"),
        (13.0850, 80.2101, "ambattur"),
        (12.9815, 80.2180, "guindy"),
        (13.0063, 80.2006, "vadapalani"),
    ]
    blds = []
    step, sz = 0.0006, 0.0004
    np.random.seed(42)
    used_names = set()
    idx = 0

    for hub_lat, hub_lon, zone in hubs:
        pool = ZONE_NAMES[zone]
        pool_idx = 0
        for i in range(-5, 5):
            for j in range(-5, 5):
                if random.random() < 0.25:
                    continue
                blat = hub_lat + i * step
                blon = hub_lon + j * step
                h = np.random.exponential(40) + 10
                c = [
                    max(10, int(25 - h * 0.1)),
                    min(200, int(h * 1.2)),
                    min(255, int(h * 1.5 + 50)),
                    180
                ]

                # Pick name from zone pool, cycling through it
                name = pool[pool_idx % len(pool)]
                pool_idx += 1

                blds.append({
                    "polygon": [
                        [blon, blat], [blon + sz, blat],
                        [blon + sz, blat + sz], [blon, blat + sz],
                        [blon, blat]
                    ],
                    "height": h,
                    "color": c,
                    "building_type": "procedural",
                    "name": name
                })
                idx += 1
    return blds


# ─── Map Renderer ─────────────────────────────────────────────────────────────

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
            "lat": c["lat"], "lon": c["lon"],
            "name": f"SITE: {c['name']}", "id": c["id"],
            "color": [255, 0, 0, 255] if is_alert else [0, 243, 255, 200],
            "radius": 45 if is_alert else 25
        })
    df_c = pd.DataFrame(cam_data)

    bld_layer = pdk.Layer(
        'PolygonLayer', data=df_b,
        get_polygon='polygon', get_elevation='height',
        elevation_scale=1, get_fill_color='color',
        extruded=True, pickable=True  # ← enabled so tooltip shows name
    )

    cam_layer = pdk.Layer(
        'ScatterplotLayer', data=df_c,
        get_position='[lon, lat]', get_radius='radius',
        get_fill_color='color', pickable=True,
        auto_highlight=True, stroked=True,
        get_line_color=[0, 243, 255, 255], line_width_min_pixels=2
    )

    view = pdk.ViewState(latitude=13.04, longitude=80.23, zoom=11.5, pitch=50, bearing=-10)

    tooltip = {
        "html": """
            <b>{name}</b><br/>
            <span style='color:#00f3ff; font-size:11px;'>
                {building_type}
            </span>
        """,
        "style": {
            "backgroundColor": "#050a0f",
            "color": "#ffffff",
            "border": "1px solid #00f3ff",
            "fontSize": "13px",
            "padding": "6px 10px"
        }
    }

    deck = pdk.Deck(
        layers=[bld_layer, cam_layer],
        initial_view_state=view,
        tooltip=tooltip,
        map_style=pdk.map_styles.DARK
    )
    st.pydeck_chart(deck, width="stretch")

    st.markdown(
        f"<div style='text-align:right; font-size:10px; color:#444;'>"
        f"Nodes: 6 | City Mesh: {bc} segments | Engine: {DEVICE_LABEL}</div>",
        unsafe_allow_html=True
    )
