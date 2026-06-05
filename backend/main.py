from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from database import engine
import models

# Crear todas las tablas al iniciar
models.Base.metadata.create_all(bind=engine)

from routers import usuarios, materiales, solicitudes, aprobaciones, bodega, dashboard, reportes, alertas, lineas

app = FastAPI(
    title="Novum GLP – Sistema de Requerimientos de Materiales",
    version="1.0.0",
    description="Sistema web para gestión de requerimientos de materia prima para Corporación Novum",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers de la API
app.include_router(usuarios.router)
app.include_router(materiales.router)
app.include_router(solicitudes.router)
app.include_router(aprobaciones.router)
app.include_router(bodega.router)
app.include_router(dashboard.router)
app.include_router(reportes.router)
app.include_router(alertas.router)
app.include_router(lineas.router)

# Servir el frontend estático
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=os.path.join(frontend_path, "css")), name="css")
    app.mount("/js", StaticFiles(directory=os.path.join(frontend_path, "js")), name="js")

    _no_cache = {"Cache-Control": "no-store, no-cache, must-revalidate", "Pragma": "no-cache"}

    @app.get("/")
    def serve_index():
        return FileResponse(os.path.join(frontend_path, "index.html"), headers=_no_cache)

    @app.get("/{page}.html")
    def serve_page(page: str):
        filepath = os.path.join(frontend_path, f"{page}.html")
        if os.path.exists(filepath):
            return FileResponse(filepath, headers=_no_cache)
        return FileResponse(os.path.join(frontend_path, "index.html"), headers=_no_cache)
