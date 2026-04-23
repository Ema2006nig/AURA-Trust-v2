import os
import sqlite3
import psycopg2
import qrcode
from datetime import datetime
from io import BytesIO
from fastapi import FastAPI, Form, Request, Response
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader

app = FastAPI()

# --- CONFIGURATION DES CHEMINS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

# On initialise les templates, mais on prépare un mode secours
try:
    templates = Jinja2Templates(directory=TEMPLATES_DIR)
except Exception:
    templates = None

# --- RÉCUPÉRATION DES VARIABLES D'ENVIRONNEMENT ---
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "code_par_defaut_7172")
DATABASE_URL = os.getenv("DATABASE_URL")

@app.on_event("startup")
def init_db():
    # Création de la base locale de secours
    try:
        conn = sqlite3.connect("backup.db")
        conn.execute("CREATE TABLE IF NOT EXISTS certs (id TEXT, name TEXT, type TEXT, date TEXT)")
        conn.commit()
        conn.close()
        print("✅ Base de données locale prête.")
    except:
        pass

# --- LA ROUTE DE TEST (ACCUEIL) ---
@app.get("/")
async def home(request: Request):
    """
    Cette route essaie d'afficher index.html. 
    Si elle échoue, elle affiche un message de diagnostic au lieu d'une erreur 500.
    """
    try:
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        return JSONResponse({
            "status": "Le serveur fonctionne ! ✅",
            "erreur": "Le fichier 'index.html' est introuvable ou mal placé.",
            "detail_technique": str(e),
            "conseil": "Vérifie que ton dossier sur GitHub s'appelle bien 'templates' (avec un s)."
        })

@app.post("/generate")
async def generate(request: Request, name: str = Form(...), cert_type: str = Form(...), password: str = Form(...)):
    if password != ADMIN_PASSWORD:
        return HTMLResponse("❌ Mot de passe incorrect", status_code=403)
    
    cert_id = f"AURA-{os.urandom(3).hex().upper()}"
    date_str = datetime.now().strftime("%d/%m/%Y")
    
    # Sauvegarde simple
    try:
        conn = sqlite3.connect("backup.db")
        conn.execute("INSERT INTO certs VALUES (?, ?, ?, ?)", (cert_id, name, cert_type, date_str))
        conn.commit()
        conn.close()
    except: pass
    
    return templates.TemplateResponse("result.html", {"request": request, "cert_id": cert_id, "name": name})

@app.get("/verify/{cert_id}")
async def verify(request: Request, cert_id: str):
    try:
        conn = sqlite3.connect("backup.db")
        data = conn.execute("SELECT name, type, date FROM certs WHERE id = ?", (cert_id,)).fetchone()
        conn.close()
        return templates.TemplateResponse("verify.html", {"request": request, "cert_id": cert_id, "data": data})
    except:
        return JSONResponse({"erreur": "Impossible de charger la page de vérification"})
