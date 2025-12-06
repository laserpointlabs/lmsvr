#!/bin/bash

# Test streaming response like the frontend does
API_KEY="sk_p_9R0Dm4kfOLxD7zjLLX8A"

echo "Testing: What are the odds for the Saints game? (STREAMING)"
echo "-----------------------------------------------------------"

curl -N -X POST http://localhost:8001/api/chat \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.2:latest",
    "messages": [{"role": "user", "content": "What are the odds for the Saints game?"}],
    "stream": true
  }' 2>&1 | head -50

echo ""
echo "-----------------------------------------------------------"
echo "If you see tool_calls above, the frontend fix didn't work."
echo "If you see actual odds (Saints -124, Panthers +148), it worked!"
