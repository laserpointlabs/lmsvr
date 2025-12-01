#!/usr/bin/env python3
"""
Cloudflare Tunnel Setup Script (Python version)
This script automates the setup of Cloudflare Tunnel for the Ollama API Gateway
"""
import subprocess
import sys
import os
import json
import re
from pathlib import Path

# Colors for output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

def print_colored(text, color=Colors.NC):
    """Print colored text."""
    print(f"{color}{text}{Colors.NC}")

def run_command(cmd, check=True, capture_output=True):
    """Run a shell command."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=check,
            capture_output=capture_output,
            text=True
        )
        return result.stdout.strip() if capture_output else None
    except subprocess.CalledProcessError as e:
        if check:
            print_colored(f"Error: {e.stderr}", Colors.RED)
            sys.exit(1)
        return None

def check_cloudflared():
    """Check if cloudflared is installed."""
    result = run_command("which cloudflared", check=False)
    if not result:
        print_colored("Error: cloudflared is not installed", Colors.RED)
        print("Please install cloudflared first:")
        print("  macOS: brew install cloudflared")
        print("  Linux: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/")
        sys.exit(1)
    print_colored("✓ cloudflared is installed", Colors.GREEN)
    return result

def authenticate():
    """Authenticate with Cloudflare."""
    credentials_dir = Path.home() / ".cloudflared"
    cert_file = credentials_dir / "cert.pem"
    
    if cert_file.exists():
        print_colored("✓ Already authenticated", Colors.GREEN)
        return True
    
    print_colored("Step 1: Authenticating with Cloudflare...", Colors.YELLOW)
    print("Opening browser for authentication...")
    run_command("cloudflared tunnel login", check=False, capture_output=False)
    return True

def get_or_create_tunnel(tunnel_name="ollama-gateway"):
    """Get existing tunnel or create a new one."""
    print_colored(f"Step 2: Creating/Getting tunnel '{tunnel_name}'...", Colors.YELLOW)
    
    # Check if tunnel exists
    list_output = run_command("cloudflared tunnel list", check=False)
    if list_output:
        for line in list_output.split('\n'):
            if tunnel_name in line:
                tunnel_id = line.split()[0]
                print_colored(f"✓ Found existing tunnel: {tunnel_id}", Colors.GREEN)
                return tunnel_id
    
    # Create new tunnel
    create_output = run_command(f"cloudflared tunnel create {tunnel_name}", check=False)
    if create_output:
        # Extract tunnel ID from output
        match = re.search(r'Created tunnel ([a-f0-9-]+)', create_output)
        if match:
            tunnel_id = match.group(1)
            print_colored(f"✓ Created tunnel: {tunnel_id}", Colors.GREEN)
            return tunnel_id
    
    print_colored("Error: Could not create or find tunnel", Colors.RED)
    sys.exit(1)

def create_dns_route(tunnel_name, domain):
    """Create DNS route for the tunnel."""
    print_colored(f"Step 3: Creating DNS route for {domain}...", Colors.YELLOW)
    result = run_command(
        f"cloudflared tunnel route dns {tunnel_name} {domain}",
        check=False
    )
    if result is None:
        print_colored("Warning: Could not create DNS route automatically", Colors.YELLOW)
        print("You may need to create a CNAME record manually:")
        print(f"  Name: {domain}")
        print(f"  Value: {tunnel_id}.cfargotunnel.com")
    else:
        print_colored("✓ DNS route created", Colors.GREEN)

def find_credentials_file(tunnel_id):
    """Find the credentials file for the tunnel."""
    credentials_dir = Path.home() / ".cloudflared"
    credentials_file = credentials_dir / f"{tunnel_id}.json"
    
    if credentials_file.exists():
        return str(credentials_file)
    
    # Try to find it in the directory
    for file in credentials_dir.glob("*.json"):
        try:
            with open(file) as f:
                data = json.load(f)
                if data.get("AccountTag") or "AccountTag" in str(data):
                    return str(file)
        except:
            continue
    
    print_colored("Warning: Credentials file not found at expected location", Colors.YELLOW)
    credentials_path = input("Please provide the path to the credentials file: ").strip()
    if os.path.exists(credentials_path):
        return credentials_path
    
    print_colored("Error: Credentials file not found", Colors.RED)
    sys.exit(1)

def create_config_file(tunnel_id, domain, credentials_file, config_dir):
    """Create the Cloudflare Tunnel configuration file."""
    print_colored("Step 4: Creating configuration file...", Colors.YELLOW)
    
    config_file = config_dir / "config.yml"
    
    config_content = f"""tunnel: {tunnel_id}
