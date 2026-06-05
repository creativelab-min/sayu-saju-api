from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from lunar_python import Solar
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

app = FastAPI(title="Sayu Saju API")

class BirthData(BaseModel):
    name: str = "User"
    year: int
    month: int
    day: int
    hour: int = 12
    minute: int = 0
    gender: str = "male"
    birthplace: str = "Vancouver, Canada"

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

        # Solar date with time
        solar = Solar.fromYmdHms(data.year, data.month, data.day, data.hour, data.minute, 0)
        lunar = solar.getLunar()
        eight_char = lunar.getEightChar()

        element_map = {"甲":"Wood","乙":"Wood","丙":"Fire","丁":"Fire","戊":"Earth","己":"Earth",
                       "庚":"Metal","辛":"Metal","壬":"Water","癸":"Water"}

        pillars = {
            "year": {"stem": eight_char.getYearGan(), "branch": eight_char.getYearZhi()},
            "month": {"stem": eight_char.getMonthGan(), "branch": eight_char.getMonthZhi()},
            "day": {"stem": eight_char.getDayGan(), "branch": eight_char.getDayZhi()},
            "hour": {"stem": eight_char.getTimeGan(), "branch": eight_char.getTimeZhi()}
        }

        response = {
            "status": "success",
            "user": {"name": data.name, "gender": data.gender, "birthplace": location_name},
            "pillars": pillars,
            "day_master": eight_char.getDayGan(),
            "raw_output": lunar.toFullString()[:500],  # truncated
            "timestamp": datetime.now().isoformat()
        }
        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "ok"}
