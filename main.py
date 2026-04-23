import os
import sqlite3
import qrcode
from datetime import datetime
from io import BytesIO
from fastapi import FastAPI, Form, Request, Response
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader

app = FastAPI()

# --- CONFIGURATION DES TEMPLATES ---
# On utilise le chemin le plus direct possible
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# --- MOT DE PASSE (Récupéré depuis Render Environment) ---
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "code7172")

# --- BASE DE DONNÉES ---
@app.on_event("startup")
def init_db():
    conn = sqlite3.connect("database.db")
    conn.execute("CREATE TABLE IF NOT EXISTS certs (id TEXT, name TEXT, type TEXT, date TEXT)")
    conn.commit()
    conn.close()

# --- ROUTES ---

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    # C'est cette ligne qui cherche 'templates/index.html'
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate", response_class=HTMLResponse)
async def generate(request: Request, name: str = Form(...), cert_type: str = Form(...), password: str = Form(...)):
    if password != ADMIN_PASSWORD:
        return HTMLResponse("❌ Mot de passe incorrect", status_code=403)
    
    cert_id = f"AURA-{os.urandom(3).hex().upper()}"
    date_str = datetime.now().strftime("%d/%m/%Y")
    
    conn = sqlite3.connect("database.db")
    conn.execute("INSERT INTO certs VALUES (?, ?, ?, ?)", (cert_id, name, cert_type, date_str))
    conn.commit()
    conn.close()
    
    return templates.TemplateResponse("result.html", {"request": request, "cert_id": cert_id, "name": name})

@app.get("/verify/{cert_id}", response_class=HTMLResponse)
async def verify(request: Request, cert_id: str):
    conn = sqlite3.connect("database.db")
    data = conn.execute("SELECT name, type, date FROM certs WHERE id = ?", (cert_id,)).fetchone()
    conn.close()
    return templates.TemplateResponse("verify.html", {"request": request, "cert_id": cert_id, "data": data})

@app.get("/download/{cert_id}")
async def download(cert_id: str):
    conn = sqlite3.connect("database.db")
    data = conn.execute("SELECT name, type, date FROM certs WHERE id = ?", (cert_id,)).fetchone()
    conn.close()
    
    if not data: return Response(status_code=404)
    
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    p.setFont("Helvetica-Bold", 25)
    p.drawCentredString(297, 750, "CERTIFICAT AURA TRUST")
    p.setFont("Helvetica", 18)
    p.drawCentredString(297, 500, data[0].upper())
    p.save()
    buffer.seek(0)
    return Response(content=buffer.getvalue(), media_type="application/pdf")
