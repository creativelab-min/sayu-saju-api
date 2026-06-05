from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
from lunar_python import Solar, Lunar
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import math
import pytz

app = FastAPI(title="Sayu Saju API", description="Gentle mirror for self-understanding")

# === TRANSLATIONS ===
stem_english = {
    "甲": "Jia (Yang Wood)", "乙": "Yi (Yin Wood)", "丙": "Bing (Yang Fire)",
    "丁": "Ding (Yin Fire)", "戊": "Wu (Yang Earth)", "己": "Ji (Yin Earth)",
    "庚": "Geng (Yang Metal)", "辛": "Xin (Yin Metal)", "壬": "Ren (Yang Water)",
    "癸": "Gui (Yin Water)"
}

branch_english = {
    "子": "Zi (Rat)", "丑": "Chou (Ox)", "寅": "Yin (Tiger)", "卯": "Mao (Rabbit)",
    "辰": "Chen (Dragon)", "巳": "Si (Snake)", "午": "Wu (Horse)", "未": "Wei (Goat)",
    "申": "Shen (Monkey)", "酉": "You (Rooster)", "戌": "Xu (Dog)", "亥": "Hai (Pig)"
}

element_map = {
    "甲":"Wood", "乙":"Wood", "丙":"Fire", "丁":"Fire", "戊":"Earth", "己":"Earth",
    "庚":"Metal", "辛":"Metal", "壬":"Water", "癸":"Water"
}

# === FULL TEN GODS (abbreviated - use full version from earlier if needed) ===
ten_gods_full = { ... }  # Paste your full ten_gods_full here

def get_timezone_from_location(location_name: str):
    try:
        if any(x in location_name for x in ["Korea", "Seoul"]):
            return pytz.timezone("Asia/Seoul")
        if any(x in location_name for x in ["Vancouver", "Canada"]):
            return pytz.timezone("America/Vancouver")
        return pytz.utc
    except:
        return pytz.utc

def calculate_true_solar_time(year, month, day, hour, minute, longitude, location_name):
    tz = get_timezone_from_location(location_name)
    dt = datetime(year, month, day, hour, minute, tzinfo=tz)
    dt_utc = dt.astimezone(pytz.utc)

    day_of_year = dt_utc.timetuple().tm_yday
    gamma = 2 * math.pi / 365 * (day_of_year - 1)
    eqtime = 229.18 * (0.000075 + 0.001868 * math.cos(gamma) - 0.032077 * math.sin(gamma) 
                       - 0.014615 * math.cos(2*gamma) - 0.04089 * math.sin(2*gamma))

    long_correction = longitude * 4.0
    total_correction_min = long_correction + eqtime

    solar_dt = dt_utc + timedelta(minutes=total_correction_min)

    return {
        "original_time": f"{hour:02d}:{minute:02d}",
        "corrected_hour": solar_dt.hour,
        "corrected_minute": solar_dt.minute,
        "corrected_time": f"{solar_dt.hour:02d}:{solar_dt.minute:02d}",
        "longitude_correction_min": round(long_correction, 1),
        "equation_of_time_min": round(eqtime, 2),
        "total_correction_min": round(total_correction_min, 2),
        "note": "Advanced True Solar Time with EoT + timezone adjustment"
    }

class BirthData(BaseModel):
    name: str = "User"
    year: int
    month: int
    day: int
    hour: int = 12
    minute: int = 0
    gender: str = "male"
    birthplace: str = "Vancouver, Canada"
    is_lunar: bool = False

@app.post("/calculate-saju")
async def calculate_saju(data: BirthData):
    try:
        # Geocoding
        geolocator = Nominatim(user_agent="sayu_saju_app")
        try:
            loc = geolocator.geocode(data.birthplace, timeout=10)
            longitude = round(loc.longitude, 4) if loc else 0
            location_name = loc.address if loc else data.birthplace
        except:
            longitude = 0
            location_name = data.birthplace

        # True Solar Time
        solar_time_info = calculate_true_solar_time(
            data.year, data.month, data.day, data.hour, data.minute, longitude, location_name
        )

        # Use corrected time
        use_hour = solar_time_info["corrected_hour"]
        use_minute = solar_time_info["corrected_minute"]

        # Calculate chart with corrected time
        if data.is_lunar:
            lunar = Lunar.fromYMDHMS(data.year, data.month, data.day, use_hour, use_minute, 0)
            solar = lunar.getSolar()
        else:
            solar = Solar.fromYmdHms(data.year, data.month, data.day, use_hour, use_minute, 0)
            lunar = solar.getLunar()

        eight_char = lunar.getEightChar()
        day_master_stem = eight_char.getDayGan()

        # Pillars (simplified for now - add full Ten Gods logic as needed)
        pillar_info = [
            ("year", eight_char.getYearGan(), eight_char.getYearZhi(), eight_char.getYearHideGan()),
            ("month", eight_char.getMonthGan(), eight_char.getMonthZhi(), eight_char.getMonthHideGan()),
            ("day", eight_char.getDayGan(), eight_char.getDayZhi(), eight_char.getDayHideGan()),
            ("hour", eight_char.getTimeGan(), eight_char.getTimeZhi(), eight_char.getTimeHideGan())
        ]

        pillars = {}
        for name, stem, branch, hidden in pillar_info:
            hidden_stems = list(hidden) if hidden else []
            pillars[name] = {
                "stem": stem,
                "stem_english": stem_english.get(stem, stem),
                "branch": branch,
                "branch_english": branch_english.get(branch, branch),
                "hidden_stems": hidden_stems
            }

        response = {
            "status": "success",
            "gentle_note": "This chart is a gentle mirror for self-reflection and personal growth.",
            "user_metadata": {
                "name": data.name,
                "gender": data.gender,
                "birthplace": location_name,
                "longitude": longitude
            },
            "true_solar_time": solar_time_info,
            "pillars": pillars,
            "day_master": day_master_stem,
            "timestamp": datetime.now().isoformat()
        }

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "ok"}
