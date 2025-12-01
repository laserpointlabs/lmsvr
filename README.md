# Ollama API Gateway with Billing

A production-ready API gateway for Ollama that provides API key authentication, usage tracking, and billing capabilities. Supports both native Ollama endpoints and OpenAI/Claude-compatible pass-through.

**Recent Updates:**
- ✅ GPU support for accelerated inference
- ✅ Cloudflare Tunnel container integration
- ✅ Comprehensive CI/CD testing with Ollama's official setup
- ✅ GPU testing and verification tools
- ✅ Improved Docker Compose configuration

## Features

- 🔐 API key authentication
- 💰 Per-request and per-model pricing
- 📊 Usage tracking and billing
- 🎯 Budget limits per customer
- 🌐 Cloudflare Tunnel integration (Docker container)
- 🚀 GPU support for Ollama (NVIDIA)
- 🔄 OpenAI and Claude API pass-through
- 📈 Usage reports and exports
- 🏥 Health check endpoints
- 🧪 Comprehensive CI/CD testing
- 🔧 GPU testing and verification tools

## Quick Start

**New Installation?** Use the automated setup script:
```bash
./setup.sh
```

This comprehensive script handles:
- ✅ Prerequisites checking (Docker, Python, etc.)
- ✅ Environment setup and configuration
- ✅ Python virtual environment and dependencies
- ✅ Docker image building
- ✅ Service startup and health checks
- ✅ Database initialization
- ✅ Optional Cloudflare Tunnel setup
- ✅ Automated testing

**Time:** ~5-10 minutes depending on system performance.

See [QUICKSTART.md](QUICKSTART.md) for detailed quick start guide and manual setup instructions.

### Prerequisites

- Docker and Docker Compose
- Cloudflare account (for tunnel)
- Python 3.11+ (for CLI tool)
- **For GPU support (optional):** NVIDIA drivers and NVIDIA Container Toolkit

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

### 2. Configure GPU (Optional)

If you have an NVIDIA GPU and want to use it with Ollama:

**GPU Setup:**
```bash
# Install NVIDIA Container Toolkit
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# Configure Docker
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# Verify GPU access
./scripts/test_gpu.sh
# or
python3 scripts/test_gpu.py
```

**Note:** If GPU is not configured, Ollama will use CPU (slower but functional). The system works fine without GPU.

### 3. Start Services

**Start core services:**
```bash
docker compose up -d
```

This will start:
- Ollama service on port 11434 (with GPU if configured)
- API Gateway on port 8001 (mapped from container port 8000)

**Start with Cloudflare Tunnel:**
```bash
docker compose --profile tunnel up -d
```

This adds:
- Cloudflare Tunnel container (requires setup first - see step 8)

### 4. Pull Models

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

### 5. Create a Customer

```bash
python cli/cli.py create-customer "John Doe" "john@example.com" --budget 100.0
```

### 6. Generate API Key

```bash
python cli/cli.py generate-key 1
```

**Important:** Save the API key securely - it won't be shown again!

### 7. Set Pricing

```bash
python cli/cli.py set-pricing llama3 0.001 0.002
```

This sets:
- $0.001 per request
- $0.002 per model usage

You can set pricing for each model individually. Models without pricing configured will use a default rate of $0.01 per request.

### 8. Configure Cloudflare Tunnel (Optional)

**Automated CLI setup (recommended - works on any computer):**
```bash
cd cloudflare
./setup_tunnel_cli.sh
```

This script will:
- Check/install cloudflared if needed
- Authenticate with Cloudflare (opens browser)
- Create or use existing tunnel named "ollama-gateway"
- Set up DNS routing automatically
- Copy credentials to `cloudflare/credentials.json` with correct permissions
- Generate Docker-compatible configuration file
- Validate the configuration

**After running the script, start services:**
```bash
docker compose up -d
```

The Cloudflare tunnel container will start automatically and connect.

**Check tunnel status:**
```bash
docker compose ps cloudflared
docker compose logs cloudflared
```

**Verify tunnel is working:**
```bash
# Check tunnel connections (should show registered connections)
docker compose logs cloudflared | grep "Registered tunnel connection"

# Test endpoint (after DNS propagation, usually 2-5 minutes)
curl https://api.yourdomain.com/health
```

**Important:** 
- The tunnel container connects to your API Gateway via Docker network (`api_gateway:8000`)
- Ensure the API Gateway is running first
- Wait a few minutes for DNS propagation after setup
- Credentials file must have 644 permissions (script handles this automatically)

**Alternative setup methods:**
```bash
# Interactive Bash script
cd cloudflare
./setup_tunnel.sh

# Python script
cd cloudflare
python3 setup_tunnel.py
```

See `cloudflare/README.md` and `cloudflare/SETUP_CLI.md` for detailed instructions and troubleshooting.

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
docker compose ps
docker compose logs ollama
```

Verify the `OLLAMA_BASE_URL` in your `.env` file matches your setup:
- Docker Compose: `http://ollama:11434` (uses Docker network service name)
- Local development: `http://localhost:11434`

