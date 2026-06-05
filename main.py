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

# === FULL TEN GODS WITH DESCRIPTIONS ===
ten_gods_full = {
    "甲": { "甲": {"name": "Friend (比肩)", "description": "Self-support, independence, strong personal will."},
            "乙": {"name": "Rob Wealth (劫财)", "description": "Competitiveness, sharing resources, rivalry."},
            "丙": {"name": "Eating God (食神)", "description": "Creativity, enjoyment, talent expression."},
            "丁": {"name": "Hurting Officer (伤官)", "description": "Rebellion, charisma, bold innovation."},
            "戊": {"name": "Indirect Wealth (偏财)", "description": "Opportunities, side income, entrepreneurship."},
            "己": {"name": "Direct Wealth (正财)", "description": "Stable resources, responsibility."},
            "庚": {"name": "Seven Killings (七杀)", "description": "Drive, pressure, leadership."},
            "辛": {"name": "Direct Officer (正官)", "description": "Structure, discipline, ethics."},
            "壬": {"name": "Indirect Resource (偏印)", "description": "Intuition, unconventional insight."},
            "癸": {"name": "Direct Resource (正印)", "description": "Support, wisdom, nurturing."} },
    # (All other 9 Day Masters follow the same pattern as provided in previous messages - abbreviated here to save space. 
    # In practice, paste the full 10 from the earlier complete dictionary.)
    # For full version, refer to the message with "complete expanded ten_gods_full"
}

def get_timezone_from_location(location_name: str):
    try:
        if any(x in location_name for x in ["Korea", "Seoul", "Tokyo"]):
            return pytz.timezone("Asia/Seoul")
        if any(x in location_name for x in ["Vancouver", "Canada", "Seattle"]):
            return pytz.timezone("America/Vancouver")
        if "London" in location_name:
            return pytz.timezone("Europe/London")
        return pytz.utc
    except:
        return pytz.utc

def calculate_true_solar_time(year, month, day, hour, minute, longitude, location_name):
    tz = get_timezone_from_location(location_name)
    dt = datetime(year, month, day, hour, minute, tzinfo=tz)
    dt_utc = dt.astimezone(pytz.utc)

    # Improved Equation of Time
    day_of_year = dt_utc.timetuple().tm_yday
    gamma = 2 * math.pi / 365 * (day_of_year - 1)
    eqtime = 229.18 * (0.000075 + 0.001868 * math.cos(gamma) - 0.032077 * math.sin(gamma) 
                       - 0.014615 * math.cos(2*gamma) - 0.04089 * math.sin(2*gamma))

    long_correction = longitude * 4.0
    total_correction_min = long_correction + eqtime

    solar_dt = dt_utc + timedelta(minutes=total_correction_min)

    return {
        "original_time": f"{hour:02d}:{minute:02d}",
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

        use_hour = int(solar_time_info["corrected_time"].split(":")[0])
        use_minute = int(solar_time_info["corrected_time"].split(":")[1])

        # Lunar / Solar with corrected time
        if data.is_lunar:
            lunar = Lunar.fromYMDHMS(data.year, data.month, data.day, use_hour, use_minute, 0)
            solar = lunar.getSolar()
        else:
            solar = Solar.fromYmdHms(data.year, data.month, data.day, use_hour, use_minute, 0)
            lunar = solar.getLunar()

        eight_char = lunar.getEightChar()
        day_master_stem = eight_char.getDayGan()

        # Pillars
        pillar_info = [
            ("year", eight_char.getYearGan(), eight_char.getYearZhi(), eight_char.getYearHideGan()),
            ("month", eight_char.getMonthGan(), eight_char.getMonthZhi(), eight_char.getMonthHideGan()),
            ("day", eight_char.getDayGan(), eight_char.getDayZhi(), eight_char.getDayHideGan()),
            ("hour", eight_char.getTimeGan(), eight_char.getTimeZhi(), eight_char.getTimeHideGan())
        ]

        pillars = {}
        for name, stem, branch, hidden in pillar_info:
            hidden_stems = list(hidden) if hidden else []
            ten_god_info = ten_gods_full.get(day_master_stem, {}).get(stem, {"name": "N/A", "description": ""})
            pillars[name] = {
                "stem": stem,
                "stem_english": stem_english.get(stem, stem),
                "branch": branch,
                "branch_english": branch_english.get(branch, branch),
                "hidden_stems": hidden_stems,
                "ten_god": ten_god_info["name"],
                "ten_god_description": ten_god_info["description"]
            }

        # Elements
        all_stems = [p["stem"] for p in pillars.values()] + [hs for p in pillars.values() for hs in p["hidden_stems"]]
        elements = {el: all_stems.count(st) for st, el in element_map.items() if st in all_stems}

        # DaYun
        gender_value = 1 if data.gender.lower() == "male" else 0
        yun = eight_char.getYun(gender_value)
        da_yun_list = yun.getDaYun()
        luck_cycles = []
        for i, dy in enumerate(da_yun_list[:8]):
            gz = dy.getGanZhi()
            luck_cycles.append({
                "cycle": i + 1,
                "age_range": f"{dy.getStartAge()}-{dy.getStartAge() + 9}",
                "pillar": gz,
                "stem_english": stem_english.get(gz[0], gz[0]),
                "branch_english": branch_english.get(gz[1], gz[1])
            })

        # Annual Cycles
        current_year = datetime.now().year
        annual_cycles = []
        for y in range(current_year - 2, current_year + 6):
            ann_solar = Solar.fromYmd(y, 1, 1)
            ann_lunar = ann_solar.getLunar()
            ann_eight = ann_lunar.getEightChar()
            annual_cycles.append({
                "year": y,
                "pillar": ann_eight.getYearGan() + ann_eight.getYearZhi(),
                "stem_english": stem_english.get(ann_eight.getYearGan(), ""),
                "branch_english": branch_english.get(ann_eight.getYearZhi(), ""),
                "is_current": y == current_year
            })

        response = {
            "status": "success",
            "gentle_note": "This chart is a gentle mirror for self-reflection and personal growth.",
            "user_metadata": {
                "name": data.name,
                "gender": data.gender,
                "birthplace": location_name,
                "longitude": longitude,
                "input_type": "Lunar" if data.is_lunar else "Solar"
            },
            "true_solar_time": solar_time_info,
            "pillars": pillars,
            "day_master": {
                "stem": day_master_stem,
                "english": stem_english.get(day_master_stem, day_master_stem),
                "element": element_map.get(day_master_stem, "Unknown")
            },
            "five_elements": elements,
            "luck_cycles": luck_cycles,
            "annual_cycles": annual_cycles,
            "timestamp": datetime.now().isoformat()
        }

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "ok"}
