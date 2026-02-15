import sqlite3
import uuid
import os
from contextlib import contextmanager
from fastapi import FastAPI, BackgroundTasks, HTTPException, Security, Depends, Request
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
from typing import List, Dict
from intelligence_engine import IntelligenceEngine
from datetime import datetime
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# CONFIGURATION
API_KEY_NAME = "x-api-key"
API_KEY = os.getenv("GATEWAY_API_KEY", "default-dev-key") 
MAX_INPUT_TOKENS = 4000

# SETUP
limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)
engine = None 

def get_engine():
    global engine
    if engine is None:
        engine = IntelligenceEngine()
    return engine

async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == API_KEY:
        return api_key_header
    raise HTTPException(status_code=403, detail="Invalid API Key")

@contextmanager
def get_db_connection():
    conn = sqlite3.connect("gateway_vault.db", check_same_thread=False)
    try:
        yield conn
    finally:
        conn.close()

with get_db_connection() as conn:
    conn.execute('CREATE TABLE IF NOT EXISTS audit_logs (id TEXT PRIMARY KEY, timestamp DATETIME, model TEXT, savings REAL, verdict TEXT, output TEXT)')
    conn.commit()

class Query(BaseModel):
    messages: List[Dict[str, str]]
    department: str
    
    def check_length(self):
        total_chars = sum(len(m['content']) for m in self.messages)
        if total_chars / 4 > MAX_INPUT_TOKENS:
            raise ValueError(f"Input exceeds {MAX_INPUT_TOKENS} tokens")

@app.post("/submit")
@limiter.limit("60/minute")
async def submit(request: Request, query: Query, bt: BackgroundTasks, api_key: str = Depends(get_api_key)):
    try:
        query.check_length()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    req_id = str(uuid.uuid4())
    bt.add_task(run_pipeline, req_id, query.messages, query.department, get_engine())
    return {"request_id": req_id, "status": "queued"}

def run_pipeline(req_id, messages, dept, engine_instance):
    try:
        res = engine_instance.process(messages, dept)
        with get_db_connection() as conn:
            conn.execute(
                'INSERT INTO audit_logs VALUES (?, ?, ?, ?, ?, ?)',
                (req_id, datetime.now(), res.get("model_used"), res.get("savings", 0), res.get("verdict"), res.get("output"))
            )
            conn.commit()
    except Exception as e:
        print(f"Pipeline Error {req_id}: {e}")

@app.get("/status/{req_id}")
async def get_status(req_id: str, api_key: str = Depends(get_api_key)):
    with get_db_connection() as conn:
        cursor = conn.execute("SELECT output, model, verdict, savings FROM audit_logs WHERE id=?", (req_id,))
        row = cursor.fetchone()
    if row:
        return {"status": "COMPLETED", "output": row[0], "model": row[1], "verdict": row[2], "savings": row[3]}
    return {"status": "PROCESSING"}

@app.get("/metrics")
async def get_metrics(api_key: str = Depends(get_api_key)):
    with get_db_connection() as conn:
        row = conn.execute("SELECT SUM(savings), COUNT(*) FROM audit_logs").fetchone()
    return {"total_savings": row[0] or 0.0, "total_queries": row[1] or 0}
