import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import text
from loguru import logger
import requests

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR))
if PARENT_DIR not in sys.path:
    sys.path.append(PARENT_DIR)

# Import the SQLAlchemy engine and our schema initializer
from backend.database.connection import engine, init_db_schema
from backend.etl.pipeline import run_etl_job
from backend.ai.copilot import LlamaCopilot as FinancialCopilot


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages application startup and shutdown lifecycle events.
    Ensures database tables/indexes are created before handling traffic.
    """
    logger.info("[Startup] Initiating backend services...")
    try:
        # Automatically run our DDL setup check on boot
        schema_ready = init_db_schema()
        if schema_ready:
            logger.info("[Startup] Database infrastructure validated and ready.")
        else:
            logger.warning("[Startup] Database schema check skipped (schema.sql might be missing).")
    except Exception as e:
        logger.critical(f"[Startup] Database schema initialization failed: {e}")
        # We let the server start up so it can serve a degraded /health check,
        # but ONE can also choose to raise/exit here.

    yield  # Application handles requests here

    logger.info("[Shutdown] Tearing down backend services...")


app = FastAPI(
    title="SelFlow Enterprise Financial Data Engine",
    description="FastAPI Backend with Local LLM Integration",
    version="1.0.0",
    lifespan=lifespan  # Attach the lifecycle manager
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

copilot = FinancialCopilot()

# Standardize base URL and fallbacks
BASE_LLM_URL = os.getenv("LOCAL_LLM_URL", "http://host.docker.internal:11434").rstrip("/")
LLAMA_MODEL = os.getenv("LLAMA_MODEL", "llama2:latest")

class ETLResponse(BaseModel):
    status: str
    message: str
    target_file: str

class QueryRequest(BaseModel):
    question: str

class LLMQueryRequest(BaseModel):
    prompt: str

SCHEMA_CONTEXT = """You are a PostgreSQL expert. Convert user questions to SQL after that provide data insights with Visualizations whenever asked.
Database: staging_transactions
Columns: transaction_id, amount, type, status, created_at, customer_id, transaction_date, value_tier
Return raw SQL then data insights with Visualizations whenever asked. No markdown. No explanation."""


@app.get("/health", tags=["Monitoring"])
def health_check():
    db_status = "unhealthy"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1;"))
            db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")

    return {
        "status": "online",
        "services": {
            "database": db_status,
            "api": "healthy"
        }
    }


@app.post("/etl/trigger", response_model=ETLResponse, tags=["Orchestration"])
def trigger_etl(background_tasks: BackgroundTasks):
    raw_path = os.getenv("RAW_DATA_PATH")
    
    if not raw_path or not os.path.exists(raw_path):
        raise HTTPException(status_code=400, detail="CSV file not found")
    
    background_tasks.add_task(run_etl_job)
    
    return ETLResponse(
        status="initiated",
        message="ETL engine running in background",
        target_file=raw_path
    )


@app.get("/metrics", tags=["Monitoring"])
def get_database_metrics():
    try:
        # Switched staging_transactions query to point to your new warehouse fact_transactions table
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT COUNT(*) FROM fact_transactions LIMIT 1;"
            )).fetchone()
            
            return {
                "total_rows_stored": result[0] if result else 0,
                "status": "ready"
            }
    except Exception as e:
        logger.error(f"Metrics fetch failed: {str(e)}")
        return {"total_rows_stored": 0, "status": "no_data"}


@app.post("/ai/query", tags=["AI Copilot"])
def query_llama(payload: LLMQueryRequest):
    """Query local Llama model for SQL generation and data retrieval"""
    full_prompt = f"{SCHEMA_CONTEXT}\n\nQuestion: {payload.prompt}\n\nSQL:"
    
    # Construct clean API endpoint: http://host.docker.internal:11434/api/generate
    generate_endpoint = f"{BASE_LLM_URL}/api/generate"
    
    try:
        logger.info(f"Querying Model: '{LLAMA_MODEL}' at endpoint: '{generate_endpoint}'")
        
        response = requests.post(
            generate_endpoint,
            json={
                "model": LLAMA_MODEL,
                "prompt": full_prompt,
                "stream": False,
                "options": {"temperature": 0.1}
            },
            timeout=30
        )
        
        # Capture raw error responses to aid troubleshooting
        if response.status_code != 200:
            logger.error(f"Ollama returned an error status: {response.status_code}. Response: {response.text}")
            raise HTTPException(status_code=response.status_code, detail=f"Ollama Error: {response.text}")
        
        generated_sql = response.json().get("response", "").strip()
        
        if "```" in generated_sql:
            generated_sql = generated_sql.split("```")[1].replace("sql", "").strip()
        
        logger.info(f"Generated SQL: {generated_sql}")
        
        with engine.connect() as conn:
            result = conn.execute(text(generated_sql))
            columns = list(result.keys())
            rows = [dict(zip(columns, row)) for row in result.fetchall()]
        
        return {
            "success": True,
            "sql": generated_sql,
            "data": rows[:100],
            "row_count": len(rows)
        }
        
    except requests.exceptions.ConnectionError:
        logger.error(f"Local LLM unreachable at {generate_endpoint}")
        raise HTTPException(status_code=503, detail="Ollama not running. Start it first.")
    except Exception as e:
        logger.error(f"Query failed: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.api.main:app", host="0.0.0.0", port=8000, reload=True)