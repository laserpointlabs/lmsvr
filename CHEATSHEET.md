# CLI Cheatsheet

Quick reference guide for common operations using the Ollama API Gateway CLI.

**Note:** Always activate the virtual environment first:
```bash
source venv/bin/activate
```

---

## Customer Management

### Create a Customer
```bash
python cli/cli.py create-customer "John DeHart" laserpointlabs@gmail.com --budget 500.00
```

### List All Customers
```bash
python cli/cli.py list-customers
```

### Update Customer Information
```bash
# Update name
python cli/cli.py update-customer 1 --name "John DeHart"

# Update email
python cli/cli.py update-customer 1 --email laserpointlabs@gmail.com

# Update budget
python cli/cli.py update-customer 1 --budget 1000.00

# Update active status
python cli/cli.py update-customer 1 --active true

# Update multiple fields at once
python cli/cli.py update-customer 1 --name "John DeHart" --budget 750.00 --active true
```

### Delete a Customer
```bash
# With confirmation prompt
python cli/cli.py delete-customer 1

# Force delete (skip confirmation)
python cli/cli.py delete-customer 1 --force
```

---

## API Key Management

### Generate API Key for Customer
```bash
# First, find customer ID from list-customers, then:
python cli/cli.py generate-key 1
```

**Important:** Save the API key securely - it won't be shown again!

### Securely Send API Key to User

**⚠️ NEVER send API keys via:**
- Plain email (unencrypted)
- SMS/text messages
- Slack/Teams without encryption
- Public channels or forums
- Screenshots in unencrypted messages

**✅ Secure Delivery Methods:**

1. **Encrypted Email (Recommended)**
   ```bash
   # Use PGP/GPG encryption
   echo "Your API key: sk_..." | gpg --encrypt --recipient user@example.com | mail -s "Your API Key" user@example.com
   
   # Or use ProtonMail, Tutanota, or other encrypted email services
   ```

2. **Password Manager Sharing**
   - Use 1Password, Bitwarden, or LastPass secure sharing
   - Create a secure note with the API key
   - Share via secure link with expiration

3. **Temporary Secure Link**
   ```bash
   # Use a service like Onetimesecret.com or Privnote.com
   # Paste the API key, get a one-time link
   # Share the link via separate channel (email/SMS)
   ```

4. **Encrypted Messaging**
   - Signal, WhatsApp (end-to-end encrypted)
   - Send key via encrypted message
   - Delete message after confirmation

5. **Secure Portal/Dashboard** (Best for Production)
   - Build a customer portal where users can view their keys
   - Require 2FA/MFA for access
   - Log all key access
   - **See [docs/CUSTOMER_PORTAL.md](../docs/CUSTOMER_PORTAL.md) for complete design and implementation guide**

6. **In-Person or Phone**
   - For high-security scenarios
   - Read key over secure phone line
   - Have user confirm receipt before hanging up

**Recommended Workflow:**
```bash
# 1. Generate the key
python cli/cli.py generate-key 1

# 2. Copy the key to clipboard (Linux)
python cli/cli.py generate-key 1 | grep "API Key:" | awk '{print $3}' | xclip -selection clipboard

# 3. Send via encrypted method (choose one):
#    - Encrypted email
#    - Password manager share
#    - Secure messaging app
#    - Temporary secure link

# 4. Follow up to confirm receipt
# 5. Instruct user to store securely (password manager)
```

### List API Keys for Customer
```bash
python cli/cli.py list-keys 1
```

### Refresh API Key (Revoke Old, Create New)
```bash
# First, find key ID from list-keys, then:
python cli/cli.py refresh-key 5
```

### Revoke API Key
```bash
python cli/cli.py revoke-key 5
```

---

## Usage & Billing

### View Usage Report
```bash
# Current month usage
python cli/cli.py usage-report 1

# Specific date range
python cli/cli.py usage-report 1 --start-date 2024-12-01 --end-date 2024-12-31
```

### Check Budget Status
```bash
python cli/cli.py check-budget 1
```

### Export Usage Data
```bash
# Export as CSV (default)
python cli/cli.py export-usage 1

# Export as JSON
python cli/cli.py export-usage 1 --format json

# Export with date range
python cli/cli.py export-usage 1 --format csv --start-date 2024-12-01 --end-date 2024-12-31
```

---

## Pricing Configuration

