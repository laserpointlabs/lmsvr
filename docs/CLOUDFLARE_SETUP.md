# Cloudflare Tunnel Setup Guide

Complete guide for setting up and testing Cloudflare Tunnel for the LMAPI service.

## Overview

Cloudflare Tunnel provides secure, HTTPS-enabled access to your API Gateway without exposing ports or requiring a public IP address. The tunnel connects outbound to Cloudflare, making it ideal for secure deployments.

## Prerequisites

- Cloudflare account with domain configured
- `cloudflared` CLI installed (or use Docker container)
- Docker and Docker Compose installed

## Quick Setup

### 1. Automated Setup (Recommended)

```bash
cd cloudflare
./setup_tunnel_cli.sh
```

This script will:
- Check/install cloudflared if needed
- Authenticate with Cloudflare
- Create tunnel (or use existing)
- Set up DNS routing
- Copy credentials
- Generate config.yml
- Update .env file

### 2. Manual Setup

See [cloudflare/README.md](../cloudflare/README.md) for detailed manual setup instructions.

## Configuration

### Environment Variables

Set in `.env` file:
```bash
CLOUDFLARE_TUNNEL_URL=https://lmapi.laserpointlabs.com
```

### Config File

The tunnel configuration is in `cloudflare/config.yml`:
```yaml
tunnel: 7a14aef0-282b-4d81-9e3a-817338eef3df
credentials-file: /etc/cloudflared/credentials.json

ingress:
  - hostname: lmapi.laserpointlabs.com
    service: http://api_gateway:8000
  - service: http_status:404
```

**Note:** Use `./cloudflare/update_config_from_env.sh` to sync config.yml from .env file.

## DNS Configuration

### Option 1: Via CLI (Recommended)

```bash
cloudflared tunnel route dns ollama-gateway lmapi.laserpointlabs.com
```

### Option 2: Via Cloudflare Dashboard

1. Go to: **Zero Trust → Tunnels → ollama-gateway → Public Hostnames**
2. Click **"Add a public hostname"**
3. Configure:
   - Subdomain: `lmapi`
   - Domain: `laserpointlabs.com`
   - Service: `http://api_gateway:8000`
4. Save

### Option 3: Manual DNS Record

1. Go to: **DNS → Records**
2. Add CNAME record:
   - Name: `lmapi`
   - Target: `7a14aef0-282b-4d81-9e3a-817338eef3df.cfargotunnel.com`
   - Proxy: Enabled (orange cloud)
   - TTL: Auto

**Wait 2-5 minutes for DNS propagation.**

## Running the Tunnel

### Docker Compose (Recommended)

```bash
# Start all services including tunnel
docker compose up -d

# Start just the tunnel
docker compose up -d cloudflared

# Check status
docker compose ps cloudflared

# View logs
docker compose logs cloudflared

# Restart tunnel
docker compose restart cloudflared
```

The tunnel container:
- Starts automatically with `docker compose up -d`
- Connects to Cloudflare outbound (no local ports)
- Routes traffic to `api_gateway:8000` via Docker network
- Restarts automatically if it crashes

## Testing

### Verify Tunnel Status

**In Cloudflare Dashboard:**
- Go to: Zero Trust → Tunnels → ollama-gateway
- Status should show: **Healthy** (green)
- Connections: Should show 4 active connections

**Via CLI:**
```bash
docker compose logs cloudflared | grep "Registered tunnel connection"
```

### Test Endpoints

**1. Health Check (no authentication):**
```bash
curl https://lmapi.laserpointlabs.com/health
```

Expected response:
```json
{"status":"healthy","service":"api_gateway"}
```

**2. List Models (requires API key):**
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
  https://lmapi.laserpointlabs.com/api/models
```

**3. Generate Text:**
```bash
curl -X POST -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"llama3.2:1b","prompt":"Say hello","stream":false}' \
  https://lmapi.laserpointlabs.com/api/generate
```

**4. Chat Completion:**
```bash
curl -X POST -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"llama3.2:1b","messages":[{"role":"user","content":"Hello!"}],"stream":false}' \
  https://lmapi.laserpointlabs.com/api/chat
```

## Troubleshooting

### DNS Not Resolving

**Symptoms:**
- `curl: (6) Could not resolve host: lmapi.laserpointlabs.com`
- `dig lmapi.laserpointlabs.com` returns no results

**Solutions:**
1. Verify DNS record exists in Cloudflare Dashboard
2. Check Public Hostnames configuration in Zero Trust
3. Wait 2-5 minutes for DNS propagation
4. Try different DNS server: `dig @1.1.1.1 lmapi.laserpointlabs.com`

### Tunnel Shows Healthy But Requests Fail

**Symptoms:**
- Tunnel status: Healthy
- Requests return 502/503 errors
- DNS resolves correctly

**Solutions:**
1. Verify API Gateway is running: `docker compose ps api_gateway`
2. Check API Gateway logs: `docker compose logs api_gateway`
3. Verify service name in config.yml matches Docker service name
4. Test API Gateway directly: `curl http://localhost:8001/health`

### Multiple Tunnels on Same Machine

**Question:** Can I run multiple Cloudflare tunnels simultaneously?

**Answer:** Yes! Multiple tunnels can run on the same machine:
- Each tunnel uses a different tunnel ID
- Each tunnel uses different Docker networks
- Each tunnel uses different config files
- Tunnels connect outbound (no port conflicts)

**Example:** Running `lmapi` and `ndaTool` tunnels together:
- `cloudflared` (lmapi) - Tunnel ID: `7a14aef0-282b-4d81-9e3a-817338eef3df`
- `nda-cloudflared` (ndaTool) - Tunnel ID: `f146869d-e718-46be-aef3-1887b0e2ddce`

Both can run simultaneously without conflicts.

### Tunnel Connection Errors

**Symptoms:**
- Logs show: `failed to serve tunnel connection`
- Tunnel keeps restarting

**Solutions:**
1. Verify credentials file exists: `ls -la cloudflare/credentials.json`
2. Check credentials file permissions: `chmod 644 cloudflare/credentials.json`
3. Verify tunnel ID in config.yml matches actual tunnel
4. Check Cloudflare Dashboard for tunnel status

## Configuration Management

### Syncing Config from .env

After changing `CLOUDFLARE_TUNNEL_URL` in `.env`:

```bash
./cloudflare/update_config_from_env.sh
docker compose restart cloudflared
```

### Changing Domain

1. Update `CLOUDFLARE_TUNNEL_URL` in `.env`
2. Run `./cloudflare/update_config_from_env.sh`
3. Update DNS route in Cloudflare Dashboard
4. Restart tunnel: `docker compose restart cloudflared`
5. Wait for DNS propagation

## Security Notes

- Tunnel provides HTTPS automatically via Cloudflare
- No need to expose ports on your server
- API Gateway remains on private Docker network
- All traffic encrypted end-to-end
- Cloudflare DDoS protection included

## Additional Resources

- [Cloudflare Tunnel Documentation](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)
- [cloudflare/README.md](../cloudflare/README.md) - Detailed setup instructions
- [cloudflare/SETUP_CLI.md](../cloudflare/SETUP_CLI.md) - CLI setup guide








