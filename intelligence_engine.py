import os
import logging
from dotenv import load_dotenv
from litellm import completion
from compliance_airlock import ComplianceAirlock
from tribunal_judges import Tribunal

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntelligenceEngine:
    def __init__(self):
        self.airlock = ComplianceAirlock()
        self.tribunal = Tribunal()
        self.FAST_MODEL = "openai/gpt-4o-mini" 
        self.SMART_MODEL = "openai/gpt-4o"
        
        # Verify OpenAI key is set
        if not os.getenv("OPENAI_API_KEY"):
            logger.error("❌ OPENAI_API_KEY not set in environment!")
        else:
            logger.info("✅ Intelligence Engine initialized")

    def process(self, prompt: str, user_dept: str = "marketing"):
        """
        Process a user prompt through the complete governance pipeline.
        
        Args:
            prompt: User input text
            user_dept: Department context for routing
            
        Returns:
            dict: Complete result with status, output, and metadata
        """
        
        # 1. COMPLIANCE SHIELD
        sanitization = self.airlock.sanitize(prompt)
        safe_prompt = sanitization["safe_text"]
        
        # 🛑 HIGH RISK BLOCK (Active Credentials Detected)
        if sanitization.get("risk_level") == "HIGH":
            found = ", ".join(sanitization.get("entities_found", []))
            logger.error(f"🚨 HIGH RISK BLOCK: {found}")
            return {
                "status": "COMPLETED",
                "output": f"🚨 **SECURITY BLOCK**\n\nActive credentials detected: {found}\n\nRequest blocked for security.",
                "model_used": "BLOCKED",
                "safe_prompt": "[REDACTED FOR SECURITY]",
                "pii_scrubbed": True,
                "entities_found": sanitization.get("entities_found", []),
                "savings": 0.0,
                "verdict": "FAIL",
                "sanitization_method": sanitization.get("method", "Unknown")
            }
        
        # ⚠️ MEDIUM RISK ALERT (PII Redacted, continuing)
        if sanitization.get("risk_level") == "MEDIUM":
            logger.warning(f"⚠️ PII Detected & Redacted: {sanitization.get('entities_found')}")

        # 2. INTELLIGENT ROUTER
        # Use semantic analysis to determine complexity
        is_complex = (
            user_dept == "engineering" or 
            any(keyword in safe_prompt.lower() for keyword in ["code", "debug", "algorithm", "function", "script"])
        )
        
        model = self.SMART_MODEL if is_complex else self.FAST_MODEL
        
        # Calculate savings (GPT-4o vs GPT-4o-mini)
        # Assuming ~500 tokens avg: $0.03/1K vs $0.003/1K = $0.027 saved
        savings = 0.027 if not is_complex else 0.0
        
        logger.info(f"🧠 Routing to {model} (dept={user_dept}, complex={is_complex})")

        # 3. LLM EXECUTION
        try:
            response = completion(
                model=model, 
                messages=[{"role": "user", "content": safe_prompt}],
                timeout=30
            )
            draft = response.choices[0].message.content
        except Exception as e:
            logger.error(f"❌ LLM Error: {e}")
            return {
                "status": "ERROR", 
                "output": f"⚠️ API Error: {str(e)}\n\nPlease check your OpenAI API key and try again.",
                "model_used": model,
                "safe_prompt": safe_prompt,
                "pii_scrubbed": sanitization["was_scrubbed"],
                "entities_found": sanitization.get("entities_found", []),
                "savings": 0.0,
                "verdict": "ERROR",
                "sanitization_method": sanitization.get("method", "Unknown")
            }

        # 4. TRIBUNAL VALIDATION
        verdict = self.tribunal.verify(draft)
        
        # Prepare final output
        if verdict["verdict"] == "PASS":
            final_output = draft
        else:
            logger.warning(f"🚫 Tribunal blocked: {verdict['issues']}")
            final_output = f"🚫 **BLOCKED BY TRIBUNAL**\n\nReason: {verdict['issues'][0]}"
        
        return {
            "status": "COMPLETED",
            "output": final_output,
            "model_used": model,
            "safe_prompt": safe_prompt,
            "pii_scrubbed": sanitization["was_scrubbed"],
            "entities_found": sanitization.get("entities_found", []),
            "savings": savings,
            "verdict": verdict["verdict"],
            "sanitization_method": sanitization.get("method", "Unknown")
        }