### Set Pricing for a Model
```bash
# Set $0.001 per request, $0.002 per model usage
python cli/cli.py set-pricing llama3.2:1b 0.001 0.002

# Example for other models
python cli/cli.py set-pricing mistral 0.002 0.003
python cli/cli.py set-pricing codellama 0.0015 0.0025
```

---

## Model Management

### List Available Models
```bash
python cli/cli.py list-models
```

### Sync Models to Database
```bash
# Syncs available Ollama models to database for metadata tracking
python cli/cli.py sync-models
```

### Pull Models Manually (via Docker)
```bash
# Pull a model
docker exec -it ollama ollama pull llama3.2:1b

# List models in container
docker exec -it ollama ollama list

# Remove a model
docker exec -it ollama ollama rm llama3.2:1b
```

### Preload Models (Warmup to Avoid First-Request Latency)
```bash
# Automatic preloading via docker-compose (recommended)
# Set in .env file:
export OLLAMA_PRELOAD_MODELS="llama3.2:1b mistral"
docker compose up -d

# Manual preloading (Python script)
OLLAMA_PRELOAD_MODELS="llama3.2:1b" python3 scripts/preload_models.py

# Manual preloading (Bash script)
OLLAMA_PRELOAD_MODELS="llama3.2:1b" ./scripts/preload_models.sh

# Direct warmup via API
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.2:1b",
    "prompt": "Hi",
    "options": {"num_predict": 5}
  }'

# See docs/MODEL_PRELOADING.md for complete guide
```

---

## API Testing

### Test API with Generated Key
```bash
# Replace YOUR_API_KEY with the key from generate-key command
export API_KEY="sk_your_api_key_here"

# List models
curl -H "Authorization: Bearer $API_KEY" \
  http://localhost:8001/api/models

# Health check
curl http://localhost:8001/health

# Ollama connectivity check
curl http://localhost:8001/health/ollama
```

### Test Chat Completion
```bash
curl -X POST http://localhost:8001/api/chat \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.2:1b",
    "messages": [
      {"role": "user", "content": "Hello, how are you?"}
    ]
  }'
```

### Complete API Testing Examples for John DeHart

**Setup:**
```bash
# Set your API key (replace with actual key from generate-key command)
export API_KEY="sk_your_actual_api_key_here"
export BASE_URL="http://localhost:8001"
```

**1. Health Checks**
```bash
# API Gateway health
curl $BASE_URL/health

# Ollama connectivity
curl $BASE_URL/health/ollama
```

**2. List Available Models**
```bash
# Ollama format
curl -H "Authorization: Bearer $API_KEY" \
  $BASE_URL/api/models

# OpenAI-compatible format
curl -H "Authorization: Bearer $API_KEY" \
  $BASE_URL/v1/models
```

**3. Chat Completion (llama3.2:1b)**
```bash
# Simple chat
curl -X POST $BASE_URL/api/chat \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.2:1b",
    "messages": [
      {"role": "user", "content": "What is artificial intelligence?"}
    ]
  }'

# Multi-turn conversation
curl -X POST $BASE_URL/api/chat \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.2:1b",
    "messages": [
      {"role": "user", "content": "Hello, my name is John."},
      {"role": "assistant", "content": "Hello John! Nice to meet you."},
      {"role": "user", "content": "Can you help me understand how to use this API?"}
    ]
  }'

# With streaming (Server-Sent Events)
curl -X POST $BASE_URL/api/chat \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.2:1b",
    "messages": [
      {"role": "user", "content": "Write a short poem about coding."}
    ],
    "stream": true
  }'
```

**4. Text Generation (llama3.2:1b)**
```bash
# Simple generation
curl -X POST $BASE_URL/api/generate \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.2:1b",
    "prompt": "Explain quantum computing in simple terms:"
  }'

# With custom options
curl -X POST $BASE_URL/api/generate \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.2:1b",
    "prompt": "Write a brief summary of machine learning:",
    "options": {
      "temperature": 0.7,
      "top_p": 0.9,
      "num_predict": 200
    }
  }'

# Streaming generation
curl -X POST $BASE_URL/api/generate \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.2:1b",
    "prompt": "List 5 benefits of using API gateways:",
    "stream": true
  }'
```

**5. OpenAI-Compatible Endpoint**
```bash
# Chat completions (OpenAI format)
curl -X POST $BASE_URL/v1/chat/completions \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.2:1b",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "What are the main features of this API gateway?"}
    ],
    "temperature": 0.7,
    "max_tokens": 500
  }'
```

