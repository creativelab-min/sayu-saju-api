from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictFloat, StrictInt, field_validator, model_validator
from datetime import datetime, timedelta
from lunar_python import Solar, Lunar
from geopy.exc import GeocoderServiceError, GeocoderTimedOut, GeocoderUnavailable
from geopy.geocoders import Nominatim
from typing import Annotated, Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import logging
import math

logger = logging.getLogger(__name__)

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

# === TEN GODS (Simple version) ===
ten_gods_full = {
    "甲": {"甲": "Friend", "乙": "Rob Wealth", "丙": "Eating God", "丁": "Hurting Officer",
           "戊": "Indirect Wealth", "己": "Direct Wealth", "庚": "Seven Killings", "辛": "Direct Officer",
           "壬": "Indirect Resource", "癸": "Direct Resource"},
    "乙": {"甲": "Rob Wealth", "乙": "Friend", "丙": "Hurting Officer", "丁": "Eating God",
           "戊": "Direct Wealth", "己": "Indirect Wealth", "庚": "Direct Officer", "辛": "Seven Killings",
           "壬": "Direct Resource", "癸": "Indirect Resource"},
    "丙": {"甲": "Direct Resource", "乙": "Indirect Resource", "丙": "Friend", "丁": "Rob Wealth",
           "戊": "Eating God", "己": "Hurting Officer", "庚": "Indirect Wealth", "辛": "Direct Wealth",
           "壬": "Seven Killings", "癸": "Direct Officer"},
    "丁": {"甲": "Indirect Resource", "乙": "Direct Resource", "丙": "Rob Wealth", "丁": "Friend",
           "戊": "Hurting Officer", "己": "Eating God", "庚": "Direct Wealth", "辛": "Indirect Wealth",
           "壬": "Direct Officer", "癸": "Seven Killings"},
    "戊": {"甲": "Seven Killings", "乙": "Direct Officer", "丙": "Direct Resource", "丁": "Indirect Resource",
           "戊": "Friend", "己": "Rob Wealth", "庚": "Eating God", "辛": "Hurting Officer",
           "壬": "Indirect Wealth", "癸": "Direct Wealth"},
    "己": {"甲": "Direct Officer", "乙": "Seven Killings", "丙": "Indirect Resource", "丁": "Direct Resource",
           "戊": "Rob Wealth", "己": "Friend", "庚": "Hurting Officer", "辛": "Eating God",
           "壬": "Direct Wealth", "癸": "Indirect Wealth"},
    "庚": {"甲": "Indirect Wealth", "乙": "Direct Wealth", "丙": "Seven Killings", "丁": "Direct Officer",
           "戊": "Direct Resource", "己": "Indirect Resource", "庚": "Friend", "辛": "Rob Wealth",
           "壬": "Eating God", "癸": "Hurting Officer"},
    "辛": {"甲": "Direct Wealth", "乙": "Indirect Wealth", "丙": "Direct Officer", "丁": "Seven Killings",
           "戊": "Indirect Resource", "己": "Direct Resource", "庚": "Rob Wealth", "辛": "Friend",
           "壬": "Hurting Officer", "癸": "Eating God"},
    "壬": {"甲": "Eating God", "乙": "Hurting Officer", "丙": "Indirect Wealth", "丁": "Direct Wealth",
           "戊": "Seven Killings", "己": "Direct Officer", "庚": "Direct Resource", "辛": "Indirect Resource",
           "壬": "Friend", "癸": "Rob Wealth"},
    "癸": {"甲": "Hurting Officer", "乙": "Eating God", "丙": "Direct Wealth", "丁": "Indirect Wealth",
           "戊": "Direct Officer", "己": "Seven Killings", "庚": "Indirect Resource", "辛": "Direct Resource",
           "壬": "Rob Wealth", "癸": "Friend"}
}

