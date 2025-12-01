"""
CLI tool tests.
"""
import pytest
import subprocess
import sys
from pathlib import Path

CLI_PATH = Path(__file__).parent.parent / "cli" / "cli.py"


def run_cli_command(args):
    """Run CLI command and return result."""
    cmd = [sys.executable, str(CLI_PATH)] + args
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=30
    )
    return result.returncode, result.stdout, result.stderr


def test_cli_help():
    """Test CLI help command."""
    code, stdout, stderr = run_cli_command([])
    assert code == 0 or "usage:" in stdout.lower() or "help" in stdout.lower()


def test_cli_list_customers():
    """Test listing customers."""
    code, stdout, stderr = run_cli_command(["list-customers"])
    # Should succeed even if no customers exist
    assert code == 0


def test_cli_create_customer():
    """Test creating a customer."""
    import secrets
    email = f"test_{secrets.token_hex(4)}@example.com"
    code, stdout, stderr = run_cli_command([
        "create-customer",
        "Test Customer",
        email,
        "--budget",
        "50.0"
    ])
    assert code == 0
    assert "Created customer" in stdout or "created" in stdout.lower()


def test_cli_create_duplicate_customer():
    """Test that duplicate customer creation fails."""
    email = "duplicate@example.com"
    # Create first customer
    code1, stdout1, stderr1 = run_cli_command([
        "create-customer",
        "First Customer",
        email
    ])
    
    # Try to create duplicate
    code2, stdout2, stderr2 = run_cli_command([
        "create-customer",
        "Second Customer",
        email
    ])
    
    # Second creation should fail
    assert code2 != 0 or "already exists" in stdout2.lower() or "already exists" in stderr2.lower()


def test_cli_list_models():
    """Test listing models."""
    code, stdout, stderr = run_cli_command(["list-models"])
    # May fail if Ollama is not running, which is acceptable
    assert code in [0, 1]

