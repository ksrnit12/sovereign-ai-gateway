import re
from presidio_analyzer import AnalyzerEngine
from typing import Dict

class ComplianceAirlock:
    def __init__(self):
        print("🔒 Initializing Compliance Airlock...")
        self.analyzer = AnalyzerEngine()
        self.secret_patterns = {
            "AWS_KEY": r"(?<![A-Z0-9])AKIA[0-9A-Z]{16}(?![A-Z0-9])",
            "STRIPE_KEY": r"(?:sk|pk)_(?:test|live)_[0-9a-zA-Z]{24}",
            "CREDIT_CARD": r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\b",
            "EMAIL": r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
        }

    def sanitize(self, text: str) -> Dict:
        safe_text = text
        findings = []
        try:
            nlp = self.analyzer.analyze(text=text, entities=["PERSON", "LOCATION"], language='en')
            findings.extend([(r.start, r.end, r.entity_type) for r in nlp])
        except: pass

        for label, pattern in self.secret_patterns.items():
            findings.extend([(m.start(), m.end(), label) for m in re.finditer(pattern, text)])
        
        # Deduplicate
        findings = sorted(findings, key=lambda x: (x[0], -(x[1]-x[0])))
        unique = []
        if findings:
            curr = findings[0]
            for next_f in findings[1:]:
                if next_f[0] >= curr[1]:
                    unique.append(curr)
                    curr = next_f
            unique.append(curr)

        for start, end, label in sorted(unique, key=lambda x: x[0], reverse=True):
            safe_text = safe_text[:start] + f"<{label}_REDACTED>" + safe_text[end:]

        high_risk = {"AWS_KEY", "STRIPE_KEY"}
        return {
            "safe_text": safe_text,
            "was_scrubbed": len(unique) > 0,
            "risk_level": "HIGH" if any(x[2] in high_risk for x in unique) else "LOW"
        }
