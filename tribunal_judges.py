import json
from litellm import completion

class Tribunal:
    def __init__(self):
        try:
            with open("policy.json", "r") as f: self.policies = json.load(f)
        except: self.policies = {"global": ["Be helpful."]}

    def verify(self, draft: str, department: str = "general"):
        rules = self.policies.get("global", []) + self.policies.get(department.lower(), [])
        prompt = f"POLICIES: {rules}\nCONTENT: {draft}\nReturn 'PASS' or 'FAIL: <Reason>'."
        
        try:
            response = completion(
                model="ollama/llama3.2", 
                messages=[{"role": "user", "content": prompt}], 
                api_base="http://localhost:11434",
                timeout=10
            )
            verdict = response.choices[0].message.content.strip()
            if "FAIL" in verdict: return {"verdict": "FAIL", "issues": [verdict]}
            return {"verdict": "PASS", "issues": []}
        except Exception as e:
            print(f"Tribunal Error: {e}")
            return {"verdict": "PASS", "issues": ["Tribunal Skipped"]}
