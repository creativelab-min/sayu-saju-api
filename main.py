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

# === COMPLETE TEN GODS ===
ten_gods_full = {
    "甲": {"甲": "Friend (比肩)", "乙": "Rob Wealth (劫财)", "丙": "Eating God (食神)", "丁": "Hurting Officer (伤官)",
           "戊": "Indirect Wealth (偏财)", "己": "Direct Wealth (正财)", "庚": "Seven Killings (七杀)", "辛": "Direct Officer (正官)",
           "壬": "Indirect Resource (偏印)", "癸": "Direct Resource (正印)"},
    "乙": {"甲": "Rob Wealth (劫财)", "乙": "Friend (比肩)", "丙": "Hurting Officer (伤官)", "丁": "Eating God (食神)",
           "戊": "Direct Wealth (正财)", "己": "Indirect Wealth (偏财)", "庚": "Direct Officer (正官)", "辛": "Seven Killings (七杀)",
           "壬": "Direct Resource (正印)", "癸": "Indirect Resource (偏印)"},
    "丙": {"甲": "Direct Resource (正印)", "乙": "Indirect Resource (偏印)", "丙": "Friend (比肩)", "丁": "Rob Wealth (劫财)",
           "戊": "Eating God (食神)", "己": "Hurting Officer (伤官)", "庚": "Indirect Wealth (偏财)", "辛": "Direct Wealth (正财)",
           "壬": "Seven Killings (七杀)", "癸": "Direct Officer (正官)"},
    "丁": {"甲": "Indirect Resource (偏印)", "乙": "Direct Resource (正印)", "丙": "Rob Wealth (劫财)", "丁": "Friend (比肩)",
           "戊": "Hurting Officer (伤官)", "己": "Eating God (食神)", "庚": "Direct Wealth (正财)", "辛": "Indirect Wealth (偏财)",
           "壬": "Direct Officer (正官)", "癸": "Seven Killings (七杀)"},
    "戊": {"甲": "Seven Killings (七杀)", "乙": "Direct Officer (正官)", "丙": "Direct Resource (正印)", "丁": "Indirect Resource (偏印)",
           "戊": "Friend (比肩)", "己": "Rob Wealth (劫财)", "庚": "Eating God (食神)", "辛": "Hurting Officer (伤官)",
           "壬": "Indirect Wealth (偏财)", "癸": "Direct Wealth (正财)"},
    "己": {"甲": "Direct Officer (正官)", "乙": "Seven Killings (七杀)", "丙": "Indirect Resource (偏印)", "丁": "Direct Resource (正印)",
           "戊": "Rob Wealth (劫财)", "己": "Friend (比肩)", "庚": "Hurting Officer (伤官)", "辛": "Eating God (食神)",
           "壬": "Direct Wealth (正财)", "癸": "Indirect Wealth (偏财)"},
    "庚": {"甲": "Indirect Wealth (偏财)", "乙": "Direct Wealth (正财)", "丙": "Seven Killings (七杀)", "丁": "Direct Officer (正官)",
           "戊": "Direct Resource (正印)", "己": "Indirect Resource (偏印)", "庚": "Friend (比肩)", "辛": "Rob Wealth (劫财)",
           "壬": "Eating God (食神)", "癸": "Hurting Officer (伤官)"},
    "辛": {"甲": "Direct Wealth (正财)", "乙": "Indirect Wealth (偏财)", "丙": "Direct Officer (正官)", "丁": "Seven Killings (七杀)",
           "戊": "Indirect Resource (偏印)", "己": "Direct Resource (正印)", "庚": "Rob Wealth (劫财)", "辛": "Friend (比肩)",
           "壬": "Hurting Officer (伤官)", "癸": "Eating God (食神)"},
    "壬": {"甲": "Eating God (食神)", "乙": "Hurting Officer (伤官)", "丙": "Indirect Wealth (偏财)", "丁": "Direct Wealth (正财)",
           "戊": "Seven Killings (七杀)", "己": "Direct Officer (正官)", "庚": "Direct Resource (正印)", "辛": "Indirect Resource (偏印)",
           "壬": "Friend (比肩)", "癸": "Rob Wealth (劫财)"},
    "癸": {"甲": "Hurting Officer (伤官)", "乙": "Eating God (食神)", "丙": "Direct Wealth (正财)", "丁": "Indirect Wealth (偏财)",
           "戊": "Direct Officer (正官)", "己": "Seven Killings (七杀)", "庚": "Indirect Resource (偏印)", "辛": "Direct Resource (正印)",
           "壬": "Rob Wealth (劫财)", "癸": "Friend (比肩)"}
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

def generate_reflection_prompts(chart):
    day_master = chart.get("day_master", "Unknown")
    day_ten_god = chart.get("day_ten_god", "Unknown")
    strongest_element = max(chart.get("five_elements", {}), key=chart.get("five_elements", {}).get) if chart.get("five_elements") else "Unknown"

    return [
        f"With your **{day_master}** Day Master as the foundation, what situations feel most natural to you right now?",
        f"How is the **{day_ten_god}** energy appearing in your current relationships or challenges?",
        f"Your chart shows strong **{strongest_element}** energy. How does this strength show up in your life?",
        f"Looking at your Luck Cycle, what gentle invitation or lesson might it be offering?",
        f"If this chart is a mirror, what part of yourself are you being invited to understand with more kindness?",
        f"How can you work *with* your natural elemental balance instead of against it?"
    ]

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
        solar_time_info = calculate_true_solar_time(data.year, data.month, data.day, data.hour, data.minute, longitude)
        use_hour = solar_time_info["corrected_hour"]
        use_minute = solar_time_info["corrected_minute"]

        # Chart Calculation
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
            pillars[name] = {
                "stem": stem,
                "stem_english": stem_english.get(stem, stem),
                "branch": branch,
                "branch_english": branch_english.get(branch, branch),
                "hidden_stems": hidden_stems
            }

        # Elements
        all_stems = [p["stem"] for p in pillars.values()] + [hs for p in pillars.values() for hs in p.get("hidden_stems", [])]
        elements = {el: all_stems.count(st) for st, el in element_map.items() if st in all_stems}

        # Advanced Reflection Prompts
        reflection_prompts = generate_reflection_prompts({
            "day_master": day_master_stem,
            "pillars": pillars,
            "five_elements": elements
        })

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
            "five_elements": elements,
            "reflection_prompts": reflection_prompts,
            "timestamp": datetime.now().isoformat()
        }

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "ok"}
