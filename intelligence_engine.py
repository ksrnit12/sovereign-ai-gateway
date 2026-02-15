from compliance_airlock import ComplianceAirlock
from tribunal_judges import Tribunal
from litellm import completion
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from tenacity import retry, stop_after_attempt, wait_exponential
import numpy as np
from typing import List, Dict

class IntelligenceEngine:
    def __init__(self):
        self.airlock = ComplianceAirlock()
        self.tribunal = Tribunal()
        print("🧠 Loading Semantic Router...")
        self.router_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.routes = {
            "engineering": ["write python code", "debug error", "aws lambda", "sql query", "api implementation"],
            "general": ["write email", "summarize text", "marketing copy", "meeting notes"]
        }
        self.route_embeddings = {k: self.router_model.encode(v) for k, v in self.routes.items()}

    def _get_route(self, text):
        emb = self.router_model.encode([text])
        scores = {k: np.max(cosine_similarity(emb, v)) for k, v in self.route_embeddings.items()}
        return max(scores, key=scores.get)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def _call_llm(self, model, messages):
        return completion(model=model, messages=messages, timeout=30)

    def process(self, messages: List[Dict[str, str]], user_dept: str = "general"):
        last_msg = messages[-1]["content"]
        sanitized = self.airlock.sanitize(last_msg)
        
        if sanitized["risk_level"] == "HIGH":
            return {
                "output": "🚨 BLOCKED: Active credentials detected.",
                "model_used": "BLOCKED",
                "verdict": "FAIL",
                "savings": 0.0
            }

        messages[-1]["content"] = sanitized["safe_text"]
        intent = self._get_route(sanitized["safe_text"])
        
        if intent == "engineering":
            model = "openai/gpt-4o"
            savings = 0.0
        else:
            model = "openai/gpt-4o-mini"
            savings = 0.027

        try:
            response = self._call_llm(model, messages)
            draft = response.choices[0].message.content
        except Exception as e:
            return {"output": f"LLM Error: {str(e)}", "verdict": "ERROR"}

        audit = self.tribunal.verify(draft, department=user_dept)
        final_out = draft if audit["verdict"] == "PASS" else f"🚫 BLOCKED: {audit['issues'][0]}"

        return {
            "output": final_out,
            "model_used": model,
            "pii_scrubbed": sanitized["was_scrubbed"],
            "savings": savings,
            "verdict": audit["verdict"]
        }
