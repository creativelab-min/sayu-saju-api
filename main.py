from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
from lunar_python import Solar, Lunar
from geopy.geocoders import Nominatim
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

# === FULL TEN GODS WITH DESCRIPTIONS (All 10 Day Masters) ===
ten_gods_full = {
    "甲": {  # Yang Wood
        "甲": {"name": "Friend (比肩)", "description": "Self-support, independence, strong personal will."},
        "乙": {"name": "Rob Wealth (劫财)", "description": "Competitiveness, sharing resources, sibling-like rivalry."},
        "丙": {"name": "Eating God (食神)", "description": "Creativity, enjoyment, talent, relaxation."},
        "丁": {"name": "Hurting Officer (伤官)", "description": "Rebellion, charisma, innovation, bold expression."},
        "戊": {"name": "Indirect Wealth (偏财)", "description": "Opportunities, side income, entrepreneurship."},
        "己": {"name": "Direct Wealth (正财)", "description": "Stable resources, responsibility, steady progress."},
        "庚": {"name": "Seven Killings (七杀)", "description": "Drive, pressure, leadership, transformation."},
        "辛": {"name": "Direct Officer (正官)", "description": "Structure, discipline, ethics, authority."},
        "壬": {"name": "Indirect Resource (偏印)", "description": "Intuition, unconventional learning, insight."},
        "癸": {"name": "Direct Resource (正印)", "description": "Support, wisdom, education, nurturing."}
    },
    "乙": {  # Yin Wood
        "甲": {"name": "Rob Wealth (劫财)", "description": "Competitiveness, sharing resources."},
        "乙": {"name": "Friend (比肩)", "description": "Self-support, independence."},
        "丙": {"name": "Hurting Officer (伤官)", "description": "Rebellion, charisma, innovation."},
        "丁": {"name": "Eating God (食神)", "description": "Creativity, enjoyment, talent."},
        "戊": {"name": "Direct Wealth (正财)", "description": "Stable resources, responsibility."},
        "己": {"name": "Indirect Wealth (偏财)", "description": "Opportunities, entrepreneurship."},
        "庚": {"name": "Direct Officer (正官)", "description": "Structure, discipline, ethics."},
        "辛": {"name": "Seven Killings (七杀)", "description": "Drive, pressure, leadership."},
        "壬": {"name": "Direct Resource (正印)", "description": "Support, wisdom, nurturing."},
        "癸": {"name": "Indirect Resource (偏印)", "description": "Intuition, unconventional insight."}
    },
    "丙": {  # Yang Fire
        "甲": {"name": "Direct Resource (正印)", "description": "Support, wisdom, nurturing."},
        "乙": {"name": "Indirect Resource (偏印)", "description": "Intuition, unconventional learning."},
        "丙": {"name": "Friend (比肩)", "description": "Self-support, independence."},
        "丁": {"name": "Rob Wealth (劫财)", "description": "Competitiveness, sharing."},
        "戊": {"name": "Eating God (食神)", "description": "Creativity, enjoyment."},
        "己": {"name": "Hurting Officer (伤官)", "description": "Rebellion, charisma."},
        "庚": {"name": "Indirect Wealth (偏财)", "description": "Opportunities, entrepreneurship."},
        "辛": {"name": "Direct Wealth (正财)", "description": "Stable resources, responsibility."},
        "壬": {"name": "Seven Killings (七杀)", "description": "Drive, pressure, leadership."},
        "癸": {"name": "Direct Officer (正官)", "description": "Structure, discipline."}
    },
    "丁": {  # Yin Fire
        "甲": {"name": "Indirect Resource (偏印)", "description": "Intuition, unconventional insight."},
        "乙": {"name": "Direct Resource (正印)", "description": "Support, wisdom, nurturing."},
        "丙": {"name": "Rob Wealth (劫财)", "description": "Competitiveness, sharing."},
        "丁": {"name": "Friend (比肩)", "description": "Self-support, independence."},
        "戊": {"name": "Hurting Officer (伤官)", "description": "Rebellion, charisma."},
        "己": {"name": "Eating God (食神)", "description": "Creativity, enjoyment."},
        "庚": {"name": "Direct Wealth (正财)", "description": "Stable resources."},
        "辛": {"name": "Indirect Wealth (偏财)", "description": "Opportunities, entrepreneurship."},
        "壬": {"name": "Direct Officer (正官)", "description": "Structure, discipline."},
        "癸": {"name": "Seven Killings (七杀)", "description": "Drive, pressure, leadership."}
    },
    "戊": {  # Yang Earth
        "甲": {"name": "Seven Killings (七杀)", "description": "Drive, pressure, leadership."},
        "乙": {"name": "Direct Officer (正官)", "description": "Structure, discipline."},
        "丙": {"name": "Direct Resource (正印)", "description": "Support, wisdom."},
        "丁": {"name": "Indirect Resource (偏印)", "description": "Intuition, insight."},
        "戊": {"name": "Friend (比肩)", "description": "Self-support, independence."},
        "己": {"name": "Rob Wealth (劫财)", "description": "Competitiveness, sharing."},
        "庚": {"name": "Eating God (食神)", "description": "Creativity, enjoyment."},
        "辛": {"name": "Hurting Officer (伤官)", "description": "Rebellion, charisma."},
        "壬": {"name": "Indirect Wealth (偏财)", "description": "Opportunities."},
        "癸": {"name": "Direct Wealth (正财)", "description": "Stable resources."}
    },
    "己": {  # Yin Earth
        "甲": {"name": "Direct Officer (正官)", "description": "Structure, discipline."},
        "乙": {"name": "Seven Killings (七杀)", "description": "Drive, pressure, leadership."},
        "丙": {"name": "Indirect Resource (偏印)", "description": "Intuition, insight."},
        "丁": {"name": "Direct Resource (正印)", "description": "Support, wisdom."},
        "戊": {"name": "Rob Wealth (劫财)", "description": "Competitiveness."},
        "己": {"name": "Friend (比肩)", "description": "Self-support, independence."},
        "庚": {"name": "Hurting Officer (伤官)", "description": "Rebellion, charisma."},
        "辛": {"name": "Eating God (食神)", "description": "Creativity, enjoyment."},
        "壬": {"name": "Direct Wealth (正财)", "description": "Stable resources."},
        "癸": {"name": "Indirect Wealth (偏财)", "description": "Opportunities."}
    },
    "庚": {  # Yang Metal
        "甲": {"name": "Indirect Wealth (偏财)", "description": "Opportunities, entrepreneurship."},
        "乙": {"name": "Direct Wealth (正财)", "description": "Stable resources, responsibility."},
        "丙": {"name": "Seven Killings (七杀)", "description": "Drive, pressure, leadership."},
        "丁": {"name": "Direct Officer (正官)", "description": "Structure, discipline."},
        "戊": {"name": "Direct Resource (正印)", "description": "Support, wisdom."},
        "己": {"name": "Indirect Resource (偏印)", "description": "Intuition, insight."},
        "庚": {"name": "Friend (比肩)", "description": "Self-support, independence."},
        "辛": {"name": "Rob Wealth (劫财)", "description": "Competitiveness, sharing."},
        "壬": {"name": "Eating God (食神)", "description": "Creativity, enjoyment."},
        "癸": {"name": "Hurting Officer (伤官)", "description": "Rebellion, charisma."}
    },
    "辛": {  # Yin Metal
        "甲": {"name": "Direct Wealth (正财)", "description": "Stable resources, responsibility."},
        "乙": {"name": "Indirect Wealth (偏财)", "description": "Opportunities, entrepreneurship."},
        "丙": {"name": "Direct Officer (正官)", "description": "Structure, discipline."},
        "丁": {"name": "Seven Killings (七杀)", "description": "Drive, pressure, leadership."},
        "戊": {"name": "Indirect Resource (偏印)", "description": "Intuition, insight."},
        "己": {"name": "Direct Resource (正印)", "description": "Support, wisdom."},
        "庚": {"name": "Rob Wealth (劫财)", "description": "Competitiveness, sharing."},
        "辛": {"name": "Friend (比肩)", "description": "Self-support, independence."},
        "壬": {"name": "Hurting Officer (伤官)", "description": "Rebellion, charisma."},
        "癸": {"name": "Eating God (食神)", "description": "Creativity, enjoyment."}
    },
    "壬": {  # Yang Water
        "甲": {"name": "Eating God (食神)", "description": "Creativity, enjoyment."},
        "乙": {"name": "Hurting Officer (伤官)", "description": "Rebellion, charisma."},
        "丙": {"name": "Indirect Wealth (偏财)", "description": "Opportunities, entrepreneurship."},
        "丁": {"name": "Direct Wealth (正财)", "description": "Stable resources."},
        "戊": {"name": "Seven Killings (七杀)", "description": "Drive, pressure, leadership."},
        "己": {"name": "Direct Officer (正官)", "description": "Structure, discipline."},
        "庚": {"name": "Direct Resource (正印)", "description": "Support, wisdom."},
        "辛": {"name": "Indirect Resource (偏印)", "description": "Intuition, insight."},
        "壬": {"name": "Friend (比肩)", "description": "Self-support, independence."},
        "癸": {"name": "Rob Wealth (劫财)", "description": "Competitiveness, sharing."}
    },
    "癸": {  # Yin Water
        "甲": {"name": "Hurting Officer (伤官)", "description": "Rebellion, charisma."},
        "乙": {"name": "Eating God (食神)", "description": "Creativity, enjoyment."},
        "丙": {"name": "Direct Wealth (正财)", "description": "Stable resources."},
        "丁": {"name": "Indirect Wealth (偏财)", "description": "Opportunities."},
        "戊": {"name": "Direct Officer (正官)", "description": "Structure, discipline."},
        "己": {"name": "Seven Killings (七杀)", "description": "Drive, pressure, leadership."},
        "庚": {"name": "Indirect Resource (偏印)", "description": "Intuition, insight."},
        "辛": {"name": "Direct Resource (正印)", "description": "Support, wisdom."},
        "壬": {"name": "Rob Wealth (劫财)", "description": "Competitiveness, sharing."},
        "癸": {"name": "Friend (比肩)", "description": "Self-support, independence."}
    }
}

