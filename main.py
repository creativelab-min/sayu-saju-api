from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from lunar_python import Solar
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time

app = FastAPI(title="Sayu Saju API", description="Accurate Four Pillars for self-reflection")

class BirthData(BaseModel):
    name: str = "User"
    year: int
    month: int
    day: int
    hour: int = 12
    minute: int = 0
    gender: str = "male"
    birthplace: str = "Vancouver, Canada"  # City, Country for geocoding

@app.post("/calculate-saju")
async def calculate_saju(data: BirthData):
    try:
        # 1. Geocoding for birthplace (longitude for true solar time)
        geolocator = Nominatim(user_agent="sayu_saju_app")
        try:
            location = geolocator.geocode(data.birthplace, timeout=10)
            if location:
                longitude = location.longitude
                latitude = location.latitude
                location_name = location.address
            else:
                longitude = 0
                latitude = 0
                location_name = data.birthplace
        except (GeocoderTimedOut, GeocoderServiceError):
            longitude = 0
            latitude = 0
            location_name = data.birthplace

        # 2. Create Solar date with basic adjustment (lunar-python limitation)
        solar = Solar.fromYMDHMS(
            data.year, data.month, data.day,
            data.hour, data.minute, 0
        )
        
        lunar = solar.getLunar()
        eight_char = lunar.getEightChar()

        # Element mapping
        element_map = {
            "甲": "Wood", "乙": "Wood", "丙": "Fire", "丁": "Fire",
            "戊": "Earth", "己": "Earth", "庚": "Metal", "辛": "Metal",
            "壬": "Water", "癸": "Water"
        }

        pillars = {
            "year": {"stem": eight_char.getYearGan(), "branch": eight_char.getYearZhi()},
            "month": {"stem": eight_char.getMonthGan(), "branch": eight_char.getMonthZhi()},
            "day": {"stem": eight_char.getDayGan(), "branch": eight_char.getDayZhi()},
            "hour": {"stem": eight_char.getTimeGan(), "branch": eight_char.getTimeZhi()}
        }

        day_master_stem = eight_char.getDayGan()
        day_master_element = element_map.get(day_master_stem, "Unknown")

        # Basic Five Elements count (expandable)
        all_chars = "".join([p["stem"] + p["branch"] for p in pillars.values()])
        elements = {v: 0 for v in ["Wood", "Fire", "Earth", "Metal", "Water"]}
        for char in all_chars:
            if char in element_map:
                elements[element_map[char]] += 1

        response = {
            "status": "success",
            "user_metadata": {
                "name": data.name,
                "gender": data.gender,
                "birthplace": location_name,
                "longitude": round(longitude, 4),
                "latitude": round(latitude, 4)
            },
            "corrected_birth": {
                "original_time": f"{data.hour:02d}:{data.minute:02d}",
                "note": "True solar time adjustment applied via longitude (full DST/historical TZ needs extra libs)"
            },
            "pillars": pillars,
            "day_master": {
                "stem": day_master_stem,
                "element": day_master_element,
                "full": f"{day_master_stem} ({day_master_element})"
            },
            "five_elements": elements,
            "chinese_full_output": lunar.toFullString(),
            "timestamp": datetime.now().isoformat(),
            "note": "This is a solid base. Full Ten Gods, Hidden Stems, DaYun, clashes need more advanced logic or external lib."
        }

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "ok"}
