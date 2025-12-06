# Auto-Start Docker Compose Services on Boot

This guide explains how to configure Docker Compose services to automatically start when the system boots, without requiring a user login.

## Problem

By default, Docker Compose services don't automatically start on system boot. Even though Docker itself starts automatically, your containers won't start until you manually run `docker compose up -d`.

## Solution

Create a systemd service that automatically starts your Docker Compose services on boot.

## Setup Instructions

### Step 1: Create Systemd Service File

A service file template has been created in the project root: `lmsvr-docker-compose.service`

### Step 2: Install the Service

Run these commands to install and enable the service:

```bash
# Copy the service file to systemd directory
sudo cp lmsvr-docker-compose.service /etc/systemd/system/

# Reload systemd to recognize the new service
sudo systemctl daemon-reload

# Enable the service to start on boot
sudo systemctl enable lmsvr-docker-compose.service

# Start the service now (optional - to test)
sudo systemctl start lmsvr-docker-compose.service
```

### Step 3: Verify Service Status

Check that the service is enabled and running:

```bash
# Check service status
sudo systemctl status lmsvr-docker-compose.service

# Verify services are running
docker compose ps
```

### Step 4: Test Auto-Start

To test that services start automatically on boot:

```bash
# Reboot the system
sudo reboot

# After reboot, check services (without logging in if possible)
# Or SSH in and check:
docker compose ps
```

## Service Management

### Start Services Manually

```bash
sudo systemctl start lmsvr-docker-compose.service
```

### Stop Services

```bash
sudo systemctl stop lmsvr-docker-compose.service
```

### Restart Services

```bash
sudo systemctl restart lmsvr-docker-compose.service
```

### Disable Auto-Start

If you want to disable auto-start:

```bash
sudo systemctl disable lmsvr-docker-compose.service
```

### View Service Logs

```bash
# View service logs
sudo journalctl -u lmsvr-docker-compose.service -f

# View recent logs
sudo journalctl -u lmsvr-docker-compose.service -n 50
```

## Troubleshooting

### Services Don't Start on Boot

1. **Check service is enabled:**
   ```bash
   sudo systemctl is-enabled lmsvr-docker-compose.service
   ```
   Should output: `enabled`

2. **Check Docker is enabled:**
   ```bash
   sudo systemctl is-enabled docker.service
   ```
   Should output: `enabled`

3. **Check service logs:**
   ```bash
   sudo journalctl -u lmsvr-docker-compose.service -n 50
   ```

4. **Verify working directory:**
   Ensure the `WorkingDirectory` in the service file matches your project location

### Permission Issues

If you see permission errors:

1. **Check file ownership:**
   ```bash
   ls -la /home/jdehart/Working/lmsvr
   ```

2. **Ensure user/group in service file matches:**
   ```bash
   whoami
   id
   ```

3. **Check Docker socket permissions:**
   ```bash
   groups
   ```
   Your user should be in the `docker` group

### Services Start But Containers Don't

1. **Check Docker Compose file:**
   ```bash
   cd /home/jdehart/Working/lmsvr
   docker compose config
   ```

2. **Check container logs:**
   ```bash
   docker compose logs
   ```

3. **Verify environment variables:**
   Ensure `.env` file exists and is readable

## Alternative: Using Docker Restart Policies

You can also use Docker's built-in restart policies in `docker-compose.yml`:

```yaml
services:
  ollama:
    restart: unless-stopped
  api_gateway:
    restart: unless-stopped
```

However, this requires Docker to be running, which may not start containers if Docker Compose isn't explicitly invoked. The systemd service approach is more reliable.

## Service File Details

The service file (`lmsvr-docker-compose.service`) includes:

- **Requires=docker.service**: Ensures Docker starts first
- **After=network-online.target**: Waits for network to be ready
- **Type=oneshot**: Runs once and exits (but RemainAfterExit keeps it active)
- **RemainAfterExit=yes**: Keeps service active after ExecStart completes
- **WorkingDirectory**: Sets the project directory
- **User/Group**: Runs as your user to avoid permission issues

## Security Considerations

- The service runs as your user, not root
- Only starts services defined in your docker-compose.yml
- Uses standard Docker Compose commands
- No elevated privileges beyond Docker access

## Related Documentation

- [Model Preloading Guide](MODEL_PRELOADING.md) - Models will auto-load when services start
- [README.md](../README.md) - Main project documentation










