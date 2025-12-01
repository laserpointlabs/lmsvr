# Quick Start Guide

Complete setup guide for deploying Ollama API Gateway on a new computer.

## Automated Setup (Recommended)

Run the complete setup script:

```bash
./setup.sh
```

This script will:
1. ✅ Check prerequisites (Docker, Python, etc.)
2. ✅ Create necessary directories
3. ✅ Setup environment variables
4. ✅ Install Python dependencies
5. ✅ Build Docker images
6. ✅ Start core services (Ollama + API Gateway)
7. ✅ Test service health
8. ✅ Initialize database
9. ✅ Optionally setup Cloudflare Tunnel
10. ✅ Run basic tests

**Time:** ~5-10 minutes depending on internet speed and system performance.

## Manual Setup

If you prefer manual setup or need more control:

### 1. Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Cloudflare account (optional, for tunnel)

### 2. Clone Repository

```bash
git clone <repository-url>
cd lmsvr
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
```

### 4. Setup Python Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r api_gateway/requirements.txt
pip install -r requirements-dev.txt
```

### 5. Start Services

```bash
docker compose up -d --build
```

### 6. Initialize Database

```bash
source venv/bin/activate
python3 -c "from api_gateway.database import init_db; init_db()"
```

### 7. Setup Cloudflare Tunnel (Optional)

```bash
cd cloudflare
./setup_tunnel_cli.sh
```

**Domain Configuration:** The domain is configured via `CLOUDFLARE_TUNNEL_URL` in your `.env` file (default: `https://lmapi.laserpointlabs.com`).

To change the domain:
1. Update `CLOUDFLARE_TUNNEL_URL` in your `.env` file
2. Run `./cloudflare/update_config_from_env.sh` to update the config file
3. Restart the tunnel: `docker compose restart cloudflared`
4. Set up DNS route (see below)

**DNS Setup:**
After tunnel is created, configure DNS:

**Option 1: Via CLI (recommended)**
```bash
cloudflared tunnel route dns ollama-gateway lmapi.laserpointlabs.com
```

**Option 2: Via Cloudflare Dashboard**
- Go to: Zero Trust → Tunnels → ollama-gateway → Public Hostnames
- Add hostname: `lmapi.laserpointlabs.com` → `http://api_gateway:8000`

**Option 3: Manual DNS Record**
- Go to: DNS → Records
- Add CNAME: `lmapi` → `7a14aef0-282b-4d81-9e3a-817338eef3df.cfargotunnel.com`
- Proxy: Enabled

Wait 2-5 minutes for DNS propagation, then test:
```bash
curl https://lmapi.laserpointlabs.com/health
```

### 8. Verify Installation

```bash
# Check services
docker compose ps

# Test API Gateway
curl http://localhost:8001/health

# Test Ollama
curl http://localhost:11434/api/tags
```

## Post-Setup

### Create Your First Customer

```bash
source venv/bin/activate
can ```

### Generate API Key

```bash
python3 cli/cli.py generate-key 1
```

**Important:** Save the API key securely - it won't be shown again!

### Pull Models

**Pull models manually:**

```bash
docker exec -it ollama ollama pull llama3.2:1b
docker exec -it ollama ollama pull mistral
```

### Set Pricing

```bash
python3 cli/cli.py set-pricing llama3 0.001 0.002
python3 cli/cli.py set-pricing mistral 0.0015 0.003
```

### Test the API

**Via localhost:**
```bash
curl -H "Authorization: Bearer <your_api_key>" \
  http://localhost:8001/api/models
```

**Via Cloudflare Tunnel (after DNS setup):**
```bash
curl -H "Authorization: Bearer <your_api_key>" \
  https://lmapi.laserpointlabs.com/api/models
```

**Complete test examples:**
```bash
# Health check (no auth)
curl https://lmapi.laserpointlabs.com/health

# Generate text
curl -X POST -H "Authorization: Bearer <your_api_key>" \
  -H "Content-Type: application/json" \
  -d '{"model":"llama3.2:1b","prompt":"Say hello","stream":false}' \
  https://lmapi.laserpointlabs.com/api/generate

# Chat completion
curl -X POST -H "Authorization: Bearer <your_api_key>" \
  -H "Content-Type: application/json" \
  -d '{"model":"llama3.2:1b","messages":[{"role":"user","content":"Hello!"}],"stream":false}' \
  https://lmapi.laserpointlabs.com/api/chat
```

## Troubleshooting

### Services won't start

```bash
# Check logs
docker compose logs ollama
docker compose logs api_gateway

# Restart services
docker compose restart
```

### Port conflicts

If port 8001 is in use:
```bash
# Find what's using it
sudo lsof -i :8001

# Or change port in docker-compose.yml
```

### Database errors

```bash
# Ensure data directory exists
mkdir -p data
chmod 755 data

# Reinitialize database
source venv/bin/activate
python3 -c "from api_gateway.database import init_db; init_db()"
```

### Cloudflare Tunnel issues

See `cloudflare/SETUP_CLI.md` for detailed troubleshooting.

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Review [CHANGELOG.md](CHANGELOG.md) for recent changes
- Check `cloudflare/README.md` for tunnel configuration
- See `scripts/README.md` for GPU testing tools

## Support

For issues or questions:
1. Check the troubleshooting sections in README.md
2. Review service logs: `docker compose logs <service>`
3. Verify configuration: `cat .env`
4. Check service status: `docker compose ps`

