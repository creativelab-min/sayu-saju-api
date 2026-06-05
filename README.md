# Sayu Saju API

**Gentle AI-powered Four Pillars (Saju) calculator for self-understanding**

A clean, accurate backend API for the Sayu app — focused on **reflection**, not fortune-telling.

---

## 🌿 About Sayu

Sayu helps users explore their personality patterns, strengths, and growth areas through traditional Saju (Four Pillars of Destiny), presented in a modern, empathetic, and CBT-informed way.

**Core Principle**:  
> "This chart offers a lens for gentle self-reflection."

---

## ✨ Features

- Accurate Four Pillars calculation (Year, Month, Day, Hour)
- Support for both **Solar** and **Lunar** calendar input
- Birthplace geocoding (longitude/latitude for better accuracy)
- Hidden Stems (藏干)
- **Complete Ten Gods (십신)** with English names and descriptions
- Five Elements distribution
- Luck Cycles (DaYun / 대운) — first 8 cycles with age ranges
- Fully English output with calm, reflective tone
- FastAPI + `lunar-python` backend

---

## 🚀 API Endpoints

### POST `/calculate-saju`

**Request Body:**

```json
{
  "name": "JM Test",
  "year": 1989,
  "month": 7,
  "day": 20,
  "hour": 13,
  "minute": 0,
  "gender": "female",
  "birthplace": "Seoul, Korea",
  "is_lunar": false
}
