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

### 1. Configure Environment Variables

Copy the example environment file and update as needed:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:
- `DATABASE_URL`: SQLite database path (default: `sqlite:///./data/lmsvr.db`)
- `OLLAMA_BASE_URL`: Ollama service URL (default: `http://ollama:11434`)
- `OPENAI_API_KEY`: Optional - for OpenAI pass-through endpoints
- `ANTHROPIC_API_KEY`: Optional - for Claude pass-through endpoints
- `LOG_LEVEL`: Logging level (default: `INFO`)

**Note:** The `.env` file is gitignored and won't be committed to the repository.

### 2. Start Services

```bash
docker-compose up -d
```

This will start:
- Ollama service on port 11434
- API Gateway on port 8000

### 3. Pull Models

```bash
docker exec -it ollama ollama pull llama3
docker exec -it ollama ollama pull mistral
```

Or use the CLI to list available models:
```bash
python cli/cli.py list-models
```

**Optional:** Sync models to database for metadata tracking:
```bash
python cli/cli.py sync-models
```

This will populate the `model_metadata` table with available models, enabling richer API responses with descriptions and context windows.

### 4. Create a Customer

```bash
python cli/cli.py create-customer "John Doe" "john@example.com" --budget 100.0
```

### 5. Generate API Key

```bash
python cli/cli.py generate-key 1
```

**Important:** Save the API key securely - it won't be shown again!

### 6. Set Pricing

```bash
python cli/cli.py set-pricing llama3 0.001 0.002
```

This sets:
- $0.001 per request
- $0.002 per model usage

You can set pricing for each model individually. Models without pricing configured will use a default rate of $0.01 per request.

### 7. Configure Cloudflare Tunnel

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
python cli/cli.py list-models          # List available Ollama models
python cli/cli.py sync-models          # Sync models to database for metadata
```

## Configuration

### Environment Variables

The application uses environment variables for configuration. Create a `.env` file from the example:

```bash
cp .env.example .env
```

**Required Settings:**
- `DATABASE_URL` - SQLite database path (default: `sqlite:///./data/lmsvr.db`)
- `OLLAMA_BASE_URL` - Ollama service URL (default: `http://ollama:11434` for Docker)

**Optional Settings:**
- `OPENAI_API_KEY` - For OpenAI pass-through endpoints (`/v1/chat/completions`)
- `ANTHROPIC_API_KEY` - For Claude pass-through endpoints (`/v1/messages`)
- `LOG_LEVEL` - Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR` (default: `INFO`)

**Note:** The `.env` file is gitignored and will not be committed to version control. Each deployment should have its own `.env` file.

## Database

The SQLite database is stored in `data/lmsvr.db` and contains:
- Customers
- API Keys (hashed)
- Usage Logs
- Pricing Configuration

## Model Management

### Using Ollama Commands

Models are managed using Ollama's native commands:

```bash
# Pull a model
docker exec -it ollama ollama pull llama3

# List models
docker exec -it ollama ollama list

# Remove a model
docker exec -it ollama ollama rm llama3
```

### Using CLI Tools

```bash
# List available models
python cli/cli.py list-models

# Sync models to database (for metadata tracking)
python cli/cli.py sync-models
```

### Model Discovery

Customers can discover available models via:
- `/api/models` - Ollama-compatible format
- `/v1/models` - OpenAI-compatible format

These endpoints return:
- Model name and ID
- Pricing configuration status
- Model metadata (description, context window) if synced via `sync-models`

### Model Metadata

The `sync-models` command populates the `model_metadata` table with information about available models. This enables:
- Richer API responses with model descriptions
- Context window information
- Better model discovery for customers

To update metadata after adding new models:
```bash
python cli/cli.py sync-models
```

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

Verify the `OLLAMA_BASE_URL` in your `.env` file matches your setup:
- Docker Compose: `http://ollama:11434`
- Local development: `http://localhost:11434`

### Database errors

Ensure the `data/` directory exists and is writable:
```bash
mkdir -p data
chmod 755 data
```

Check that `DATABASE_URL` in `.env` points to a valid path.

### Environment Variables Not Loading

If environment variables aren't being picked up:
1. Ensure `.env` file exists in the project root
2. Check that variable names match exactly (case-sensitive)
3. Restart Docker containers: `docker-compose restart api_gateway`

### Cloudflare Tunnel issues

See `cloudflare/README.md` for troubleshooting.

### CLI Connection Errors

If CLI commands can't connect to the database:
- Ensure the database file exists: `ls -la data/lmsvr.db`
- Check file permissions: `chmod 644 data/lmsvr.db`
- Verify `DATABASE_URL` in `.env` matches the CLI's expected path

## License

MIT

