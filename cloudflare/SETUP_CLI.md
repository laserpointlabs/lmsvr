# Cloudflare Tunnel CLI Setup Guide

This guide documents how to set up Cloudflare Tunnel using the CLI, and provides an automated script for easy setup on other computers.

**Quick Start:** Run the automated script:
```bash
cd cloudflare
./setup_tunnel_cli.sh
```

This script automates all the steps below.

## Manual CLI Setup Steps

### 1. Check if cloudflared is installed

```bash
which cloudflared
cloudflared --version
```

If not installed, install it:
```bash
# Linux (snap)
sudo snap install cloudflared

# Or download binary
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
sudo mv cloudflared-linux-amd64 /usr/local/bin/cloudflared
sudo chmod +x /usr/local/bin/cloudflared
```

### 2. Authenticate with Cloudflare

```bash
cloudflared tunnel login
```

This opens a browser window for authentication. Select your domain.

### 3. List existing tunnels (optional)

```bash
cloudflared tunnel list
```

### 4. Create a new tunnel

```bash
cloudflared tunnel create ollama-gateway
```

This will:
- Create a tunnel named "ollama-gateway"
- Save credentials to `~/.cloudflared/<tunnel-id>.json`
- Display the tunnel ID

Example output:
```
Created tunnel ollama-gateway with id 7a14aef0-282b-4d81-9e3a-817338eef3df
Tunnel credentials written to /home/user/.cloudflared/7a14aef0-282b-4d81-9e3a-817338eef3df.json
```

### 5. Create DNS route

```bash
cloudflared tunnel route dns ollama-gateway api.yourdomain.com
```

This creates a CNAME record pointing to your tunnel.

### 6. Copy credentials to project

```bash
# Get tunnel ID
TUNNEL_ID=$(cloudflared tunnel list | grep ollama-gateway | awk '{print $1}')

# Copy credentials and set permissions (Docker needs readable permissions)
cp ~/.cloudflared/${TUNNEL_ID}.json cloudflare/credentials.json
chmod 644 cloudflare/credentials.json
```

**Important:** The credentials file must be readable by the Docker container (644 permissions).

### 7. Create config file

Create `cloudflare/config.yml`:

```yaml
tunnel: <TUNNEL_ID>
credentials-file: /etc/cloudflared/credentials.json

ingress:
  - hostname: api.yourdomain.com
    service: http://api_gateway:8000
  - service: http_status:404
```

Replace `<TUNNEL_ID>` with your actual tunnel ID.

### 8. Start Docker containers

```bash
docker compose up -d
```

The Cloudflare tunnel container will automatically connect using the config file.

## Verification

### Check tunnel status

```bash
# List tunnels
cloudflared tunnel list

# Get tunnel info
cloudflared tunnel info ollama-gateway
```

### Check Docker container

```bash
docker compose ps cloudflared
docker compose logs cloudflared
```

### Test the endpoint

```bash
curl https://api.yourdomain.com/health
```

## Troubleshooting

### Tunnel won't start

- Verify credentials file exists: `ls -la cloudflare/credentials.json`
- Check config file syntax: `cloudflared tunnel --config cloudflare/config.yml ingress validate`
- Verify tunnel ID matches: `cloudflared tunnel list`

### DNS not resolving

- Wait a few minutes for DNS propagation
- Verify CNAME record in Cloudflare dashboard
- Check DNS: `dig api.yourdomain.com`

### Container can't find credentials

- Ensure file exists: `ls -la cloudflare/credentials.json`
- Check file permissions: `chmod 644 cloudflare/credentials.json` (must be readable)
- Verify volume mount in docker-compose.yml
- Check container logs: `docker compose logs cloudflared`
- Ensure file is a regular file, not a directory: `file cloudflare/credentials.json`

## Using the Automated Script

For automated setup, use the provided script:

```bash
cd cloudflare
./setup_tunnel_cli.sh
```

This script automates all the steps above:
1. Checks/installs cloudflared
2. Authenticates with Cloudflare
3. Creates or uses existing tunnel
4. Sets up DNS routing
5. Copies credentials with correct permissions
6. Creates configuration file
7. Validates configuration

**The script is designed to be run on any computer** - it handles installation, authentication, and setup automatically.

### What the Script Does

- **Checks for cloudflared:** Installs if missing (via snap or binary download)
- **Handles authentication:** Opens browser for Cloudflare login if needed
- **Manages tunnel:** Creates new tunnel or uses existing one
- **DNS setup:** Creates DNS routes automatically
- **File management:** Copies credentials and sets proper permissions (644)
- **Configuration:** Generates Docker-compatible config.yml
- **Validation:** Verifies the configuration is correct

After running the script, simply start Docker containers:
```bash
docker compose up -d
```

The Cloudflare tunnel container will start automatically and connect.

