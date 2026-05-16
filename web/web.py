from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from web.back_end.routes.orders import router as orders_router
from web.back_end.routes.home import router as home_router
from web.back_end.routes.products import router as products_router
from web.back_end.routes.broadcast import router as broadcast_router
from web.back_end.routes.settings import router as settings_router
from web.back_end.routes.profile import router as profile_router
import os

app = FastAPI(title="AiGen Store Admin Dashboard")

# Mount folder frontend di /static agar CSS/JS bisa diakses
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "front_end")), name="static")

# Include API router
app.include_router(orders_router)
app.include_router(home_router)
app.include_router(products_router)
app.include_router(broadcast_router)
app.include_router(settings_router)
app.include_router(profile_router)

# Baca HTML index.html
HTML_PATH = os.path.join(os.path.dirname(__file__), "front_end", "html", "index.html")
with open(HTML_PATH, "r", encoding="utf-8") as f:
    DASHBOARD_HTML = f.read()

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return DASHBOARD_HTML