# === INTERACTION RULES ===
clashes = {"子":"午","午":"子","丑":"未","未":"丑","寅":"申","申":"寅","卯":"酉","酉":"卯","辰":"戌","戌":"辰","巳":"亥","亥":"巳"}
combinations = {"子":"丑","丑":"子","寅":"亥","亥":"寅","卯":"戌","戌":"卯","辰":"酉","酉":"辰","巳":"申","申":"巳","午":"未","未":"午"}
harms = {"子":"未","未":"子","丑":"午","午":"丑","寅":"巳","巳":"寅","卯":"辰","辰":"卯","申":"亥","亥":"申","酉":"戌","戌":"酉"}
punishments = {"子":"卯","卯":"子","丑":"辰","辰":"丑","寅":"巳","巳":"寅","午":"午","未":"戌","戌":"未","申":"申","酉":"酉","亥":"亥"}

def get_interaction(b1, b2):
    if clashes.get(b1) == b2 or clashes.get(b2) == b1: return "Clash (冲)"
    if combinations.get(b1) == b2 or combinations.get(b2) == b1: return "Combination (合)"
    if harms.get(b1) == b2 or harms.get(b2) == b1: return "Harm (害)"
    if punishments.get(b1) == b2 or punishments.get(b2) == b1: return "Punishment (刑)"
    return None

