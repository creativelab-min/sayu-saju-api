from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from lunar_python import Solar, EightChar

app = FastAPI(title="Sayu Saju API", description="Accurate Four Pillars calculator for self-reflection")

class BirthData(BaseModel):
    year: int
    month: int
    day: int
    hour: int = 12
    minute: int = 0
    gender: str = "male"
    timezone_offset: int = 8

@app.post("/calculate-saju")
async def calculate_saju(data: BirthData):
    try:
        solar = Solar.fromYMDHMS(
            data.year, data.month, data.day, 
            data.hour, data.minute, 0
        )
        
        lunar = solar.getLunar()
        eight_char = lunar.getEightChar()
        
        element_map = {
            "甲": "Wood", "乙": "Wood",
            "丙": "Fire", "丁": "Fire",
            "戊": "Earth", "己": "Earth",
            "庚": "Metal", "辛": "Metal",
            "壬": "Water", "癸": "Water"
        }
        
        pillars = {
            "year": eight_char.getYear(),
            "month": eight_char.getMonth(),
            "day": eight_char.getDay(),
            "hour": eight_char.getTime()
        }
        
        day_master = eight_char.getDayGan()
        day_master_element = element_map.get(day_master, "Unknown")
        
        all_chars = "".join(pillars.values())
        elements = {v: 0 for v in ["Wood", "Fire", "Earth", "Metal", "Water"]}
        for char in all_chars:
            if char in element_map:
                elements[element_map[char]] += 1
        
        response = {
            "status": "success",
            "input": data.dict(),
            "pillars": {
                "year_pillar": pillars["year"],
                "month_pillar": pillars["month"],
                "day_pillar": pillars["day"],
                "hour_pillar": pillars["hour"]
            },
            "day_master": {
                "stem": day_master,
                "element": day_master_element,
                "full": f"{day_master} ({day_master_element})"
            },
            "five_elements": elements,
            "chinese_output": lunar.toFullString(),
            "timestamp": datetime.now().isoformat()
        }
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "ok", "message": "Sayu Saju API is running"}