credentials-file: {credentials_file}

ingress:
  - hostname: {domain}
    service: http://localhost:8000
  - service: http_status:404
"""
    
    with open(config_file, 'w') as f:
        f.write(config_content)
    
    print_colored(f"✓ Configuration file created: {config_file}", Colors.GREEN)
    return config_file

def validate_config(config_file):
    """Validate the tunnel configuration."""
    print_colored("Step 5: Validating configuration...", Colors.YELLOW)
    result = run_command(
        f"cloudflared tunnel --config {config_file} ingress validate",
        check=False
    )
    if result:
        print_colored("✓ Configuration is valid", Colors.GREEN)
    else:
        print_colored("Warning: Configuration validation failed", Colors.YELLOW)

def create_systemd_service(config_file, tunnel_name="ollama-gateway"):
    """Create a systemd service file."""
    print_colored("Step 6: Systemd Service Setup (Optional)", Colors.YELLOW)
    create_service = input("Create systemd service to run tunnel automatically? (y/n): ").strip().lower()
    
    if create_service != 'y':
        return
    
    cloudflared_path = run_command("which cloudflared")
    user = os.getenv("USER")
    service_content = f"""[Unit]
Description=Cloudflare Tunnel for Ollama API Gateway
After=network.target

[Service]
Type=simple
User={user}
ExecStart={cloudflared_path} tunnel --config {config_file} run
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
"""
    
    service_file = Path(f"/etc/systemd/system/cloudflared-tunnel.service")
    
    try:
        service_file.write_text(service_content)
        print_colored(f"✓ Systemd service file created: {service_file}", Colors.GREEN)
        print("\nTo enable and start the service:")
        print("  sudo systemctl daemon-reload")
        print("  sudo systemctl enable cloudflared-tunnel")
        print("  sudo systemctl start cloudflared-tunnel")
    except PermissionError:
        print_colored("Error: Permission denied. Run with sudo to create systemd service.", Colors.RED)

def main():
    """Main setup function."""
    print_colored("Cloudflare Tunnel Setup for Ollama API Gateway", Colors.GREEN)
    print("=" * 50)
    print()
    
    # Get script directory
    script_dir = Path(__file__).parent.absolute()
    config_dir = script_dir
    
    # Step 1: Check cloudflared
    cloudflared_path = check_cloudflared()
    print()
    
    # Step 2: Authenticate
    authenticate()
    print()
    
    # Step 3: Get domain
    domain = input("Enter your domain name (e.g., api.yourdomain.com): ").strip()
    if not domain:
        print_colored("Error: Domain name is required", Colors.RED)
        sys.exit(1)
    print()
    
    # Step 4: Get or create tunnel
    tunnel_id = get_or_create_tunnel()
    print()
    
    # Step 5: Create DNS route
    create_dns_route("ollama-gateway", domain)
    print()
    
    # Step 6: Find credentials file
    credentials_file = find_credentials_file(tunnel_id)
    print()
    
    # Step 7: Create config file
    config_file = create_config_file(tunnel_id, domain, credentials_file, config_dir)
    print()
    
    # Step 8: Validate config
    validate_config(config_file)
    print()
    
    # Step 9: Optional systemd service
    create_systemd_service(config_file)
    print()
    
    # Summary
    print_colored("=" * 50, Colors.GREEN)
    print_colored("Setup Complete!", Colors.GREEN)
    print_colored("=" * 50, Colors.GREEN)
    print()
    print(f"Tunnel ID: {tunnel_id}")
    print(f"Domain: {domain}")
    print(f"Config File: {config_file}")
    print()
    print("To run the tunnel manually:")
    print(f"  cloudflared tunnel --config {config_file} run")
    print()
    print_colored("Important:", Colors.YELLOW)
    print("1. Make sure the API Gateway is running on localhost:8000")
    print("2. Ensure DNS propagation is complete (may take a few minutes)")
    print(f"3. Test the connection: curl https://{domain}/health")
    print()

if __name__ == "__main__":
    main()

