import streamlit as st
import requests
import time

st.set_page_config(page_title="Sovereign AI Gateway", layout="wide", page_icon="🛡️")

# Initialize Session State
if "total_savings" not in st.session_state: 
    st.session_state.total_savings = 0.0
if "pii_blocks" not in st.session_state: 
    st.session_state.pii_blocks = 0
if "policy_violations" not in st.session_state: 
    st.session_state.policy_violations = 0
if "messages" not in st.session_state: 
    st.session_state.messages = []

st.title("🛡️ Sovereign AI Gateway (M4 Edition)")

# --- METRICS DASHBOARD ---
col1, col2, col3 = st.columns(3)
col1.metric("💰 Total Savings", f"${st.session_state.total_savings:.3f}", "Smart Routing")
col2.metric("🔒 PII Blocks", st.session_state.pii_blocks, "Privacy Shield")
col3.metric("🚫 Policy Blocks", st.session_state.policy_violations, "Tribunal")
st.divider()

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configuration")
    dept = st.selectbox(
        "Department Context", 
        ["marketing", "engineering", "legal"],
        help="Select your department for context-specific routing"
    )
    
    st.divider()
    
    if st.button("🔄 Reset Session", use_container_width=True):
        st.session_state.total_savings = 0.0
        st.session_state.pii_blocks = 0
        st.session_state.policy_violations = 0
        st.session_state.messages = []
        st.rerun()
    
    st.divider()
    
    # System Status
    st.subheader("🔧 System Status")
    try:
        health = requests.get("http://localhost:8000/health", timeout=2).json()
        st.success(f"✅ API Server: {health.get('status', 'unknown').title()}")
    except:
        st.error("❌ API Server: Offline")
    
    st.divider()
    
    # Info
    with st.expander("ℹ️ About"):
        st.markdown("""
        **Sovereign AI Gateway** provides:
        - 🔒 PII/Secret Detection
        - 🧠 Semantic Routing (M4 NPU)
        - 📋 Policy Enforcement
        - 💰 Cost Optimization
        - 📊 Audit Logging
        
        Routes general queries to GPT-4o-mini for cost savings.
        Technical queries use GPT-4o for better code quality.
        """)

# --- CHAT INTERFACE ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        
        # Show audit trail for assistant messages
        if msg["role"] == "assistant" and "metadata" in msg:
            data = msg["metadata"]
            with st.expander("🔍 View Audit Trail"):
                # Metrics display
                c1, c2 = st.columns(2)
                c1.metric("Model Used", data.get("model_used", "N/A"))
                c1.metric("Verdict", data.get("verdict", "N/A"))
                c2.metric("Savings", f"${data.get('savings', 0):.4f}")
                pii_status = "Yes ✅" if data.get("pii_scrubbed") else "No"
                c2.metric("PII Scrubbed", pii_status)
                
                # Show redacted content if PII was scrubbed
                if data.get("pii_scrubbed"):
                    st.warning("🔒 Sensitive data was redacted before sending to API")
                    st.code(data.get("safe_prompt", "N/A"), language=None)
                    if data.get("entities_found"):
                        st.info(f"Detected: {', '.join(data.get('entities_found', []))}")
                
                # Full JSON
                st.json(data)

# --- INPUT HANDLER ---
if prompt := st.chat_input("Enter your prompt..."):
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Process request
    with st.spinner("🔄 Processing through Sovereign Gateway..."):
        try:
            # Submit request
            resp = requests.post(
                "http://localhost:8000/submit", 
                json={"messages": [{"content": prompt}], "department": dept},
                timeout=5
            )
            
            # Check for errors
            if resp.status_code != 200:
                st.error(f"❌ API Error: {resp.status_code}")
                st.code(resp.text)
                st.stop()
            
            job_id = resp.json()["request_id"]
            
            # Poll for completion (max 60 seconds)
            max_attempts = 120  # 60 seconds with 0.5s sleep
            for attempt in range(max_attempts):
                status_resp = requests.get(
                    f"http://localhost:8000/status/{job_id}",
                    timeout=5
                )
                
                if status_resp.status_code == 200:
                    data = status_resp.json()
                    
                    if data.get("status") in ["COMPLETED", "ERROR"]:
                        break
                
                time.sleep(0.5)
            else:
                # Timeout after 60 seconds
                st.error("⏱️ Request timeout - please try again")
                st.session_state.messages.pop()  # Remove failed user message
                st.stop()
            
            # Handle completed request
            if data.get("status") == "COMPLETED":
                # Update session metrics
                if data.get("pii_scrubbed"):
                    st.session_state.pii_blocks += 1
                if data.get("verdict") == "FAIL":
                    st.session_state.policy_violations += 1
                st.session_state.total_savings += data.get("savings", 0.0)
                
                # Prepare metadata
                metadata = {
                    "model_used": data.get("model_used", "N/A"),
                    "safe_prompt": data.get("safe_prompt", "N/A"),
                    "pii_scrubbed": data.get("pii_scrubbed", False),
                    "entities_found": data.get("entities_found", []),
                    "verdict": data.get("verdict", "N/A"),
                    "savings": data.get("savings", 0.0),
                    "sanitization_method": data.get("sanitization_method", "Unknown")
                }
                
                # Display response
                output_text = data.get("output", "No output received.")
                
                with st.chat_message("assistant"):
                    st.markdown(output_text)
                    
                    with st.expander("🔍 View Audit Trail"):
                        c1, c2 = st.columns(2)
                        c1.metric("Model Used", metadata["model_used"])
                        c1.metric("Verdict", metadata["verdict"])
                        c2.metric("Savings", f"${metadata['savings']:.4f}")
                        pii_status = "Yes ✅" if metadata["pii_scrubbed"] else "No"
                        c2.metric("PII Scrubbed", pii_status)
                        
                        if metadata["pii_scrubbed"]:
                            st.warning("🔒 Sensitive data was redacted")
                            st.code(metadata["safe_prompt"], language=None)
                            if metadata["entities_found"]:
                                st.info(f"Detected: {', '.join(metadata['entities_found'])}")
                        
                        st.json(metadata)
                
                # Save to session
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": output_text, 
                    "metadata": metadata
                })
                
                st.rerun()
            
            elif data.get("status") == "ERROR":
                st.error(f"❌ Processing Error: {data.get('output', 'Unknown error')}")
                st.session_state.messages.pop()  # Remove failed user message
                
        except requests.exceptions.ConnectionError:
            st.error("❌ Connection Error: Cannot reach API server")
            st.info("💡 Make sure the API server is running: `python api_server.py`")
            st.session_state.messages.pop()
        except requests.exceptions.Timeout:
            st.error("⏱️ Request timeout - server took too long to respond")
            st.session_state.messages.pop()
        except Exception as e:
            st.error(f"❌ Unexpected Error: {str(e)}")
            st.session_state.messages.pop()

# Footer
st.sidebar.markdown("---")
st.sidebar.caption("Sovereign AI Gateway v3.0 | Production Ready")
