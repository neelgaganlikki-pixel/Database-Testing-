import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from app.routes import customers, products, categories, cart, orders, payments
from database.connection import execute_select
from utils.logger import logger

app = FastAPI(
    title="E-Commerce Database Test Automation Application",
    description="Local E-Commerce REST API & Frontend for comprehensive Database, API, and UI Automation Testing",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(customers.router)
app.include_router(products.router)
app.include_router(categories.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(payments.router)

# Static and UI Setup
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
if not STATIC_DIR.exists():
    STATIC_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/", include_in_schema=False)
def serve_home():
    """Serves the main single page e-commerce frontend."""
    return FileResponse(str(STATIC_DIR / "index.html"))

@app.get("/health", tags=["Health"])
def health_check():
    """Application and database health check."""
    try:
        res = execute_select("SELECT 1 as is_alive;")
        db_alive = bool(res and res[0]["is_alive"] == 1)
    except Exception as e:
        logger.error(f"Health check DB error: {e}")
        db_alive = False

    return {
        "status": "healthy" if db_alive else "degraded",
        "database_connected": db_alive,
        "app": "ecommerce_test_app"
    }

if __name__ == "__main__":
    import uvicorn
    from config.db_config import DBConfig
    uvicorn.run("app.main:app", host=DBConfig.APP_HOST, port=DBConfig.APP_PORT, reload=True)
