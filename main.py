import os
import sqlite3
from fastapi import FastAPI, Form, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

app = FastAPI()

# Configuration ultra-simple des templates
# On cherche le dossier 'templates' au même niveau que ce fichier
templates = Jinja2Templates(directory="templates")

# Variable pour le mot de passe (à configurer sur Render)
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "7172")

@app.on_event("startup")
def startup():
    # Crée la base de données au démarrage
    conn = sqlite3.connect("database.db")
    conn.execute("CREATE TABLE IF NOT EXISTS certs (id TEXT, name TEXT, type TEXT)")
    conn.commit()
    conn.close()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    # Syntaxe moderne pour éviter les erreurs de dictionnaire
    return templates.TemplateResponse(
        request=request, name="index.html", context={}
    )

@app.post("/generate", response_class=HTMLResponse)
async def generate(request: Request, name: str = Form(...), cert_type: str = Form(...), password: str = Form(...)):
    if password != ADMIN_PASSWORD:
        return HTMLResponse("❌ Mot de passe incorrect", status_code=403)
    
    cert_id = os.urandom(3).hex().upper()
    conn = sqlite3.connect("database.db")
    conn.execute("INSERT INTO certs VALUES (?, ?, ?)", (cert_id, name, cert_type))
    conn.commit()
    conn.close()
    
    return templates.TemplateResponse(
        request=request, name="result.html", context={"cert_id": cert_id, "name": name}
    )
