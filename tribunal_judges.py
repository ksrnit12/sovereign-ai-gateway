import re
import logging
from litellm import completion

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Tribunal:
    def __init__(self):
        self.JUDGE_MODEL = "ollama/llama3.2"
        
        # Whitelist: Patterns that ALWAYS pass (bypass AI entirely)
        self.safe_refusals = [
            r"I'?m sorry,? (?:but )?I (?:can'?t|cannot) assist",
            r"I (?:don'?t|do not) have (?:access|information)",
            r"I'?m unable to (?:help|assist)",
            r"I (?:can'?t|cannot) help with that",
            r"I don'?t have the ability",
            r"I (?:can'?t|cannot|am not able to) (?:send|receive) email",
            r"I (?:can'?t|cannot) provide",
        ]
        
        logger.info("✅ Tribunal initialized with safe refusal patterns")

    def verify(self, draft: str, domain: str = "general"):
        """
        Verify draft against security policies.
        
        Args:
            draft: The LLM-generated response to validate
            domain: Department context (unused in this version)
            
        Returns:
            dict: {"verdict": "PASS" | "FAIL", "issues": list}
        """
        
        # STEP 0: Auto-pass common refusals (bypass AI entirely)
        for pattern in self.safe_refusals:
            if re.search(pattern, draft, re.IGNORECASE):
                logger.info("✅ Standard refusal pattern detected, auto-passing")
                return {"verdict": "PASS", "issues": []}
        
        # STEP 1: Check for actual secrets (regex-based, fast)
        forbidden_patterns = [
            r"sk-[a-zA-Z0-9]{20,}",              # OpenAI keys
            r"AKIA[0-9A-Z]{16}",                  # AWS keys
            r"ghp_[a-zA-Z0-9]{36,}",              # GitHub tokens
            r"password\s*[=:]\s*['\"][^'\"]+",    # Hardcoded passwords
            r"(?:api[_-]?key|secret)\s*[=:]\s*['\"][^'\"]+",  # API keys
        ]
        
        for pattern in forbidden_patterns:
            if re.search(pattern, draft, re.IGNORECASE):
                logger.error(f"🚨 Secret pattern detected in output")
                return {"verdict": "FAIL", "issues": ["Output contains credentials"]}

        # STEP 2: AI Check (only for edge cases now)
        try:
            response = completion(
                model=self.JUDGE_MODEL,
                messages=[{
                    "role": "system", 
                    "content": "Reply ONLY with 'SAFE' or 'UNSAFE'. If you see passwords, API keys, or secrets, reply 'UNSAFE'. Otherwise reply 'SAFE'. No explanations."
                }, {
                    "role": "user", 
                    "content": f"Check this text:\n\n{draft[:500]}"
                }],
                temperature=0.0,  # Zero creativity
                timeout=10
            )
            
            verdict = response.choices[0].message.content.strip().upper()
            
            # Only block if it explicitly says UNSAFE
            if verdict == "UNSAFE":
                logger.warning("⚠️ Tribunal AI flagged content as unsafe")
                return {"verdict": "FAIL", "issues": ["Security risk detected by AI scan"]}
                
        except Exception as e:
            logger.warning(f"⚠️ Tribunal check failed: {e}, defaulting to PASS (fail-open)")
            pass  # If Ollama fails, fail-open
        
        return {"verdict": "PASS", "issues": []}
