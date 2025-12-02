# Ollama API Gateway with Billing

A production-ready API gateway for Ollama that provides API key authentication, usage tracking, and billing capabilities. Supports both native Ollama endpoints and OpenAI/Claude-compatible pass-through.

**Recent Updates:**
- ✅ GPU support for accelerated inference
- ✅ Cloudflare Tunnel container integration
- ✅ Comprehensive CI/CD testing with Ollama's official setup
- ✅ GPU testing and verification tools
- ✅ Improved Docker Compose configuration
- ✅ Automatic model preloading on startup
- ✅ Permanent model loading (no timeout) with `OLLAMA_KEEP_ALIVE=-1`

## Features

- 🔐 API key authentication
- 💰 Per-request and per-model pricing
- 📊 Usage tracking and billing
- 🎯 Budget limits per customer
- 🌐 Cloudflare Tunnel integration (Docker container)
- 🚀 GPU support for Ollama (NVIDIA)
- 🔄 OpenAI and Claude API pass-through
- 📈 Usage reports and exports
- 🏥 Health check endpoints with timestamps and auto-updating dashboard
- 🧪 Comprehensive CI/CD testing
- 🔧 GPU testing and verification tools
- ⚡ Automatic model preloading of models into GPU memory
- 🔄 Auto-start services on system boot (systemd integration)

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
- `DATABASE_URL`: SQLite database path (default: `sqlite:///./data/lmapi.db`)
- `OLLAMA_BASE_URL`: Ollama service URL (default: `http://ollama:11434`)

**Important:** The database is initialized automatically during setup with proper user permissions. Docker containers run as your user (not root) to ensure all files are accessible.
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
- Cloudflare Tunnel container (if configured - see Cloudflare Setup section)

**Quick Health Check:**
```bash
# JSON health endpoint (includes timestamp)
curl http://localhost:8001/health

# Interactive dashboard with auto-updating time (open in browser)
# http://localhost:8001/health/dashboard
```

**Note:** If Cloudflare tunnel credentials (`cloudflare/credentials.json`) and config (`cloudflare/config.yml`) exist, the tunnel will start automatically with `docker compose up -d`.

### 4. Pull and Preload Models

**Option A: Manual Model Pulling**

```bash
docker exec -it ollama ollama pull llama3
docker exec -it ollama ollama pull mistral
```

**Option B: Automatic Model Preloading (Recommended)**

Configure models to automatically load on startup by setting `OLLAMA_PRELOAD_MODELS` in your `.env` file:

```bash
OLLAMA_PRELOAD_MODELS="qwen3-coder:30b,devstral,qwen2.5-coder:1.5b-base,nomic-embed-text"
```

Models will be:
- Automatically pulled if not already available
- Loaded into GPU memory on container startup
- Kept loaded permanently (due to `OLLAMA_KEEP_ALIVE=-1`)

