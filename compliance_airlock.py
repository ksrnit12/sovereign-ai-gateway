import re
import logging
from typing import Dict, List, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComplianceAirlock:
    def __init__(self):
        self.secret_patterns = {
            "AWS_KEY": r"(?<![A-Z0-9])AKIA[0-9A-Z]{16}(?![A-Z0-9])",
            "OPENAI_KEY": r"sk-[a-zA-Z0-9]{20,}",
            "STRIPE_KEY": r"(?:sk|pk)_(?:test|live)_[0-9a-zA-Z]{24,}",
            "GITHUB_TOKEN": r"ghp_[a-zA-Z0-9]{36,255}",
        }
        
        self.pii_patterns = {
            # Catch any 13-16 digit sequence for initial screening
            "CREDIT_CARD": r"\b(?:\d[ -]*?){13,16}\b",
            "US_SSN": r"\b(?!000|666|9\d{2})\d{3}[- ]?\d{2}[- ]?\d{4}\b",
            "EMAIL": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "PHONE": r"\b(?:\+1[-.\s]?)?(?:\([0-9]{3}\)|[0-9]{3})[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b"
        }
        
        logger.info("🛡️ Compliance Airlock initialized: Luhn + Regex Mode")

    def luhn_check(self, card_number: str) -> bool:
        """Mathematically validates a credit card number."""
        # Remove non-digits
        digits = [int(d) for d in re.sub(r'\D', '', card_number)]
        if not digits: return False
        
        # Luhn Algorithm
        checksum = 0
        reverse_digits = digits[::-1]
        for i, digit in enumerate(reverse_digits):
            if i % 2 == 1:
                digit *= 2
                if digit > 9: digit -= 9
            checksum += digit
        return checksum % 10 == 0

    def sanitize(self, text: str) -> Dict:
        findings = []
        
        # A. Scan for Secrets (HIGH risk)
        for label, pattern in self.secret_patterns.items():
            for match in re.finditer(pattern, text):
                findings.append((match.start(), match.end(), label, "HIGH"))
        
        # B. Scan for PII (MEDIUM risk)
        for label, pattern in self.pii_patterns.items():
            for match in re.finditer(pattern, text):
                # Extra validation for Credit Cards
                if label == "CREDIT_CARD":
                    if self.luhn_check(match.group()):
                        findings.append((match.start(), match.end(), label, "MEDIUM"))
                else:
                    findings.append((match.start(), match.end(), label, "MEDIUM"))
        
        # C. Deduplicate and Redact
        findings = sorted(findings, key=lambda x: (x[0], -(x[1]-x[0])))
        unique_findings = []
        if findings:
            curr = findings[0]
            for next_f in findings[1:]:
                if next_f[0] >= curr[1]:
                    unique_findings.append(curr)
                    curr = next_f
            unique_findings.append(curr)
        
        safe_text = text
        entities_found = set()
        risk_level = "LOW"
        
        for start, end, label, severity in sorted(unique_findings, key=lambda x: x[0], reverse=True):
            safe_text = safe_text[:start] + f"<{label}_REDACTED>" + safe_text[end:]
            entities_found.add(label)
            if severity == "HIGH": risk_level = "HIGH"
            elif severity == "MEDIUM" and risk_level != "HIGH": risk_level = "MEDIUM"
        
        return {
            "safe_text": safe_text,
            "was_scrubbed": len(unique_findings) > 0,
            "entities_found": list(entities_found),
            "risk_level": risk_level,
            "method": "Luhn-Validated Regex v4.0"
        }