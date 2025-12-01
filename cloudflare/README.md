# Cloudflare Tunnel Setup

This directory contains configuration for exposing the Ollama API Gateway via Cloudflare Tunnel.

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
   - Update `hostname` with your domain name
   - Update the `credentials-file` path if needed

4. **Create DNS record:**
   ```bash
   cloudflared tunnel route dns ollama-gateway yourdomain.com
   ```

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

## Notes

- The tunnel routes traffic from your Cloudflare domain to `localhost:8000` (the API Gateway)
- Make sure the API Gateway is running before starting the tunnel
- The tunnel provides HTTPS automatically via Cloudflare
- DNS propagation may take a few minutes after setup

