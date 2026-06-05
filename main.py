from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from lunar_python import Solar, Lunar
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

app = FastAPI(title="Sayu Saju API", description="Gentle mirror for self-understanding")

# Translations
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

class BirthData(BaseModel):
    name: str = "User"
    year: int
    month: int
    day: int
    hour: int = 12
    minute: int = 0
    gender: str = "male"
    birthplace: str = "Vancouver, Canada"
    is_lunar: bool = False   # New: True if input is Lunar calendar

@app.post("/calculate-saju")
async def calculate_saju(data: BirthData):
    try:
        # Geocoding
        geolocator = Nominatim(user_agent="sayu_saju_app")
        try:
            loc = geolocator.geocode(data.birthplace, timeout=10)
            longitude = round(loc.longitude, 4) if loc else 0
            latitude = round(loc.latitude, 4) if loc else 0
            location_name = loc.address if loc else data.birthplace
        except:
            longitude = latitude = 0
            location_name = data.birthplace

        # === LUNAR / SOLAR HANDLING ===
        if data.is_lunar:
            lunar = Lunar.fromYMDHMS(data.year, data.month, data.day, data.hour, data.minute, 0)
            solar = lunar.getSolar()
        else:
            solar = Solar.fromYmdHms(data.year, data.month, data.day, data.hour, data.minute, 0)
            lunar = solar.getLunar()

        eight_char = lunar.getEightChar()

        day_master_stem = eight_char.getDayGan()

        # Pillars with Hidden Stems
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
                "hidden_stems": hidden_stems,
                "hidden_stems_english": [stem_english.get(h, h) for h in hidden_stems]
            }

        # Elements + Luck Cycles (same as before)
        all_stems = [p["stem"] for p in pillars.values()] + [hs for p in pillars.values() for hs in p["hidden_stems"]]
        elements = {el: all_stems.count(st) for st, el in element_map.items() if st in all_stems}

        # Luck Cycles
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

        response = {
            "status": "success",
            "gentle_note": "This chart offers a lens for gentle self-reflection and personal growth.",
            "user_metadata": {
                "name": data.name,
                "gender": data.gender,
                "birthplace": location_name,
                "input_type": "Lunar" if data.is_lunar else "Solar",
                "longitude": longitude
            },
            "pillars": pillars,
            "day_master": {
                "stem": day_master_stem,
                "english": stem_english.get(day_master_stem, day_master_stem),
                "element": element_map.get(day_master_stem, "Unknown")
            },
            "five_elements": elements,
            "luck_cycles": luck_cycles,
            "timestamp": datetime.now().isoformat()
        }

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "ok"}
