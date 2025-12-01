# Ollama API Gateway with Billing

A production-ready API gateway for Ollama that provides API key authentication, usage tracking, and billing capabilities. Supports both native Ollama endpoints and OpenAI/Claude-compatible pass-through.

## Features

- 🔐 API key authentication
- 💰 Per-request and per-model pricing
- 📊 Usage tracking and billing
- 🎯 Budget limits per customer
- 🌐 Cloudflare Tunnel integration
- 🔄 OpenAI and Claude API pass-through
- 📈 Usage reports and exports
- 🏥 Health check endpoints

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Cloudflare account (for tunnel)
- Python 3.11+ (for CLI tool)

### 1. Start Services

```bash
docker-compose up -d
```

This will start:
- Ollama service on port 11434
- API Gateway on port 8000

### 2. Pull Models

```bash
docker exec -it ollama ollama pull llama3
docker exec -it ollama ollama pull mistral
```

Or use the CLI:
```bash
python cli/cli.py list-models
```

### 3. Create a Customer

```bash
python cli/cli.py create-customer "John Doe" "john@example.com" --budget 100.0
```

### 4. Generate API Key

```bash
python cli/cli.py generate-key 1
```

Save the API key securely - it won't be shown again!

### 5. Set Pricing

```bash
python cli/cli.py set-pricing llama3 0.001 0.002
```

This sets:
- $0.001 per request
- $0.002 per model usage

### 6. Configure Cloudflare Tunnel

**Quick setup (recommended):**
```bash
cd cloudflare
./setup_tunnel.sh
# or
python3 setup_tunnel.py
```

See `cloudflare/README.md` for detailed instructions.

## API Usage

### Authentication

All requests require an API key in the `Authorization` header:

```bash
curl -H "Authorization: Bearer sk_your_api_key_here" \
  http://localhost:8000/api/models
```

### Ollama Endpoints

- `POST /api/chat` - Chat completion
- `POST /api/generate` - Text generation
- `GET /api/models` - List available models

### OpenAI-Compatible Endpoints

- `POST /v1/chat/completions` - OpenAI-compatible chat
- `GET /v1/models` - OpenAI-compatible model list

### Claude-Compatible Endpoints

- `POST /v1/messages` - Claude-compatible messages

### Health Checks

- `GET /health` - API Gateway health
- `GET /health/ollama` - Ollama connectivity

## CLI Commands

```bash
# Customer Management
python cli/cli.py create-customer <name> <email> [--budget]
python cli/cli.py list-customers

# API Key Management
python cli/cli.py generate-key <customer_id>
python cli/cli.py revoke-key <key_id>
python cli/cli.py list-keys <customer_id>

# Usage & Billing
python cli/cli.py usage-report <customer_id> [--start-date] [--end-date]
python cli/cli.py check-budget <customer_id>
python cli/cli.py export-usage <customer_id> [--format csv|json] [--start-date] [--end-date]

# Pricing
python cli/cli.py set-pricing <model> <per_request> <per_model>

# Models
python cli/cli.py list-models
```

## Configuration

Copy `.env.example` to `.env` and update as needed:

```bash
cp .env.example .env
```

Key settings:
- `DATABASE_URL` - SQLite database path
- `OLLAMA_BASE_URL` - Ollama service URL
- `OPENAI_API_KEY` - For OpenAI pass-through (optional)
- `ANTHROPIC_API_KEY` - For Claude pass-through (optional)

## Database

The SQLite database is stored in `data/lmsvr.db` and contains:
- Customers
- API Keys (hashed)
- Usage Logs
- Pricing Configuration

## Model Management

Models are managed using Ollama's native commands:

```bash
# Pull a model
docker exec -it ollama ollama pull llama3

# List models
docker exec -it ollama ollama list

# Remove a model
docker exec -it ollama ollama rm llama3
```

Customers can discover available models via the `/api/models` or `/v1/models` endpoints.

## Pricing Model

Costs are calculated as:
- Base cost per request (configurable per model)
- Additional cost per model usage (configurable per model)

External API costs (OpenAI/Claude) are calculated based on token usage and current pricing.

## Security

- API keys are hashed using SHA-256
- HTTPS provided via Cloudflare Tunnel
- Request logging for audit trail
- Budget limits prevent over-spending

## Troubleshooting

### API Gateway can't connect to Ollama

Check that Ollama is running:
```bash
docker ps
docker logs ollama
```

### Database errors

Ensure the `data/` directory exists and is writable:
```bash
mkdir -p data
chmod 755 data
```

### Cloudflare Tunnel issues

See `cloudflare/README.md` for troubleshooting.

## License

MIT

