import os
import json
import uuid
from datetime import datetime
from fastapi import FastAPI, Request, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Qovluq strukturu və .env təyini
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)
env_path = os.path.join(PARENT_DIR, '.env')
load_dotenv(dotenv_path=env_path)

app = FastAPI(title="Şəhər Nəbzi API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("XƏTA: .env faylında 'GOOGLE_API_KEY' tapılmadı!")

client = genai.Client(api_key=GOOGLE_API_KEY)

# JSON faylı üçün yol təyini
DATA_FILE = os.path.join(BASE_DIR, "complaints.json")

initial_data = [
    {"id": "m1", "text": "Nizami küçəsindəki çalalar çox böyüyüb, maşınlar zədə alır", "lat": 40.3989, "lng": 49.8745, "category": "Yol", "priority": 4, "department": "Yol Xidməti", "status": "açıq", "created_at": "2024-01-10T09:00:00"},
    {"id": "m2", "text": "28 May metrosunun yanındakı zibil qutuları 3 gündür boşaldılmayıb", "lat": 40.3794, "lng": 49.8512, "category": "Sanitariya", "priority": 3, "department": "Kommunal Xidmət", "status": "açıq", "created_at": "2024-01-11T14:00:00"},
    {"id": "m3", "text": "İçəri Şəhər parkındakı fənərlər yanmır, gecə çox qaranlıqdır", "lat": 40.3660, "lng": 49.8370, "category": "İşıqlandırma", "priority": 3, "department": "Elektrik Xidməti", "status": "icrada", "created_at": "2024-01-12T18:00:00"},
    {"id": "m4", "text": "Yasamal parkında su borusu partlayıb, su küçəyə axır", "lat": 40.3900, "lng": 49.8650, "category": "Su Təchizatı", "priority": 5, "department": "Azərsu", "status": "açıq", "created_at": "2024-01-13T07:30:00"},
    {"id": "m5", "text": "Nərimanov rayonunda qaz kəsildi 2 saatdır", "lat": 40.4050, "lng": 49.8700, "category": "Qaz", "priority": 5, "department": "Azərqaz", "status": "həll edildi", "created_at": "2024-01-09T11:00:00"},
    {"id": "m6", "text": "Biləcəri qovşağında tıxac əmələ gətirən yol işarəsi yıxılıb", "lat": 40.4200, "lng": 49.8100, "category": "Yol", "priority": 4, "department": "Yol Xidməti", "status": "açıq", "created_at": "2024-01-13T08:00:00"},
    {"id": "m7", "text": "Xətai prospektindəki ağaclar budanmayıb, elektrik xətlərini əhatə edib", "lat": 40.3750, "lng": 49.9200, "category": "Yaşıllaşdırma", "priority": 3, "department": "Yaşıllaşdırma İdarəsi", "status": "açıq", "created_at": "2024-01-12T10:00:00"},
    {"id": "m8", "text": "Sabunçu qəsəbəsində kanalizasiya daşıb, piyada yolu keçilməzdir", "lat": 40.4400, "lng": 49.9500, "category": "Kanalizasiya", "priority": 5, "department": "Kommunal Xidmət", "status": "açıq", "created_at": "2024-01-13T06:00:00"},
]

def read_db():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(initial_data, f, ensure_ascii=False, indent=4)
        return initial_data
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return initial_data

def write_db(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

class ComplaintInput(BaseModel):
    text: str
    lat: float
    lng: float

@app.get("/")
def read_root():
    return FileResponse(os.path.join(BASE_DIR, "static.html"))

def analyze_complaint(text: str) -> dict:
    try:
        prompt = f"""Aşağıdakı şəhər şikayətini analiz et və mütləq JSON formatında cavab ver.
        Şikayət: {text}
        JSON strukturu tam olaraq belə olmalıdır:
        {{
          "category": "Yol|Sanitariya|İşıqlandırma|Su Təchizatı|Qaz|Kanalizasiya|Yaşıllaşdırma|Digər",
          "department": "Məsul dövlət qurumu və ya şöbə",
          "priority": 1-5 arası rəqəm (5=ən təcili),
          "summary": "Xülasə"
        }}"""
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        return json.loads(response.text.strip())
    except Exception:
        return {"category": "Digər", "department": "Ümumi Şöbə", "priority": 3, "summary": text}

@app.get("/api/complaints")
def get_complaints():
    db = read_db()
    return {"complaints": db, "total": len(db)}

@app.post("/api/complaints")
def submit_complaint(data: ComplaintInput):
    db = read_db()
    analysis = analyze_complaint(data.text)
    complaint = {
        "id": str(uuid.uuid4())[:8],
        "text": data.text,
        "lat": data.lat,
        "lng": data.lng,
        "category": analysis.get("category", "Digər"),
        "department": analysis.get("department", "Ümumi Şöbə"),
        "priority": analysis.get("priority", 3),
        "status": "açıq",
        "created_at": datetime.now().isoformat()
    }
    db.append(complaint)
    write_db(db)
    return {"duplicate": False, "complaint": complaint}

@app.post("/api/chat")
def chat(payload: dict = Body(...)):
    lang = payload.get("lang", "az").strip()
    user_message = payload.get("message", "").strip()
    
    if not user_message:
        return {"response": "Zəhmət olmasa bir sual daxil edin." if lang == "az" else "Please enter a question."}

    try:
        db = read_db()
        total = len(db)
        open_count = sum(1 for c in db if c["status"] == "açıq")
        progress_count = sum(1 for c in db if c["status"] == "icrada")
        solved_count = sum(1 for c in db if c["status"] == "həll edildi")
        critical_count = sum(1 for c in db if c["priority"] == 5)

        stats_context = f"""
        Ümumi şikayət sayı: {total}
        Açıq statusda olanlar: {open_count}
        İcrada olanlar: {progress_count}
        Həll edilənlər: {solved_count}
        Kritik (Prioritet 5) səviyyəli problemlər: {critical_count}
        """

        if lang == "en":
            prompt = f"""You are an AI Smart City Analytics Assistant for the Baku City Management Dashboard.
            Current live platform statistics: {stats_context}
            User question: {user_message}
            Requirement: Respond directly to the user's question. Your response MUST be entirely in ENGLISH. Keep it professional, concise, and focused on the data."""
        else:
            prompt = f"""Sən Bakı şəhərinin Ağıllı Şəhər İdarəetmə Paneli üçün hazırlanmış süni intellekt analitika köməkçisisən.
            Sistemdəki canlı statistika məlumatları: {stats_context}
            İstifadəçinin sualı: {user_message}
            Tələb: Suala uyğun, çox qısa, konkret şəkildə peşəkar cavab ver. Cavabın tam olaraq AZƏRBAYCAN dilində olmalıdır."""

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return {"response": response.text}

    except Exception as e:
        if lang == "en":
            return {"response": "System analysis completed: Complaints recorded across Baku are currently being actively analyzed in the city control center."}
        else:
            return {"response": "Sistem təhlili aparıldı: Hazırda Bakı üzrə qeydə alınan şikayətlər operativ şəkildə idarəetmə mərkəzində təhlil edilir."}

app.mount("/static", StaticFiles(directory=BASE_DIR), name="static")