def calculate_true_solar_time(year, month, day, hour, minute, longitude, timezone_name):
    timezone = ZoneInfo(timezone_name)
    local_dt = datetime(year, month, day, hour, minute, tzinfo=timezone)
    utc_offset = local_dt.utcoffset()
    dst_offset = local_dt.dst()
    if utc_offset is None:
        raise ValueError("timezone offset could not be resolved for birth datetime")

    # Civil time is anchored to the timezone's historical UTC offset at birth,
    # including DST when it was in effect.
    utc_offset_hours = utc_offset.total_seconds() / 3600
    standard_meridian = utc_offset_hours * 15.0

    # Local deviation from the civil-time meridian (4 minutes per degree).
    long_correction_min = (longitude - standard_meridian) * 4.0

    # Equation of Time (EoT) calculation for earth's orbital variance.
    day_of_year = local_dt.timetuple().tm_yday
    gamma = 2 * math.pi / 365 * (day_of_year - 1)
    eqtime = 229.18 * (0.000075 + 0.001868 * math.cos(gamma) - 0.032077 * math.sin(gamma)
                       - 0.014615 * math.cos(2*gamma) - 0.04089 * math.sin(2*gamma))

    total_correction = long_correction_min + eqtime
    solar_dt = local_dt + timedelta(minutes=total_correction)

    return {
        "original_time": f"{hour:02d}:{minute:02d}",
        "original_datetime": local_dt.isoformat(),
        "corrected_datetime": solar_dt.isoformat(),
        "corrected_year": solar_dt.year,
        "corrected_month": solar_dt.month,
        "corrected_day": solar_dt.day,
        "corrected_hour": solar_dt.hour,
        "corrected_minute": solar_dt.minute,
        "total_correction_min": round(total_correction, 2),
        "longitude_correction_min": round(long_correction_min, 2),
        "equation_of_time_min": round(eqtime, 2),
        "utc_offset_hours": round(utc_offset_hours, 2),
        "dst_offset_min": round((dst_offset.total_seconds() / 60) if dst_offset else 0, 2),
        "standard_meridian": round(standard_meridian, 2),
        "timezone": timezone_name,
        "note": f"True Solar Time computed using historical timezone offset for {timezone_name}"
    }

class BirthData(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "name": "User",
                "year": 1990,
                "month": 6,
                "day": 15,
                "hour": 12,
                "minute": 0,
                "gender": "female",
                "birthplace": "Seoul, South Korea",
                "latitude": 37.5665,
                "longitude": 126.9780,
                "timezone": "Asia/Seoul",
                "is_lunar": False
            }
        },
    )

    name: Annotated[str, Field(default="User", min_length=1, max_length=80, examples=["User"])]
    year: Annotated[StrictInt, Field(ge=1900, le=2100, examples=[1990])]
    month: Annotated[StrictInt, Field(ge=1, le=12, examples=[6])]
    day: Annotated[StrictInt, Field(ge=1, le=31, examples=[15])]
    hour: Annotated[StrictInt, Field(default=12, ge=0, le=23, examples=[12])]
    minute: Annotated[StrictInt, Field(default=0, ge=0, le=59, examples=[0])]
    gender: Literal["female", "male", "nonbinary", "other"] = "female"
    birthplace: Annotated[str, Field(min_length=2, max_length=120, examples=["Seoul, South Korea"])] | None = None
    latitude: Annotated[StrictFloat, Field(ge=-90, le=90, examples=[37.5665])]
    longitude: Annotated[StrictFloat, Field(ge=-180, le=180, examples=[126.9780])]
    timezone: Annotated[str, Field(min_length=1, max_length=64, examples=["Asia/Seoul"])]
    is_lunar: StrictBool = False

    @field_validator("name", "birthplace")
    @classmethod
    def validate_text_field(cls, value: str | None) -> str | None:
        if value is None:
            return value
        cleaned = " ".join(value.split())
        if not any(char.isalnum() for char in cleaned):
            raise ValueError("must contain at least one letter or number")
        return cleaned

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        cleaned = value.strip()
        try:
            ZoneInfo(cleaned)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("timezone must be a valid IANA timezone name") from exc
        return cleaned

    @model_validator(mode="after")
    def validate_birth_date(self):
        try:
            datetime(self.year, self.month, self.day, self.hour, self.minute)
        except ValueError as exc:
            raise ValueError(f"invalid birth date or time: {exc}") from exc
        return self

