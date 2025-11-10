# core/geo_utils.py (ฉบับเต็ม - สร้างใหม่)

import json
from shapely.geometry import shape, Point
from typing import List

# --- 1. นี่คือโค้ดที่คุณให้มา (ผมปรับแต่งเล็กน้อย) ---

# (ใช้ Path() เพื่อให้หาไฟล์เจอไม่ว่าจะรันจากที่ไหน)
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent # (ชี้ไปที่ bma_project/)
GEOJSON_FILE = BASE_DIR / "bangkok_districts.geojson" 

BKK_DISTRICTS_GEOMETRY = [] # (เก็บ (ชื่อเขต, รูปทรง) )

def load_geojson_polygons():
    """
    โหลดไฟล์ GeoJSON (แผนที่ 50 เขต) เข้าสู่ Memory
    """
    global BKK_DISTRICTS_GEOMETRY
    BKK_DISTRICTS_GEOMETRY.clear()
    try:
        with open(GEOJSON_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if "features" not in data:
            raise ValueError("GeoJSON file missing 'features' key")

        for feature in data["features"]:
            geometry = shape(feature["geometry"])
            props = feature.get("properties", {})

            # (ใช้ Logic การหาชื่อเขตที่คุณให้มา)
            district_name = (
                props.get("dname") or 
                props.get("dname_th") or
                props.get("name") or
                props.get("amphoe_th") or 
                props.get("DISTRICT_T") or
                "ไม่ทราบชื่อเขต"
            )

            BKK_DISTRICTS_GEOMETRY.append((district_name, geometry))

        print(f"✅ [Geo-Utils] Loaded {len(BKK_DISTRICTS_GEOMETRY)} districts successfully. Geo-Routing is active.")
        
    except FileNotFoundError:
        print(f"⚠️ WARNING: [Geo-Utils] {GEOJSON_FILE} not found. Geo-Routing will NOT work.")
    except Exception as e:
        print(f"❌ ERROR: [Geo-Utils] Error loading GeoJSON: {e}")

def get_district_from_coords(lat: float, lon: float) -> str:
    """
    ฟังก์ชัน Geo-Routing (Point in Polygon)
    ค้นหาว่า (lat, lon) นี้ อยู่ในเขตใด
    """
    if not BKK_DISTRICTS_GEOMETRY:
        return "รอฐานข้อมูลเขต" # (สถานะเริ่มต้น)
        
    point = Point(lon, lat) # (Shapely ใช้ (lon, lat))
    
    for district_name, geometry in BKK_DISTRICTS_GEOMETRY:
        if point.within(geometry):
            return district_name # (เช่น "เขตปทุมวัน")
            
    return "นอกเขต กทม." # (ถ้าหาไม่เจอ)

# --- (ส่วน AI Triage เราจะยังไม่ใช้ตอนนี้) ---
# def ai_triage_and_route(...):
#    ...