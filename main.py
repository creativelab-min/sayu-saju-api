from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
from lunar_python import Solar, Lunar
from geopy.geocoders import Nominatim
import math

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

# === TEN GODS ===
ten_gods_full = {
    "甲": {"甲": "Friend", "乙": "Rob Wealth", "丙": "Eating God", "丁": "Hurting Officer", "戊": "Indirect Wealth", "己": "Direct Wealth", "庚": "Seven Killings", "辛": "Direct Officer", "壬": "Indirect Resource", "癸": "Direct Resource"},
    "乙": {"甲": "Rob Wealth", "乙": "Friend", "丙": "Hurting Officer", "丁": "Eating God", "戊": "Direct Wealth", "己": "Indirect Wealth", "庚": "Direct Officer", "辛": "Seven Killings", "壬": "Direct Resource", "癸": "Indirect Resource"},
    # ... (shortened for brevity - full version works the same)
}

def calculate_true_solar_time(year, month, day, hour, minute, longitude):
    dt = datetime(year, month, day, hour, minute)
    long_correction_min = longitude * 4.0
    day_of_year = dt.timetuple().tm_yday
    gamma = 2 * math.pi / 365 * (day_of_year - 1)
    eqtime = 229.18 * (0.000075 + 0.001868 * math.cos(gamma) - 0.032077 * math.sin(gamma) 
                       - 0.014615 * math.cos(2*gamma) - 0.04089 * math.sin(2*gamma))
    total = max(min(long_correction_min + eqtime, 40), -40)
    solar_dt = dt + timedelta(minutes=total)
    return {
        "original_time": f"{hour:02d}:{minute:02d}",
        "corrected_hour": solar_dt.hour,
        "corrected_minute": solar_dt.minute,
        "total_correction_min": round(total, 2),
        "note": "Realistic capped True Solar Time"
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

class ChatRequest(BaseModel):
    chart: dict
    user_message: str
    name: str = "User"

@app.post("/chat")
async def chat_with_sayu(request: ChatRequest):
    try:
        # Simple rule-based gentle response for now (no OpenAI needed)
        day_master = request.chart.get("day_master", "Unknown")
        
        response_text = f"""Hello {request.name},

Thank you for sharing. From your Saju chart, your Day Master is **{day_master}**.

Your message: "{request.user_message}"

This may be highlighting a pattern worth reflecting on gently. 
What feelings or situations are coming up for you right now?

I'm here to listen without judgment. Would you like to explore this further?"""

        return {
            "status": "success",
            "response": response_text,
            "note": "This is a basic reflective response. You can upgrade to OpenAI later."
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/calculate-saju")
async def calculate_saju(data: BirthData):
    try:
        geolocator = Nominatim(user_agent="sayu_saju_app")
        try:
            loc = geolocator.geocode(data.birthplace, timeout=10)
            longitude = round(loc.longitude, 4) if loc else 0
            location_name = loc.address if loc else data.birthplace
        except:
            longitude = 0
            location_name = data.birthplace

        solar_time_info = calculate_true_solar_time(data.year, data.month, data.day, data.hour, data.minute, longitude)
        use_hour = solar_time_info["corrected_hour"]
        use_minute = solar_time_info["corrected_minute"]

        if data.is_lunar:
            lunar = Lunar.fromYMDHMS(data.year, data.month, data.day, use_hour, use_minute, 0)
            solar = lunar.getSolar()
        else:
            solar = Solar.fromYmdHms(data.year, data.month, data.day, use_hour, use_minute, 0)
            lunar = solar.getLunar()

        eight_char = lunar.getEightChar()
        day_master_stem = eight_char.getDayGan()

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
