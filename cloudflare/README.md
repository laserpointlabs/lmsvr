# Cloudflare Tunnel Setup

This directory contains configuration for exposing the Ollama API Gateway via Cloudflare Tunnel.

## Quick Setup (Automated)

Use the setup script to automate the entire process:

**Bash version:**
```bash
cd cloudflare
./setup_tunnel.sh
```

**Python version:**
```bash
cd cloudflare
python3 setup_tunnel.py
```

The script will:
1. Check if cloudflared is installed
2. Authenticate with Cloudflare (opens browser)
3. Create or find the tunnel
4. Set up DNS routing
5. Create the configuration file
6. Optionally create a systemd service

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

### Manual Run
```bash
cloudflared tunnel --config cloudflare/config.yml run
```

### Systemd Service (if created by script)
```bash
sudo systemctl start cloudflared-tunnel
sudo systemctl enable cloudflared-tunnel  # Auto-start on boot
sudo systemctl status cloudflared-tunnel   # Check status
```

### Docker Compose (Alternative)
You can also add cloudflared to your docker-compose.yml if preferred.

## Notes

- The tunnel routes traffic from your Cloudflare domain to `localhost:8000` (the API Gateway)
- Make sure the API Gateway is running before starting the tunnel
- The tunnel provides HTTPS automatically via Cloudflare
- DNS propagation may take a few minutes after setup

