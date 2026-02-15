#!/bin/bash
echo "🛡️  Starting Sovereign AI Gateway..."

export OLLAMA_HOST=127.0.0.1:11434
if ! pgrep -x "ollama" > /dev/null; then
    echo "🧠 Starting Ollama..."
    ollama serve > /dev/null 2>&1 &
    sleep 3
else
    echo "✅ Ollama is already running."
fi

echo "📦 Installing Dependencies..."
pip install -r requirements.txt > /dev/null 2>&1

if [ -z "$GATEWAY_API_KEY" ]; then
    export GATEWAY_API_KEY=$(openssl rand -hex 32)
    echo "🔑 Generated API Key: $GATEWAY_API_KEY"
fi

echo "🍳 Starting API Server..."
uvicorn api_server:app --port 8000 > /dev/null 2>&1 &
PID_API=$!
sleep 2

echo "🍽️  Starting UI..."
streamlit run ui_frontend.py &
PID_UI=$!

echo "🚀 System Online at http://localhost:8501"
echo "Press CTRL+C to stop."

trap "kill $PID_API $PID_UI; exit" INT
wait
