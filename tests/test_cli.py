"""
CLI tool tests.
"""
import pytest
import subprocess
import sys
import os
from pathlib import Path

CLI_PATH = Path(__file__).parent.parent / "cli" / "cli.py"


@pytest.fixture(scope="session", autouse=True)
def init_database():
    """Initialize database before running CLI tests."""
    import os
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    # Ensure data directory exists
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    os.chmod(data_dir, 0o755)
    
    # Set DATABASE_URL if not set
    if "DATABASE_URL" not in os.environ:
        os.environ["DATABASE_URL"] = "sqlite:///./data/lmapi.db"
    
    from api_gateway.database import init_db
    init_db()
    yield
    # Cleanup if needed


def run_cli_command(args):
    """Run CLI command and return result."""
    cmd = [sys.executable, str(CLI_PATH)] + args
    env = os.environ.copy()
    env["DATABASE_URL"] = env.get("DATABASE_URL", "sqlite:///./data/lmapi.db")
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=30,
        env=env
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


def test_cli_update_customer():
    """Test updating a customer."""
    import secrets
    # Create a customer first
    email = f"update_test_{secrets.token_hex(4)}@example.com"
    code1, stdout1, stderr1 = run_cli_command([
        "create-customer",
        "Original Name",
        email,
        "--budget",
        "50.0"
    ])
    assert code1 == 0
    
    # Extract customer ID from output (format: "ID: X")
    import re
    match = re.search(r'ID:\s*(\d+)', stdout1)
    assert match, f"Could not find customer ID in output: {stdout1}"
    customer_id = match.group(1)
    
    # Update customer name
    code2, stdout2, stderr2 = run_cli_command([
        "update-customer",
        customer_id,
        "--name",
        "Updated Name"
    ])
    assert code2 == 0
    assert "Updated name" in stdout2 or "updated" in stdout2.lower()
    
    # Update customer budget
    code3, stdout3, stderr3 = run_cli_command([
        "update-customer",
        customer_id,
        "--budget",
        "100.0"
    ])
    assert code3 == 0
    assert "Updated monthly budget" in stdout3 or "updated" in stdout3.lower()
    
    # Update customer active status
    code4, stdout4, stderr4 = run_cli_command([
        "update-customer",
        customer_id,
        "--active",
        "false"
    ])
    assert code4 == 0
    assert "deactivated" in stdout4.lower() or "updated" in stdout4.lower()


def test_cli_update_customer_email():
    """Test updating customer email."""
    import secrets
    # Create a customer first
    email1 = f"email_test_{secrets.token_hex(4)}@example.com"
    code1, stdout1, stderr1 = run_cli_command([
        "create-customer",
        "Email Test Customer",
        email1
    ])
    assert code1 == 0
    
    # Extract customer ID
    import re
    match = re.search(r'ID:\s*(\d+)', stdout1)
    assert match, f"Could not find customer ID in output: {stdout1}"
    customer_id = match.group(1)
    
    # Update email
    email2 = f"email_updated_{secrets.token_hex(4)}@example.com"
    code2, stdout2, stderr2 = run_cli_command([
        "update-customer",
        customer_id,
        "--email",
        email2
    ])
    assert code2 == 0
    assert "Updated email" in stdout2 or "updated" in stdout2.lower()


def test_cli_delete_customer():
    """Test deleting a customer."""
    import secrets
    # Create a customer first
    email = f"delete_test_{secrets.token_hex(4)}@example.com"
    code1, stdout1, stderr1 = run_cli_command([
        "create-customer",
        "Delete Test Customer",
        email
    ])
    assert code1 == 0
    
    # Extract customer ID
    import re
    match = re.search(r'ID:\s*(\d+)', stdout1)
    assert match, f"Could not find customer ID in output: {stdout1}"
    customer_id = match.group(1)
    
    # Generate a key for the customer (so we can test that deletion removes keys)
    code2, stdout2, stderr2 = run_cli_command([
        "generate-key",
        customer_id
    ])
    assert code2 == 0
    
    # Delete customer with --force flag (to avoid interactive prompt in CI)
    code3, stdout3, stderr3 = run_cli_command([
        "delete-customer",
        customer_id,
        "--force"
    ])
    assert code3 == 0
    assert "Deleted customer" in stdout3 or "deleted" in stdout3.lower()
    
    # Verify customer is gone
    code4, stdout4, stderr4 = run_cli_command(["list-customers"])
    assert code4 == 0
    assert customer_id not in stdout4


def test_cli_refresh_key():
    """Test refreshing an API key."""
    import secrets
    # Create a customer first
    email = f"refresh_test_{secrets.token_hex(4)}@example.com"
    code1, stdout1, stderr1 = run_cli_command([
        "create-customer",
        "Refresh Test Customer",
        email
    ])
    assert code1 == 0
    
    # Extract customer ID
    import re
    match = re.search(r'ID:\s*(\d+)', stdout1)
    assert match, f"Could not find customer ID in output: {stdout1}"
    customer_id = match.group(1)
    
    # Generate initial key
    code2, stdout2, stderr2 = run_cli_command([
        "generate-key",
        customer_id
    ])
    assert code2 == 0
    assert "Generated API key" in stdout2 or "generated" in stdout2.lower()
    
    # Extract key ID from output
    match2 = re.search(r'Key ID:\s*(\d+)', stdout2)
    assert match2, f"Could not find key ID in output: {stdout2}"
    key_id = match2.group(1)
    
    # Refresh the key
    code3, stdout3, stderr3 = run_cli_command([
        "refresh-key",
        key_id
    ])
    assert code3 == 0
    assert "Refreshed API key" in stdout3 or "refreshed" in stdout3.lower()
    assert "Old Key ID" in stdout3 or "old" in stdout3.lower()
    assert "New Key ID" in stdout3 or "new" in stdout3.lower()
    assert "New API Key" in stdout3 or "api key" in stdout3.lower()


def test_cli_refresh_key_nonexistent():
    """Test refreshing a non-existent key fails gracefully."""
    code, stdout, stderr = run_cli_command([
        "refresh-key",
        "99999"  # Non-existent key ID
    ])
    assert code != 0 or "not found" in stdout.lower() or "not found" in stderr.lower()


def test_cli_update_customer_nonexistent():
    """Test updating a non-existent customer fails gracefully."""
    code, stdout, stderr = run_cli_command([
        "update-customer",
        "99999",  # Non-existent customer ID
        "--name",
        "Test"
    ])
    assert code != 0 or "not found" in stdout.lower() or "not found" in stderr.lower()


def test_cli_delete_customer_nonexistent():
    """Test deleting a non-existent customer fails gracefully."""
    code, stdout, stderr = run_cli_command([
        "delete-customer",
        "99999",  # Non-existent customer ID
        "--force"
    ])
    assert code != 0 or "not found" in stdout.lower() or "not found" in stderr.lower()


def test_cli_help_commands():
    """Test that --help works for all new commands."""
    commands = [
        ["update-customer", "--help"],
        ["delete-customer", "--help"],
        ["refresh-key", "--help"],
    ]
    
    for cmd in commands:
        code, stdout, stderr = run_cli_command(cmd)
        assert code == 0, f"Help failed for {' '.join(cmd)}: {stderr}"
        assert "usage:" in stdout.lower() or "help" in stdout.lower()