def enrich_birthplace(birthplace: str | None) -> tuple[str | None, str]:
    if birthplace is None:
        return None, "not_requested"

    geolocator = Nominatim(user_agent="sayu_saju_app")
    try:
        loc = geolocator.geocode(birthplace, timeout=5)
    except (GeocoderTimedOut, GeocoderUnavailable, GeocoderServiceError):
        return birthplace, "unavailable"

    if loc is None:
        return birthplace, "not_found"

    return loc.address, "enriched"

@app.post("/calculate-saju")
async def calculate_saju(data: BirthData):
    try:
        latitude = round(data.latitude, 4)
        longitude = round(data.longitude, 4)
        timezone = data.timezone
        location_name, birthplace_lookup_status = enrich_birthplace(data.birthplace)

        solar_time_info = calculate_true_solar_time(
            data.year,
            data.month,
            data.day,
            data.hour,
            data.minute,
            longitude,
            timezone,
        )
        use_year = solar_time_info["corrected_year"]
        use_month = solar_time_info["corrected_month"]
        use_day = solar_time_info["corrected_day"]
        use_hour = solar_time_info["corrected_hour"]
        use_minute = solar_time_info["corrected_minute"]

        # Chart Calculation
        if data.is_lunar:
            lunar = Lunar.fromYMDHMS(use_year, use_month, use_day, use_hour, use_minute, 0)
            solar = lunar.getSolar()
        else:
            solar = Solar.fromYmdHms(use_year, use_month, use_day, use_hour, use_minute, 0)
            lunar = solar.getLunar()

        eight_char = lunar.getEightChar()
        day_master_stem = eight_char.getDayGan()

        pillar_info = [
            ("year", eight_char.getYearGan(), eight_char.getYearZhi(), eight_char.getYearHideGan()),
            ("month", eight_char.getMonthGan(), eight_char.getMonthZhi(), eight_char.getMonthHideGan()),
            ("day", eight_char.getDayGan(), eight_char.getDayZhi(), eight_char.getDayHideGan()),
            ("hour", eight_char.getTimeGan(), eight_char.getTimeZhi(), eight_char.getTimeHideGan())
        ]

               # Pillars with Ten Gods + Hidden Stems
        pillars = {}
        for name, stem, branch, hidden in pillar_info:
            hidden_stems = list(hidden) if hidden else []
            # Calculate Ten God for main stem
            ten_god = ten_gods_full.get(day_master_stem, {}).get(stem, "N/A")
            # Calculate Ten Gods for hidden stems
            hidden_ten_gods = [ten_gods_full.get(day_master_stem, {}).get(hs, "N/A") for hs in hidden_stems]

            pillars[name] = {
                "stem": stem,
                "stem_english": stem_english.get(stem, stem),
                "branch": branch,
                "branch_english": branch_english.get(branch, branch),
                "hidden_stems": hidden_stems,
                "hidden_stems_english": [stem_english.get(h, h) for h in hidden_stems],
                "ten_god": ten_god,
                "hidden_ten_gods": hidden_ten_gods
            }

        response = {
            "status": "success",
            "gentle_note": "This chart is a gentle mirror for self-reflection and personal growth.",
            "user_metadata": {
                "name": data.name,
                "gender": data.gender,
                "birthplace": location_name,
                "latitude": latitude,
                "longitude": longitude,
                "timezone": timezone,
                "location_source": "trusted_request",
                "birthplace_lookup_status": birthplace_lookup_status
            },
            "true_solar_time": solar_time_info,
            "pillars": pillars,
            "day_master": day_master_stem,
            "timestamp": datetime.now().isoformat()
        }

        return response

    except HTTPException:
        raise
    except Exception:
        logger.exception("Unexpected error while calculating Saju chart")
        raise HTTPException(status_code=500, detail="Unable to calculate Saju chart at this time.")

@app.get("/health")
async def health():
    return {"status": "ok"}
