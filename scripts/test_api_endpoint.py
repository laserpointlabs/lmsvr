#!/usr/bin/env python3
"""
Test script that creates a user, generates an API key, tests the mistral model,
and then cleans up by deleting the user.

Uses the lmapi.laserpointlabs.com endpoint (not localhost).
"""
import sys
import os
import subprocess
import re
import json
import time
import httpx
from typing import Optional, Tuple

# Colors for output
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color

BASE_URL = "https://lmapi.laserpointlabs.com"
MODEL = "mistral"
TEST_QUESTION = "What is 2+2? Answer in one sentence."


def print_step(message: str):
    """Print a step message."""
    print(f"{BLUE}→ {message}{NC}")


def print_success(message: str):
    """Print a success message."""
    print(f"{GREEN}✓ {message}{NC}")


def print_error(message: str):
    """Print an error message."""
    print(f"{RED}✗ {message}{NC}")


def print_warning(message: str):
    """Print a warning message."""
    print(f"{YELLOW}⚠ {message}{NC}")


def run_cli_command(command: list) -> Tuple[int, str, str]:
    """Run a CLI command and return exit code, stdout, stderr."""
    try:
        result = subprocess.run(
            ["python3", "cli/cli.py"] + command,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Command timed out"
    except Exception as e:
        return 1, "", str(e)


def create_test_customer() -> Optional[int]:
    """Create a test customer and return the customer ID."""
    print_step("Creating test customer...")
    
    # Generate unique email based on timestamp
    timestamp = int(time.time())
    email = f"test_{timestamp}@test.local"
    name = f"Test User {timestamp}"
    
    code, stdout, stderr = run_cli_command([
        "create-customer",
        name,
        email,
        "--budget",
        "1000.00"
    ])
    
    if code != 0:
        print_error(f"Failed to create customer: {stderr}")
        return None
    
    # Extract customer ID from output
    # Format: "✓ Created customer: Test User 1234567890 (ID: 5)"
    match = re.search(r'ID:\s*(\d+)', stdout)
    if match:
        customer_id = int(match.group(1))
        print_success(f"Created customer: {name} (ID: {customer_id})")
        return customer_id
    else:
        print_error("Could not extract customer ID from output")
        print(f"Output: {stdout}")
        return None


def generate_api_key(customer_id: int) -> Optional[str]:
    """Generate an API key for a customer and return the key."""
    print_step(f"Generating API key for customer {customer_id}...")
    
    code, stdout, stderr = run_cli_command([
        "generate-key",
        str(customer_id)
    ])
    
    if code != 0:
        print_error(f"Failed to generate API key: {stderr}")
        return None
    
    # Extract API key from output
    # Format: "  API Key: sk_..."
    match = re.search(r'API Key:\s*(sk_\S+)', stdout)
    if match:
        api_key = match.group(1)
        print_success("API key generated successfully")
        return api_key
    else:
        print_error("Could not extract API key from output")
        print(f"Output: {stdout}")
        return None


def test_chat_api(api_key: str) -> Tuple[bool, dict]:
    """Test the chat API with the mistral model."""
    print_step(f"Testing chat API with {MODEL} model...")
    print(f"  Question: {TEST_QUESTION}")
    
    url = f"{BASE_URL}/api/chat"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": TEST_QUESTION}
        ],
        "stream": False
    }
    
    try:
        start_time = time.time()
        response = httpx.post(url, json=payload, headers=headers, timeout=60.0)
        elapsed_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"API request successful ({elapsed_time:.2f}s)")
            return True, {
                "status_code": response.status_code,
                "response": data,
                "elapsed_time": elapsed_time
            }
        else:
            print_error(f"API request failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"  Error: {error_data}")
            except:
                print(f"  Error: {response.text}")
            return False, {
                "status_code": response.status_code,
                "error": response.text
            }
    except httpx.TimeoutException:
        print_error("API request timed out")
        return False, {"error": "Request timed out"}
    except httpx.RequestError as e:
        print_error(f"API request failed: {e}")
        return False, {"error": str(e)}
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return False, {"error": str(e)}


def delete_customer(customer_id: int) -> bool:
    """Delete a customer."""
    print_step(f"Deleting customer {customer_id}...")
    
    code, stdout, stderr = run_cli_command([
        "delete-customer",
        str(customer_id),
        "--force"
    ])
    
    if code != 0:
        print_error(f"Failed to delete customer: {stderr}")
        return False
    
    print_success("Customer deleted successfully")
    return True


def print_results(success: bool, customer_id: Optional[int], api_key: Optional[str], 
                  test_result: Optional[dict]):
    """Print test results summary."""
    print("\n" + "=" * 70)
    print(f"{BLUE}TEST RESULTS{NC}")
    print("=" * 70)
    
    if customer_id:
        print(f"Customer ID: {customer_id}")
    else:
        print(f"{RED}Customer ID: FAILED{NC}")
    
    if api_key:
        # Show only first 20 chars for security
        masked_key = api_key[:20] + "..." if len(api_key) > 20 else api_key
        print(f"API Key: {masked_key}")
    else:
        print(f"{RED}API Key: FAILED{NC}")
    
    if test_result:
        if test_result.get("status_code") == 200:
            print(f"{GREEN}API Test: PASSED{NC}")
            print(f"  Status Code: {test_result.get('status_code')}")
            print(f"  Response Time: {test_result.get('elapsed_time', 0):.2f}s")
            
            # Extract and show response content
            response_data = test_result.get("response", {})
            if "message" in response_data:
                message = response_data["message"]
                content = message.get("content", "") if isinstance(message, dict) else str(message)
                if content:
                    # Truncate if too long
                    if len(content) > 200:
                        content = content[:200] + "..."
                    print(f"  Response: {content}")
        else:
            print(f"{RED}API Test: FAILED{NC}")
            print(f"  Status Code: {test_result.get('status_code', 'N/A')}")
            if "error" in test_result:
                print(f"  Error: {test_result['error']}")
    else:
        print(f"{RED}API Test: NOT RUN{NC}")
    
    print("=" * 70)
    
    # Overall status
    if success and test_result and test_result.get("status_code") == 200:
        print(f"\n{GREEN}✓ OVERALL TEST: PASSED{NC}")
        return True
    else:
        print(f"\n{RED}✗ OVERALL TEST: FAILED{NC}")
        return False


def main():
    """Main test function."""
    print(f"{BLUE}{'=' * 70}{NC}")
    print(f"{BLUE}API Endpoint Test Script{NC}")
    print(f"{BLUE}{'=' * 70}{NC}")
    print(f"Endpoint: {BASE_URL}")
    print(f"Model: {MODEL}")
    print(f"Test Question: {TEST_QUESTION}")
    print()
    
    customer_id = None
    api_key = None
    test_result = None
    cleanup_success = False
    
    try:
        # Step 1: Create customer
        customer_id = create_test_customer()
        if not customer_id:
            print_results(False, None, None, None)
            return 1
        
        # Step 2: Generate API key
        api_key = generate_api_key(customer_id)
        if not api_key:
            print_results(False, customer_id, None, None)
            # Try to clean up
            if customer_id:
                delete_customer(customer_id)
            return 1
        
        # Step 3: Test API
        success, test_result = test_chat_api(api_key)
        
        # Step 4: Cleanup
        if customer_id:
            cleanup_success = delete_customer(customer_id)
        
        # Step 5: Print results
        overall_success = print_results(
            success and cleanup_success,
            customer_id,
            api_key,
            test_result
        )
        
        return 0 if overall_success else 1
        
    except KeyboardInterrupt:
        print_warning("\nTest interrupted by user")
        # Try to clean up
        if customer_id:
            print_step("Cleaning up...")
            delete_customer(customer_id)
        return 1
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        # Try to clean up
        if customer_id:
            print_step("Cleaning up...")
            delete_customer(customer_id)
        return 1


if __name__ == "__main__":
    sys.exit(main())












