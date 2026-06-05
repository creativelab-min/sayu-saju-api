from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from lunar_python import Solar
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

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
    "甲": { "甲": {"name": "Friend (比肩)", "description": "Self-support, independence, strong personal will and self-reliance."},
            "乙": {"name": "Rob Wealth (劫财)", "description": "Competitiveness, sharing resources, sibling-like rivalry or teamwork challenges."},
            "丙": {"name": "Eating God (食神)", "description": "Creativity, enjoyment, talent, relaxation and joyful self-expression."},
            "丁": {"name": "Hurting Officer (伤官)", "description": "Rebellion, charisma, innovation, bold self-expression and originality."},
            "戊": {"name": "Indirect Wealth (偏财)", "description": "Opportunities, side income, entrepreneurial spirit and risk-taking."},
            "己": {"name": "Direct Wealth (正财)", "description": "Stable resources, consistent effort, responsibility and steady progress."},
            "庚": {"name": "Seven Killings (七杀)", "description": "Drive, pressure, leadership, transformative power and ambition."},
            "辛": {"name": "Direct Officer (正官)", "description": "Structure, discipline, ethics, formal authority and responsibility."},
            "壬": {"name": "Indirect Resource (偏印)", "description": "Intuition, unconventional learning, deep insight and creativity."},
            "癸": {"name": "Direct Resource (正印)", "description": "Support, wisdom, education, nurturing and steady knowledge."} },
    "乙": { "甲": {"name": "Rob Wealth (劫财)", "description": "Competitiveness, sharing resources, sibling-like rivalry."},
            "乙": {"name": "Friend (比肩)", "description": "Self-support, independence and personal will."},
            "丙": {"name": "Hurting Officer (伤官)", "description": "Rebellion, charisma, innovation and bold expression."},
            "丁": {"name": "Eating God (食神)", "description": "Creativity, enjoyment, talent and relaxation."},
            "戊": {"name": "Direct Wealth (正财)", "description": "Stable resources, responsibility and consistent effort."},
            "己": {"name": "Indirect Wealth (偏财)", "description": "Opportunities, side income and entrepreneurial energy."},
            "庚": {"name": "Direct Officer (正官)", "description": "Structure, discipline, ethics and formal authority."},
            "辛": {"name": "Seven Killings (七杀)", "description": "Drive, pressure, leadership and transformative ambition."},
            "壬": {"name": "Direct Resource (正印)", "description": "Support, wisdom, education and nurturing."},
            "癸": {"name": "Indirect Resource (偏印)", "description": "Intuition, unconventional insight and deep learning."} },
    "丙": { "甲": {"name": "Direct Resource (正印)", "description": "Support, wisdom, education and nurturing stability."},
            "乙": {"name": "Indirect Resource (偏印)", "description": "Intuition, unconventional learning and creative insight."},
            "丙": {"name": "Friend (比肩)", "description": "Self-support, independence and personal will."},
            "丁": {"name": "Rob Wealth (劫财)", "description": "Competitiveness, sharing and teamwork energy."},
            "戊": {"name": "Eating God (食神)", "description": "Creativity, enjoyment, talent and joyful expression."},
            "己": {"name": "Hurting Officer (伤官)", "description": "Rebellion, charisma, innovation and bold expression."},
            "庚": {"name": "Indirect Wealth (偏财)", "description": "Opportunities, side income and entrepreneurial drive."},
            "辛": {"name": "Direct Wealth (正财)", "description": "Stable resources, responsibility and steady progress."},
            "壬": {"name": "Seven Killings (七杀)", "description": "Drive, pressure, leadership and transformative power."},
            "癸": {"name": "Direct Officer (正官)", "description": "Structure, discipline, ethics and authority."} },
    "丁": { "甲": {"name": "Indirect Resource (偏印)", "description": "Intuition, unconventional learning and insight."},
            "乙": {"name": "Direct Resource (正印)", "description": "Support, wisdom, education and nurturing."},
            "丙": {"name": "Rob Wealth (劫财)", "description": "Competitiveness and sharing energy."},
            "丁": {"name": "Friend (比肩)", "description": "Self-support and independence."},
            "戊": {"name": "Hurting Officer (伤官)", "description": "Rebellion, charisma and bold innovation."},
            "己": {"name": "Eating God (食神)", "description": "Creativity, enjoyment and talent expression."},
            "庚": {"name": "Direct Wealth (正财)", "description": "Stable resources and responsibility."},
            "辛": {"name": "Indirect Wealth (偏财)", "description": "Opportunities and entrepreneurial energy."},
            "壬": {"name": "Direct Officer (正官)", "description": "Structure, discipline and ethics."},
            "癸": {"name": "Seven Killings (七杀)", "description": "Drive, pressure and leadership."} },
    "戊": { "甲": {"name": "Seven Killings (七杀)", "description": "Drive, pressure, leadership and transformation."},
            "乙": {"name": "Direct Officer (正官)", "description": "Structure, discipline, ethics and authority."},
            "丙": {"name": "Direct Resource (正印)", "description": "Support, wisdom and nurturing stability."},
            "丁": {"name": "Indirect Resource (偏印)", "description": "Intuition and unconventional insight."},
            "戊": {"name": "Friend (比肩)", "description": "Self-support and independence."},
            "己": {"name": "Rob Wealth (劫财)", "description": "Competitiveness and sharing energy."},
            "庚": {"name": "Eating God (食神)", "description": "Creativity, enjoyment and talent."},
            "辛": {"name": "Hurting Officer (伤官)", "description": "Rebellion, charisma and innovation."},
            "壬": {"name": "Indirect Wealth (偏财)", "description": "Opportunities and entrepreneurial drive."},
            "癸": {"name": "Direct Wealth (正财)", "description": "Stable resources and responsibility."} },
    "己": { "甲": {"name": "Direct Officer (正官)", "description": "Structure, discipline and formal authority."},
            "乙": {"name": "Seven Killings (七杀)", "description": "Drive, pressure and transformative leadership."},
            "丙": {"name": "Indirect Resource (偏印)", "description": "Intuition and unconventional learning."},
            "丁": {"name": "Direct Resource (正印)", "description": "Support, wisdom and nurturing."},
            "戊": {"name": "Rob Wealth (劫财)", "description": "Competitiveness and sharing."},
            "己": {"name": "Friend (比肩)", "description": "Self-support and independence."},
            "庚": {"name": "Hurting Officer (伤官)", "description": "Rebellion, charisma and bold expression."},
            "辛": {"name": "Eating God (食神)", "description": "Creativity, enjoyment and talent."},
            "壬": {"name": "Direct Wealth (正财)", "description": "Stable resources and responsibility."},
            "癸": {"name": "Indirect Wealth (偏财)", "description": "Opportunities and entrepreneurial energy."} },
    "庚": { "甲": {"name": "Indirect Wealth (偏财)", "description": "Opportunities, side income and risk-taking."},
            "乙": {"name": "Direct Wealth (正财)", "description": "Stable resources and consistent responsibility."},
            "丙": {"name": "Seven Killings (七杀)", "description": "Drive, pressure and transformative leadership."},
            "丁": {"name": "Direct Officer (正官)", "description": "Structure, discipline and ethics."},
            "戊": {"name": "Direct Resource (正印)", "description": "Support, wisdom and nurturing."},
            "己": {"name": "Indirect Resource (偏印)", "description": "Intuition and unconventional insight."},
            "庚": {"name": "Friend (比肩)", "description": "Self-support and independence."},
            "辛": {"name": "Rob Wealth (劫财)", "description": "Competitiveness and sharing energy."},
            "壬": {"name": "Eating God (食神)", "description": "Creativity, enjoyment and talent."},
            "癸": {"name": "Hurting Officer (伤官)", "description": "Rebellion, charisma and innovation."} },
    "辛": { "甲": {"name": "Direct Wealth (正财)", "description": "Stable resources and responsibility."},
            "乙": {"name": "Indirect Wealth (偏财)", "description": "Opportunities and entrepreneurial energy."},
            "丙": {"name": "Direct Officer (正官)", "description": "Structure, discipline and ethics."},
            "丁": {"name": "Seven Killings (七杀)", "description": "Drive, pressure and leadership."},
            "戊": {"name": "Indirect Resource (偏印)", "description": "Intuition and unconventional learning."},
            "己": {"name": "Direct Resource (正印)", "description": "Support, wisdom and nurturing."},
            "庚": {"name": "Rob Wealth (劫财)", "description": "Competitiveness and sharing."},
            "辛": {"name": "Friend (比肩)", "description": "Self-support and independence."},
            "壬": {"name": "Hurting Officer (伤官)", "description": "Rebellion, charisma and bold expression."},
            "癸": {"name": "Eating God (食神)", "description": "Creativity, enjoyment and talent."} },
    "壬": { "甲": {"name": "Eating God (食神)", "description": "Creativity, enjoyment and joyful expression."},
            "乙": {"name": "Hurting Officer (伤官)", "description": "Rebellion, charisma and innovation."},
            "丙": {"name": "Indirect Wealth (偏财)", "description": "Opportunities and entrepreneurial energy."},
            "丁": {"name": "Direct Wealth (正财)", "description": "Stable resources and responsibility."},
            "戊": {"name": "Seven Killings (七杀)", "description": "Drive, pressure and transformative leadership."},
            "己": {"name": "Direct Officer (正官)", "description": "Structure, discipline and ethics."},
            "庚": {"name": "Direct Resource (正印)", "description": "Support, wisdom and nurturing."},
            "辛": {"name": "Indirect Resource (偏印)", "description": "Intuition and unconventional insight."},
            "壬": {"name": "Friend (比肩)", "description": "Self-support and independence."},
            "癸": {"name": "Rob Wealth (劫财)", "description": "Competitiveness and sharing energy."} },
    "癸": { "甲": {"name": "Hurting Officer (伤官)", "description": "Rebellion, charisma and bold innovation."},
            "乙": {"name": "Eating God (食神)", "description": "Creativity, enjoyment and talent expression."},
            "丙": {"name": "Direct Wealth (正财)", "description": "Stable resources and responsibility."},
            "丁": {"name": "Indirect Wealth (偏财)", "description": "Opportunities and entrepreneurial drive."},
            "戊": {"name": "Direct Officer (正官)", "description": "Structure, discipline and ethics."},
            "己": {"name": "Seven Killings (七杀)", "description": "Drive, pressure and leadership."},
            "庚": {"name": "Indirect Resource (偏印)", "description": "Intuition and unconventional learning."},
            "辛": {"name": "Direct Resource (正印)", "description": "Support, wisdom and nurturing."},
            "壬": {"name": "Rob Wealth (劫财)", "description": "Competitiveness and sharing."},
            "癸": {"name": "Friend (比肩)", "description": "Self-support and independence."} }
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
            latitude = round(loc.latitude, 4) if loc else 0
            location_name = loc.address if loc else data.birthplace
        except:
            longitude = latitude = 0
            location_name = data.birthplace

        # Lunar / Solar handling
        if data.is_lunar:
            lunar = Lunar.fromYMDHMS(data.year, data.month, data.day, data.hour, data.minute, 0)
            solar = lunar.getSolar()
        else:
            solar = Solar.fromYmdHms(data.year, data.month, data.day, data.hour, data.minute, 0)
            lunar = solar.getLunar()

        eight_char = lunar.getEightChar()
        day_master_stem = eight_char.getDayGan()

        # Pillars with Ten Gods + Hidden Stems
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
                "hidden_stems_english": [stem_english.get(h, h) for h in hidden_stems],
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

        response = {
            "status": "success",
            "gentle_note": "This chart is a gentle mirror for self-reflection and personal growth. Use it with curiosity and compassion.",
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
