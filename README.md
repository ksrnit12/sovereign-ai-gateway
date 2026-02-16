# 🛡️ Sovereign AI Gateway (v4.0)
### The "CrowdStrike" for GenAI Cost & Governance

**A local-first "Thick Client" that governs AI usage on the device—saving 40% on API costs without the latency of cloud routers.**

![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)
![Architecture](https://img.shields.io/badge/Architecture-Edge%20Compute-blueviolet)
![Status](https://img.shields.io/badge/Status-Production%20Ready-success.svg)

---

## 🌪️ The "AI Race" Problem
The AI market is fragmented. Today, **Claude Opus 4.6** is king. Tomorrow, it might be **GPT-5.3** or **Gemini 3 Deep Thinking**.
Companies are paralyzed:
1.  **The "Wealth Drain":** Employees use the "Best" model (e.g., Claude Opus @ $15/1M tokens) for *everything*—even simple "thank you" emails.
2.  **The "Cloud Router" Tax:** Tools like **Langflow** or **LangChain** add latency and require sending your data to *another* cloud server just to make a decision.
3.  **The Context Trap:** Switching models usually means losing context.

## 💡 The Solution: Edge Governance
Think of **Sovereign Gateway** not as a cloud platform, but as **"Antivirus for AI Costs."** It installs locally (like CrowdStrike) on your laptop fleet.

It acts as a **Smart Firewall** between your employees and the AI models.

| Feature | ☁️ Cloud Routers (Langflow) | 🛡️ Sovereign Gateway (Local) |
| :--- | :--- | :--- |
| **Location** | Remote Server (AWS/Azure) | **On-Device (Mac NPU / CPU)** |
| **Latency** | 800ms - 2000ms (Network Hop) | **< 20ms (Zero Latency)** |
| **Cost Control** | Reactive (End of month bill) | **Proactive (Blocks waste instantly)** |
| **Context** | Fragmented | **Unified (Carries history across models)** |
| **Privacy** | Decrypts data in cloud to route | **Routes via Vector (No PII leaves device)** |

---

## 🏗️ How It Works

### 1. The "Budget Guardrail" (Routing)
The Gateway analyzes every prompt locally using a Semantic Router.
* **Simple Task:** "Draft an email" → Routes to `gpt-4o-mini` ($0.15/1M tokens).
* **Complex Task:** "Debug this Python Race Condition" → Routes to `gpt-4o` ($5.00/1M tokens).
* **Result:** You get the "Best AI" when you need it, and the "Cheap AI" when you don't.

### 2. The "Privacy Shield" (Luhn-Validated)
* **Real-Time Redaction:** Uses the **Luhn Algorithm** to distinguish between fake numbers (e.g., `1234-1234...`) and real credit cards (`4242-4242...`).
* **Zero-Leak Policy:** Sensitive data is redacted to `<CREDIT_CARD_REDACTED>` *before* it leaves your laptop.

### 3. The "Tribunal" (Local Judge)
* **Tone Policing:** A local **Llama 3.2** model reviews every response to ensure it adheres to corporate policy (e.g., no toxic content, no competitor mentions).
* **Fail-Open Safety:** If the Judge crashes, the system defaults to "Allow" to ensure business continuity.

---

## 🚀 Quick Start

### Prerequisites
* **Preferred:** MacBook with Apple Silicon (M1-M4) for Hardware Acceleration.
* **Supported:** Windows/Linux (Runs on CPU).
* Python 3.10+
* OpenAI API Key

### Installation

1.  **Clone the Repository**
    ```bash
    git clone [https://github.com/ksrnit12/sovereign-ai-gateway.git](https://github.com/ksrnit12/sovereign-ai-gateway.git)
    cd sovereign-ai-gateway
    ```

2.  **Setup Environment**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

3.  **Configure Secrets**
    ```bash
    # Create .env file
    echo "OPENAI_API_KEY=sk-your-key-here" > .env
    ```

4.  **Run the Gateway**
    ```bash
    chmod +x run_app.sh
    ./run_app.sh
    ```

---

## 🛡️ Security & Privacy
* **Zero-Trust:** No data is sent to us. Routing happens on *your* hardware.
* **PII Redaction:** Luhn-Validated Regex v4.0 runs locally to strip Credit Cards/SSNs.
* **Audit Logs:** A local JSON audit trail tracks "Money Saved" for every query.

## 📜 License
MIT License - Open for Enterprise Modification.

---
*Built to democratize AI Governance.*
