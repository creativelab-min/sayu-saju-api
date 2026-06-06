# Sayu Saju API — Usage Examples

This document shows how to use the Sayu Saju API effectively.

---

## Base URL
https://sayu-saju-api.onrender.com


**Interactive Swagger Docs**: [https://sayu-saju-api.onrender.com/docs](https://sayu-saju-api.onrender.com/docs)

---

## 1. Calculate Saju Chart (Main Endpoint)

**POST** `/calculate-saju`

### Example Request (Solar Calendar - Recommended)

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

### Example Request (Solar Calendar

```json
{
  "name": "JM Test",
  "year": 1989,
  "month": 6,
  "day": 18,
  "hour": 13,
  "minute": 0,
  "gender": "female",
  "birthplace": "Seoul, Korea",
  "is_lunar": true
}

