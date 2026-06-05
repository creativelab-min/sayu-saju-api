from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from lunar_python import Solar, Lunar
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

app = FastAPI(title="Sayu Saju API", description="Gentle mirror for self-understanding")

# Translations and Ten Gods (same as previous full version)
stem_english = { ... }  # Keep all previous dictionaries
branch_english = { ... }
element_map = { ... }
ten_gods_full = { ... }  # Full dictionary from before

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
            latitude = round(loc.latitude, 4) if loc else 0
            location_name = loc.address if loc else data.birthplace
        except:
            longitude = latitude = 0
            location_name = data.birthplace

        # Lunar/Solar handling
        if data.is_lunar:
            lunar = Lunar.fromYMDHMS(data.year, data.month, data.day, data.hour, data.minute, 0)
            solar = lunar.getSolar()
        else:
            solar = Solar.fromYmdHms(data.year, data.month, data.day, data.hour, data.minute, 0)
            lunar = solar.getLunar()

        eight_char = lunar.getEightChar()
        day_master_stem = eight_char.getDayGan()

        # Pillars with Ten Gods + Hidden Stems (same as before)
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

        # Element distribution
        all_stems = [p["stem"] for p in pillars.values()] + [hs for p in pillars.values() for hs in p["hidden_stems"]]
        elements = {el: all_stems.count(st) for st, el in element_map.items() if st in all_stems}

        # Luck Cycles (DaYun)
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

        # === NEW: Annual Cycles (세운 / Liu Nian) ===
        current_year = datetime.now().year
        annual_cycles = []
        for y in range(current_year - 2, current_year + 6):  # Past 2 years + next 5 years
            annual_solar = Solar.fromYmd(y, 1, 1)
            annual_lunar = annual_solar.getLunar()
            annual_eight = annual_lunar.getEightChar()
            annual_cycles.append({
                "year": y,
                "pillar": annual_eight.getYearGan() + annual_eight.getYearZhi(),
                "stem_english": stem_english.get(annual_eight.getYearGan(), ""),
                "branch_english": branch_english.get(annual_eight.getYearZhi(), ""),
                "is_current": y == current_year
            })

        response = {
            "status": "success",
            "gentle_note": "This chart is a gentle mirror for self-reflection and personal growth.",
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
            "annual_cycles": annual_cycles,   # ← New!
            "timestamp": datetime.now().isoformat()
        }

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "ok"}
