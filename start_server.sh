#!/bin/bash
# Start the FastAPI server with WebSocket support

cd "$(dirname "$0")"
source env/bin/activate

echo "Starting server on port 8009..."
echo "WebSocket endpoint: ws://localhost:8009/voice"
echo "API docs: http://localhost:8009/docs"
echo ""
echo "Press Ctrl+C to stop"
echo ""

uvicorn app.main:app --host 0.0.0.0 --port 8009 --reload