**6. Pretty Print JSON Responses**
```bash
# Install jq for better output: sudo apt-get install jq

# List models (pretty)
curl -s -H "Authorization: Bearer $API_KEY" \
  $BASE_URL/api/models | jq

# Chat with formatted output
curl -s -X POST $BASE_URL/api/chat \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.2:1b",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ]
  }' | jq
```

**7. Save Response to File**
```bash
# Save chat response
curl -X POST $BASE_URL/api/chat \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.2:1b",
    "messages": [
      {"role": "user", "content": "Explain REST APIs"}
    ]
  }' > response.json

# View saved response
cat response.json | jq
```

**8. Error Testing**
```bash
# Test without API key (should fail)
curl $BASE_URL/api/models

# Test with invalid API key
curl -H "Authorization: Bearer sk_invalid_key" \
  $BASE_URL/api/models

# Test with invalid model
curl -X POST $BASE_URL/api/chat \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "nonexistent-model",
    "messages": [
      {"role": "user", "content": "Hello"}
    ]
  }'
```

**Quick Test Script**
```bash
#!/bin/bash
# Save this script as: chmod +x test_api.sh && ./test_api.sh

API_KEY="sk_your_actual_api_key_here"
BASE_URL="http://localhost:8001"

echo "Testing API Gateway for John DeHart..."
echo ""

echo "1. Health Check:"
curl -s $BASE_URL/health | jq
echo ""

echo "2. List Models:"
curl -s -H "Authorization: Bearer $API_KEY" \
  $BASE_URL/api/models | jq '.models[] | select(.name == "llama3.2:1b")'
echo ""

echo "3. Chat Completion:"
curl -s -X POST $BASE_URL/api/chat \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.2:1b",
    "messages": [
      {"role": "user", "content": "Say hello in one sentence."}
    ]
  }' | jq '.message.content'
echo ""

echo "Test complete!"
```

---

## Common Workflows

### Complete Setup for John DeHart
```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Create customer
python cli/cli.py create-customer "John DeHart" laserpointlabs@gmail.com --budget 500.00

# 3. Generate API key (note the customer ID from step 2)
python cli/cli.py generate-key 1

# 4. Set pricing for models
python cli/cli.py set-pricing llama3.2:1b 0.001 0.002

# 5. Verify setup
python cli/cli.py list-customers
python cli/cli.py list-keys 1
python cli/cli.py list-models
```

### Monthly Usage Review
```bash
# Get usage report for current month
python cli/cli.py usage-report 1

# Check if budget is exceeded
python cli/cli.py check-budget 1

# Export detailed usage
python cli/cli.py export-usage 1 --format csv
```

### Rotate API Key
```bash
# List current keys
python cli/cli.py list-keys 1

# Refresh key (creates new, revokes old)
python cli/cli.py refresh-key 5
```

---

## Help & Troubleshooting

### Get Help
```bash
# General help
python cli/cli.py --help

# Command-specific help
python cli/cli.py create-customer --help
python cli/cli.py update-customer --help
```

### Check Service Status
```bash
# Docker services
docker compose ps

# Ollama container
docker compose ps ollama

# API Gateway logs
docker compose logs api_gateway --tail 50

# Ollama logs
docker compose logs ollama --tail 50
```

---

## Quick Reference

| Command | Description |
|---------|-------------|
| `list-customers` | List all customers |
| `create-customer "Name" email@example.com --budget 100` | Create customer |
| `update-customer ID --name "Name" --budget 200` | Update customer |
| `delete-customer ID` | Delete customer |
| `generate-key ID` | Generate API key |
| `list-keys ID` | List customer's API keys |
| `refresh-key KEY_ID` | Rotate API key |
| `revoke-key KEY_ID` | Revoke API key |
| `usage-report ID` | View usage report |
| `check-budget ID` | Check budget status |
| `export-usage ID --format csv` | Export usage data |
| `set-pricing MODEL PER_REQUEST PER_MODEL` | Set pricing |
| `list-models` | List available models |
| `sync-models` | Sync models to database |

---

## Example Customer: John DeHart

**Email:** laserpointlabs@gmail.com  
**Customer ID:** (check with `list-customers`)  
**Default Budget:** $500.00

**Common Commands:**
```bash
# Create
python cli/cli.py create-customer "John DeHart" laserpointlabs@gmail.com --budget 500.00

# Generate key (replace 1 with actual customer ID)
python cli/cli.py generate-key 1

# Check usage
python cli/cli.py usage-report 1

# Update budget
python cli/cli.py update-customer 1 --budget 1000.00
```


