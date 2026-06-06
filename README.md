# Sayu Saju API

**🌿 Gentle AI-powered Four Pillars (Saju) calculator for self-understanding**

A clean, accurate, and reflective backend API for the Sayu app — built for modern self-reflection, not fortune-telling.

---

## 🌟 About Sayu

Sayu turns traditional Saju (Four Pillars of Destiny) into a modern tool for self-understanding. It combines accurate chart calculation with CBT-informed reflection and empathetic guidance.

**Core Principle**:  
> “This chart is a gentle mirror for self-reflection and personal growth.”

---

## ✨ Current Features

- Accurate Four Pillars (Year, Month, Day, Hour)
- Solar + Lunar calendar support
- Advanced True Solar Time adjustment (longitude + Equation of Time)
- Hidden Stems (藏干)
- **Complete Ten Gods** (main stems + hidden stems)
- Five Elements distribution
- DaYun (Luck Cycles) — first 8 cycles with age ranges
- Annual Cycles (세운)
- **Pillar Interactions** — Clash (冲), Combination (合), Harm (害), Punishment (刑)
- Luck Cycle Interactions
- Gentle, non-predictive language
- English-first output with Korean character support

---

## 🚀 API Endpoints

### POST `/calculate-saju`

**Request Body Example:**

```json
{
  "name": "Test User",
  "year": 1989,
  "month": 7,
  "day": 20,
  "hour": 13,
  "minute": 0,
  "gender": "female",
  "birthplace": "Seoul, Korea",
  "is_lunar": false
}