See [Model Preloading](#model-preloading) section for details.

**List Available Models:**

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
curl https://lmapi.laserpointlabs.com/health

# View interactive health dashboard with auto-updating time
# Open in browser: https://lmapi.laserpointlabs.com/health/dashboard
```

**Note:** The default domain is `lmapi.laserpointlabs.com`. You can change this by:
1. Updating `cloudflare/config.yml` with your desired hostname
2. Setting `CLOUDFLARE_TUNNEL_URL` in your `.env` file
3. Setting up the DNS route via Cloudflare dashboard or CLI

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

- `POST /v1/chat/completions` - OpenAI-compatible chat (pass-through to external OpenAI)
- `POST /v1/ollama/chat/completions` - OpenAI-compatible chat using local Ollama models
- `GET /v1/models` - OpenAI-compatible model list

### Claude-Compatible Endpoints

- `POST /v1/messages` - Claude-compatible messages

### Health Checks

- `GET /health` - API Gateway health (includes current timestamp)
- `GET /health/ollama` - Ollama connectivity (includes current timestamp)
- `GET /health/dashboard` - Interactive health dashboard with auto-updating time (HTML)

## Continue.dev Integration

This API gateway is compatible with [Continue.dev](https://continue.dev/), the open-source AI code assistant for VS Code and JetBrains IDEs.

### Quick Setup (2 Steps)

**Step 1: Save your API key**

```bash
mkdir -p ~/.continue && echo "LMAPI_KEY=your_api_key_here" > ~/.continue/.env
```

Replace `your_api_key_here` with your actual API key.

**Step 2: Copy the config file**

Copy the provided `config.yaml` to your project:

```bash
mkdir -p your-project/.continue/agents
cp config.yaml your-project/.continue/agents/
```

**Step 3: Restart VS Code**

Reload the VS Code window to apply the configuration.

---

### Config File Reference

The config file (`.continue/agents/config.yaml`) should contain:

```yaml
name: LaserPoint Labs API Gateway
version: 1.0.0
schema: v1

models:
  # Qwen3 Coder 30B - Primary chat model
  - name: Qwen3 Coder 30B
    provider: openai
    model: qwen3-coder:30b
    apiBase: https://lmapi.laserpointlabs.com/v1/ollama
    apiKey: ${{ secrets.LMAPI_KEY }}
    roles:
      - chat
      - edit
      - apply
    defaultCompletionOptions:
      temperature: 0.7
      maxTokens: 4096
    requestOptions:
      timeout: 300

  # Devstral 27B - Alternative chat model
  - name: Devstral 27B
    provider: openai
    model: devstral
    apiBase: https://lmapi.laserpointlabs.com/v1/ollama
    apiKey: ${{ secrets.LMAPI_KEY }}
    roles:
      - chat
      - edit
      - apply
    defaultCompletionOptions:
      temperature: 0.7
      maxTokens: 4096
    requestOptions:
      timeout: 300

  # GPT-OSS 20B - Good balance for Chat and Edit
  - name: GPT-OSS 20B
    provider: openai
    model: gpt-oss:20b
    apiBase: https://lmapi.laserpointlabs.com/v1/ollama
    apiKey: ${{ secrets.LMAPI_KEY }}
    roles:
      - chat
      - edit
      - apply
    defaultCompletionOptions:
      temperature: 0.7
      maxTokens: 4096
    requestOptions:
      timeout: 300

context:
  - provider: file
  - provider: code
  - provider: diff
  - provider: terminal

rules:
  - Be concise and helpful in responses
  - Focus on code quality and best practices
  - When editing code, maintain existing patterns and style
```

### Available Models

| Model | Size | Best For |
|-------|------|----------|
| `qwen3-coder:30b` | 30B | Code generation, chat, editing |
| `devstral` | 27B | Code generation, chat, editing |
| `gpt-oss:20b` | 20B | General chat, code assistance |

### Troubleshooting

**401 Invalid API Key:**
- Ensure `~/.continue/.env` exists with `LMAPI_KEY=your_key`
- The syntax must be `${{ secrets.LMAPI_KEY }}` in the config
- Restart VS Code after creating/changing `.env`

**No Response (GPU fires but nothing appears):**
- Ensure config uses `provider: openai` (not `provider: ollama`)
- Ensure `apiBase` is `https://lmapi.laserpointlabs.com/v1/ollama`

**Config Not Loading:**
- Workspace config must be at `.continue/agents/config.yaml`
- Reload VS Code window after config changes

## CLI Commands

```bash
# Customer Management
python cli/cli.py create-customer <name> <email> [--budget]
python cli/cli.py update-customer <customer_id> [--name NAME] [--email EMAIL] [--budget BUDGET] [--active true|false]
python cli/cli.py delete-customer <customer_id> [--force]
python cli/cli.py list-customers

# API Key Management
python cli/cli.py generate-key <customer_id>
python cli/cli.py refresh-key <key_id>          # Revoke old key and generate new one
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

# Help
python cli/cli.py --help               # Show all available commands
python cli/cli.py <command> --help     # Show help for specific command
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
- `CLOUDFLARE_TUNNEL_URL` - Public URL for the API Gateway via Cloudflare Tunnel (default: `https://lmapi.laserpointlabs.com`)
- `OLLAMA_MAX_LOADED_MODELS` - Maximum number of models to keep loaded in memory concurrently (default: `6`). Increase this value if you want to keep more models loaded simultaneously. Default is 3 * number of GPUs (or 3 for CPU inference). With 4 GPUs (64GB VRAM), 6-8 models is recommended.
- `OLLAMA_KEEP_ALIVE` - Duration to keep models loaded in memory (default: `-1` = forever). Set to `-1` or `-1m` to keep models loaded indefinitely, preventing automatic unloading. Default behavior without this setting is 5 minutes of inactivity before unloading.
- `OLLAMA_PRELOAD_MODELS` - Comma-separated list of models to automatically load on Ollama startup (default: empty). Models will be pulled if not available and loaded permanently. Example: `"llama3.2:latest,qwen3-coder:30b,mistral:latest"`. Leave empty to skip automatic loading.
  
  **Note:** The `CLOUDFLARE_TUNNEL_URL` value is used to update `cloudflare/config.yml`. After changing it in `.env`, run:
  ```bash
  ./cloudflare/update_config_from_env.sh
  docker compose restart cloudflared
  ```

**Note:** The `.env` file is gitignored and will not be committed to version control. Each deployment should have its own `.env` file.

## Database

The SQLite database is stored in `data/lmsvr.db` and contains:
- Customers
- API Keys (hashed)
- Usage Logs
- Pricing Configuration

## Model Management

### Model Preloading

The system supports automatic model preloading on container startup. Models specified in `OLLAMA_PRELOAD_MODELS` will be automatically loaded into GPU memory and kept loaded permanently.

**Configuration:**

Add models to your `.env` file:

```bash
# Comma-separated list of models to preload
OLLAMA_PRELOAD_MODELS="qwen3-coder:30b,devstral,qwen2.5-coder:1.5b-base,nomic-embed-text"
```

**How It Works:**

1. On container startup, the `ollama-start.sh` script runs automatically
2. Script waits for Ollama service to be ready
3. For each model in `OLLAMA_PRELOAD_MODELS`:
   - Checks if model exists locally
   - Pulls model if not found
   - Loads model into GPU memory
   - Keeps model loaded permanently (via `OLLAMA_KEEP_ALIVE=-1`)

**Model Loading Behavior:**

- **Regular Models** (chat, code, etc.): Loaded via `ollama run` and appear in `ollama ps` with "Forever" status
- **Embedding Models**: 
  - Cannot be loaded via `ollama run` (they don't support the generate API)
  - Automatically loaded via `/api/embeddings` endpoint by the startup script
  - Once loaded, appear in `ollama ps` with "Forever" status
  - Stay loaded in GPU memory permanently (Note: Embedding models require the embeddings API endpoint, not the generate API. This is handled automatically by the startup script.

**Verify Loaded Models:**

```bash
# Check which models are currently loaded in GPU memory
docker exec ollama ollama ps

# Check GPU memory usage
docker exec ollama nvidia-smi
```

**Environment Variables:**

- `OLLAMA_PRELOAD_MODELS`: Comma-separated list of models to preload (e.g., `"model1,model2,model3"`)
- `OLLAMA_KEEP_ALIVE`: Set to `-1` to keep models loaded forever (default: `-1`)
- `OLLAMA_MAX_LOADED_MODELS`: Maximum number of models to keep loaded simultaneously (default: `6` for 4 GPUs)

**For detailed information, see:** [Model Preloading Guide](docs/MODEL_PRELOADING.md)

### Using Ollama Commands

Models can also be managed manually using Ollama's native commands:

```bash
# Pull a model
docker exec -it ollama ollama pull llama3

# List available models
docker exec -it ollama ollama list

# Check loaded models (in GPU memory)
docker exec -it ollama ollama ps

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

## Auto-Start on Boot

To configure Docker Compose services to automatically start on system boot (without requiring login), see the [Auto-Start Guide](docs/AUTO_START.md).

Quick setup:
```bash
# Copy service file and enable
sudo cp lmsvr-docker-compose.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable lmsvr-docker-compose.service
sudo systemctl start lmsvr-docker-compose.service
```

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
docker compose logs cloudflared
```

Common issues:
- Credentials not found: Ensure `cloudflare/credentials.json` exists
- Config file incorrect: Verify `cloudflare/config.yml` has correct tunnel ID and service URL
- API Gateway not running: Tunnel depends on `api_gateway` service
- DNS not resolving: Verify DNS record exists in Cloudflare Dashboard
  - Check: Zero Trust → Tunnels → ollama-gateway → Public Hostnames
  - Or manually add CNAME: `lmapi` → `7a14aef0-282b-4d81-9e3a-817338eef3df.cfargotunnel.com`
- DNS not propagated: Wait 2-5 minutes after DNS setup

### Testing Cloudflare Tunnel

Once DNS is configured, test endpoints:
```bash
# Health check
curl https://lmapi.laserpointlabs.com/health

# List models (replace YOUR_API_KEY)
curl -H "Authorization: Bearer YOUR_API_KEY" https://lmapi.laserpointlabs.com/api/models
```

See [Testing](#testing) section for complete curl commands.

### Database errors

Ensure the `data/` directory exists and is writable:
```bash
mkdir -p data
chmod 755 data
```

Check that `DATABASE_URL` in `.env` points to a valid path:
- Docker: `sqlite:///app/data/lmapi.db` (path inside container)
- Local CLI: `sqlite:///./data/lmapi.db` (relative to project root)

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
- Ensure the database file exists: `ls -la data/lmapi.db`
- Check file permissions: `chmod 644 data/lmapi.db`
- Verify `DATABASE_URL` in `.env` matches the CLI's expected path

## Testing

### Testing API Endpoints

**Get an API Key:**
```bash
source venv/bin/activate
python3 cli/cli.py generate-key <customer_id>
```

**Test via localhost:**
```bash
# Health check (no auth)
curl http://localhost:8001/health

# List models
curl -H "Authorization: Bearer YOUR_API_KEY" http://localhost:8001/api/models

# Generate text
curl -X POST -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"llama3.2:1b","prompt":"Say hello","stream":false}' \
  http://localhost:8001/api/generate

# Chat completion
curl -X POST -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"llama3.2:1b","messages":[{"role":"user","content":"Hello!"}],"stream":false}' \
  http://localhost:8001/api/chat
```

**Test via Cloudflare Tunnel:**
```bash
# Replace lmapi.laserpointlabs.com with your domain
# Replace YOUR_API_KEY with your actual API key

# Health check
curl https://lmapi.laserpointlabs.com/health

# List models
curl -H "Authorization: Bearer YOUR_API_KEY" https://lmapi.laserpointlabs.com/api/models

# Generate text
curl -X POST -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"llama3.2:1b","prompt":"Say hello","stream":false}' \
  https://lmapi.laserpointlabs.com/api/generate

# Chat completion
curl -X POST -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"llama3.2:1b","messages":[{"role":"user","content":"Hello!"}],"stream":false}' \
  https://lmapi.laserpointlabs.com/api/chat
```

### Running Automated Tests

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

All services run on the `lmapi_network` Docker network (note: docker-compose.yml may still show `lmsvr_network` - both work):
- Ollama: `http://ollama:11434`
- API Gateway: `http://api_gateway:8000` (internal), `http://localhost:8001` (external)
- Cloudflare Tunnel: Connects to `api_gateway:8000` via Docker network

### Data Storage

- SQLite database: `data/lmapi.db` (persisted via volume mount)
- Ollama models: `ollama_data` Docker volume
- Cloudflare credentials: `cloudflare/credentials.json` (gitignored)

## Recent Changes

See [CHANGELOG.md](CHANGELOG.md) for detailed change history.

**Latest updates:**
- GPU support configuration
- Cloudflare Tunnel container integration with automated setup
- DNS route configuration via CLI
- Configuration sync from .env file
- Complete Cloudflare tunnel testing and documentation
- CI/CD testing improvements
- GPU testing tools
- Fixed API key authentication (HTTPBearer)
- Fixed database name consistency (lmapi.db)
- Fixed log_usage parameter naming

## License

MIT