### GPU not working

Test GPU access:
```bash
./scripts/test_gpu.sh
```

Common issues:
- NVIDIA Container Toolkit not installed: `sudo apt-get install -y nvidia-container-toolkit`
- Docker not restarted after toolkit installation: `sudo systemctl restart docker`
- GPU configuration in docker-compose.yml incorrect: Check `deploy.resources.reservations.devices` section

### Cloudflare Tunnel not connecting

Check tunnel container:
```bash
docker compose --profile tunnel logs cloudflared
```

Common issues:
- Credentials not found: Ensure `cloudflare/credentials/` contains your tunnel JSON file
- Config file incorrect: Verify `cloudflare/config.yml` has correct tunnel ID and service URL
- API Gateway not running: Tunnel depends on `api_gateway` service
- DNS not propagated: Wait a few minutes after DNS setup

### Database errors

Ensure the `data/` directory exists and is writable:
```bash
mkdir -p data
chmod 755 data
```

Check that `DATABASE_URL` in `.env` points to a valid path:
- Docker: `sqlite:///app/data/lmsvr.db` (path inside container)
- Local CLI: `sqlite:///./data/lmsvr.db` (relative to project root)

### Environment Variables Not Loading

If environment variables aren't being picked up:
1. Ensure `.env` file exists in the project root
2. Check that variable names match exactly (case-sensitive)
3. Restart Docker containers: `docker compose restart api_gateway`

**Note:** Docker Compose automatically loads `.env` file. For CLI tools, ensure you're using the correct `DATABASE_URL` path.

### Port conflicts

If port 8001 is already in use:
```bash
# Check what's using the port
sudo lsof -i :8001

# Change port in docker-compose.yml
# Update: ports: - "8002:8000" (or another available port)
```

### Container restart issues

Restart all services:
```bash
docker compose down
docker compose up -d
```

Check logs for errors:
```bash
docker compose logs api_gateway
docker compose logs ollama
```

### CLI Connection Errors

If CLI commands can't connect to the database:
- Ensure the database file exists: `ls -la data/lmsvr.db`
- Check file permissions: `chmod 644 data/lmsvr.db`
- Verify `DATABASE_URL` in `.env` matches the CLI's expected path

## Testing

### Running Tests Locally

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run specific test suite
pytest tests/test_database.py -v
pytest tests/test_api.py -v
pytest tests/test_cli.py -v
pytest tests/test_ollama_integration.py -v -m integration
```

### GPU Testing

**Basic GPU Access Test:**
```bash
# Bash version
./scripts/test_gpu.sh

# Python version
python3 scripts/test_gpu.py
```

This verifies GPU is accessible but doesn't confirm it's being used.

**GPU Utilization Test (Recommended):**
```bash
# Bash version
./scripts/test_gpu_utilization.sh

# Python version
python3 scripts/test_gpu_utilization.py
```

This actually runs inference and monitors GPU usage to verify GPU is being utilized:
- Runs a model inference
- Monitors GPU utilization in real-time
- Shows GPU memory usage
- Compares baseline vs. peak usage
- Provides clear pass/fail results

**What to look for:**
- ✅ GPU utilization should jump to 50-100% during inference
- ✅ GPU memory should increase (varies by model size)
- ✅ Inference should be faster than CPU-only
- ❌ If utilization stays near 0%, GPU is not being used

See `docs/GPU_TESTING.md` for detailed testing guide and troubleshooting.

### CI/CD

The project uses GitHub Actions for continuous integration. Tests run automatically on:
- Push to main/develop branches
- Pull requests

The CI workflow:
- Sets up Ollama using the official `ai-action/setup-ollama@v1` GitHub Action
- Caches Ollama models for faster test runs
- Runs database, CLI, API, and integration tests
- Verifies API Gateway connectivity with Ollama
- Tests with actual Ollama models when available

See `.github/workflows/ci.yml` for the complete CI configuration.

## Architecture

### Services

- **Ollama**: LLM inference server (with optional GPU acceleration)
- **API Gateway**: FastAPI service handling authentication, routing, and billing
- **Cloudflare Tunnel**: Secure tunnel container for internet exposure (optional)

### Network

All services run on the `lmsvr_network` Docker network:
- Ollama: `http://ollama:11434`
- API Gateway: `http://api_gateway:8000` (internal), `http://localhost:8001` (external)
- Cloudflare Tunnel: Connects to `api_gateway:8000` via Docker network

### Data Storage

- SQLite database: `data/lmsvr.db` (persisted via volume mount)
- Ollama models: `ollama_data` Docker volume
- Cloudflare credentials: `cloudflare/credentials/` (gitignored)

## Recent Changes

See [CHANGELOG.md](CHANGELOG.md) for detailed change history.

**Latest updates:**
- GPU support configuration
- Cloudflare Tunnel container integration
- CI/CD testing improvements
- GPU testing tools

## License

MIT

