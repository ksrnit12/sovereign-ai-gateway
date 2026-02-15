import uuid
import uvicorn
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from intelligence_engine import IntelligenceEngine

app = FastAPI(title="Sovereign AI Gateway API")
engine = IntelligenceEngine()
job_store = {}

class QueryRequest(BaseModel):
    messages: List[Dict[str, str]]
    department: str = "marketing"

def background_processor(job_id: str, messages: List[Dict[str, str]], dept: str):
    try:
        prompt = messages[-1]["content"] if messages else ""
        result = engine.process(prompt, dept)
        job_store[job_id] = result
    except Exception as e:
        job_store[job_id] = {"status": "ERROR", "output": str(e)}

@app.post("/submit")
async def submit(req: QueryRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    job_store[job_id] = {"status": "PROCESSING"}
    background_tasks.add_task(background_processor, job_id, req.messages, req.department)
    return {"request_id": job_id, "status": "QUEUED"}

@app.get("/status/{request_id}")
def get_status(request_id: str):
    job = job_store.get(request_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.get("/health")
def health():
    return {"status": "healthy", "service": "Sovereign AI Gateway"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
