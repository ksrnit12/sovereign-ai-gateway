import streamlit as st
import requests
import time
import os

st.set_page_config(page_title="Sovereign AI Gateway", layout="wide")

API_KEY = os.getenv("GATEWAY_API_KEY", "default-dev-key")
HEADERS = {"x-api-key": API_KEY}

# --- SIDEBAR CONFIGURATION ---
st.sidebar.title("Configuration")
dept = st.sidebar.selectbox("Department", ["General", "Engineering", "Marketing"])

if st.sidebar.button("🗑️ Clear Chat History"):
    st.session_state.messages = []
    st.rerun()

# --- METRICS DASHBOARD ---
dashboard_placeholder = st.empty()

def render_metrics():
    try:
        response = requests.get("http://localhost:8000/metrics", headers=HEADERS, timeout=1)
        if response.status_code == 200:
            data = response.json()
        else:
            data = {"total_savings": 0.0, "total_queries": 0}
    except:
        data = {"total_savings": 0.0, "total_queries": 0}
    
    with dashboard_placeholder.container():
        col1, col2 = st.columns(2)
        col1.metric("💰 Total Savings", f"${data.get('total_savings', 0.0):.3f}")
        col2.metric("📊 Queries Processed", data.get('total_queries', 0))

render_metrics()

# --- CHAT INTERFACE ---
st.title("🛡️ Sovereign AI Gateway")

if "messages" not in st.session_state: 
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Enter prompt..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    payload = {
        "messages": [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
        "department": dept.lower()
    }

    try:
        req = requests.post("http://localhost:8000/submit", json=payload, headers=HEADERS)
        
        if req.status_code == 200:
            job_id = req.json()["request_id"]
            
            with st.spinner("Processing on M4..."):
                # FIX: Increase polling to 100 attempts x 0.5s = 50 seconds wait time
                for _ in range(100):
                    try:
                        data = requests.get(f"http://localhost:8000/status/{job_id}", headers=HEADERS).json()
                        if data.get("status") == "COMPLETED":
                            break
                    except:
                        pass
                    time.sleep(0.5)
            
            if data.get("status") != "COMPLETED":
                st.error("⏱️ The AI is taking too long (Timeout). Try a simpler request.")
            else:
                with st.chat_message("assistant"):
                    st.markdown(data.get("output", ""))
                    with st.expander("🔍 Audit Trail"):
                        st.json(data)
                
                st.session_state.messages.append({"role": "assistant", "content": data.get("output", "")})
                render_metrics()
            
        else:
            st.error(f"API Error: {req.status_code}")
            
    except Exception as e:
        st.error(f"Connection Error: {e}")