def analyze_luck_cycle_interactions(natal_branches, luck_cycles):
    result = []
    for cycle in luck_cycles:
        cycle_branch = cycle.get("branch")
        inters = []
        for p_name, n_branch in natal_branches.items():
            inter = get_interaction(n_branch, cycle_branch)
            if inter:
                inters.append(f"{p_name} {inter}")
        if inters:
            result.append({"cycle": cycle["cycle"], "age_range": cycle["age_range"], "interactions": inters})
    return result

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
        "corrected_time": f"{solar_dt.hour:02d}:{solar_dt.minute:02d}",
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
        use_hour = int(solar_time_info["corrected_time"].split(":")[0])
        use_minute = int(solar_time_info["corrected_time"].split(":")[1])

        # Chart
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
        natal_branches = {}
        for name, stem, branch, hidden in pillar_info:
            hidden_stems = list(hidden) if hidden else []
            natal_branches[name] = branch
            pillars[name] = {
                "stem": stem,
                "stem_english": stem_english.get(stem, stem),
                "branch": branch,
                "branch_english": branch_english.get(branch, branch),
                "hidden_stems": hidden_stems
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
                "branch": gz[1],
                "branch_english": branch_english.get(gz[1], gz[1])
            })

        # Luck Cycle Interactions
        luck_interactions = analyze_luck_cycle_interactions(natal_branches, luck_cycles)

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
            "luck_cycles": luck_cycles,
            "luck_cycle_interactions": luck_interactions,
            "timestamp": datetime.now().isoformat()
        }

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "ok"}
