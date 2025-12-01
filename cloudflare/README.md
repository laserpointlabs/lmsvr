# Cloudflare Tunnel Setup

This directory contains configuration for exposing the Ollama API Gateway via Cloudflare Tunnel.

**Important:** The domain/hostname is configured via `CLOUDFLARE_TUNNEL_URL` in your `.env` file. After changing the domain in `.env`, run `./update_config_from_env.sh` to sync the config file.

## Quick Setup (Automated)

### CLI Setup (Recommended)

Use the CLI setup script for automated setup:

```bash
cd cloudflare
./setup_tunnel_cli.sh
```

This script will:
1. Check/install cloudflared if needed
2. Authenticate with Cloudflare (opens browser)
3. Create or use existing tunnel
4. Set up DNS routing
5. Copy credentials to project
6. Create configuration file
7. Validate configuration

**See [SETUP_CLI.md](SETUP_CLI.md) for detailed CLI setup documentation.**

### Alternative Setup Scripts

**Interactive Bash script:**
```bash
cd cloudflare
./setup_tunnel.sh
```

**Python version:**
```bash
cd cloudflare
python3 setup_tunnel.py
```

These scripts provide similar functionality with interactive prompts.

## Manual Setup Instructions

If you prefer to set up manually:

1. **Authenticate with Cloudflare:**
   ```bash
   cloudflared tunnel login
   ```

2. **Create a tunnel:**
   ```bash
   cloudflared tunnel create ollama-gateway
   ```
   This will output a tunnel ID. Save this ID.

3. **Update config.yml:**
   - Replace `<TUNNEL_ID>` with your actual tunnel ID
   - Set `CLOUDFLARE_TUNNEL_URL` in your `.env` file (e.g., `https://lmapi.laserpointlabs.com`)
   - Run `./update_config_from_env.sh` to sync config.yml from .env
   - Or manually update `hostname` in config.yml

4. **Create DNS record via CLI:**
   ```bash
   cloudflared tunnel route dns ollama-gateway lmapi.laserpointlabs.com
   ```
   
   **OR manually in Cloudflare Dashboard:**
   - Go to: Zero Trust → Tunnels → ollama-gateway → Public Hostnames
   - Click "Add a public hostname"
   - Subdomain: `lmapi`
   - Domain: `laserpointlabs.com`
   - Service: `http://api_gateway:8000`
   - Save
   
   **OR add DNS CNAME record:**
   - Go to: DNS → Records
   - Add CNAME: `lmapi` → `7a14aef0-282b-4d81-9e3a-817338eef3df.cfargotunnel.com`
   - Proxy: Enabled (orange cloud)

5. **Run the tunnel:**
   ```bash
   cloudflared tunnel run ollama-gateway
   ```
   
   Or use the config file:
   ```bash
   cloudflared tunnel --config cloudflare/config.yml run
   ```

6. **Run as a service (optional):**
   ```bash
   sudo cloudflared service install
   ```

## Running the Tunnel

### Docker Compose (Recommended)
```bash
# Start all services including Cloudflare tunnel
docker compose up -d

# Or start just the tunnel
docker compose up -d cloudflared

# Check status
docker compose ps cloudflared

# View logs
docker compose logs cloudflared

# Stop tunnel
docker compose stop cloudflared
```

**Note:** The Cloudflare tunnel container starts automatically with `docker compose up -d` (no profile needed).

The tunnel container will automatically:
- Connect to your Cloudflare tunnel
- Route traffic from your domain to the API Gateway
- Restart automatically if it crashes

### Manual Run (Alternative)
```bash
cloudflared tunnel --config cloudflare/config.yml run
```

### Systemd Service (Alternative)
```bash
sudo systemctl start cloudflared-tunnel
sudo systemctl enable cloudflared-tunnel  # Auto-start on boot
sudo systemctl status cloudflared-tunnel   # Check status
```

## Configuration Management

### Domain Configuration

The domain is configured via `CLOUDFLARE_TUNNEL_URL` in your `.env` file:

```bash
CLOUDFLARE_TUNNEL_URL=https://lmapi.laserpointlabs.com
```

**To change the domain:**
1. Edit `CLOUDFLARE_TUNNEL_URL` in your `.env` file
2. Run `./update_config_from_env.sh` to update `config.yml`
3. Restart the tunnel: `docker compose restart cloudflared`
4. Update DNS route in Cloudflare dashboard

### Syncing Config from .env

Use the provided script to keep `config.yml` in sync with your `.env` file:

```bash
./cloudflare/update_config_from_env.sh
```

This script:
- Reads `CLOUDFLARE_TUNNEL_URL` from `.env`
- Updates `config.yml` with the correct hostname
- Preserves tunnel ID and other settings

## Testing the Tunnel

Once DNS is configured and propagated (2-5 minutes), test the tunnel:

```bash
# Health check (no authentication)
curl https://lmapi.laserpointlabs.com/health

# List models (requires API key)
curl -H "Authorization: Bearer YOUR_API_KEY" https://lmapi.laserpointlabs.com/api/models

# Generate text
curl -X POST -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"llama3.2:1b","prompt":"Say hello","stream":false}' \
  https://lmapi.laserpointlabs.com/api/generate
```

**Troubleshooting:**
- If DNS doesn't resolve: Verify DNS record exists in Cloudflare Dashboard
- If tunnel shows "Healthy" but requests fail: Check Public Hostnames configuration
- If 502/503 errors: Verify API Gateway is running and accessible from tunnel container

## Notes

- The tunnel routes traffic from your Cloudflare domain to `api_gateway:8000` (via Docker network)
- Make sure the API Gateway is running before starting the tunnel
- The tunnel provides HTTPS automatically via Cloudflare
- DNS propagation may take 2-5 minutes after setup
- Domain configuration comes from `.env` file, not hardcoded
- Multiple tunnels can run simultaneously on the same machine (different tunnel IDs)

