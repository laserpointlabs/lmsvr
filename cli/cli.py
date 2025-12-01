#!/usr/bin/env python3
"""
CLI tool for managing customers, API keys, and viewing usage reports.
"""
import sys
import os
import argparse
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional
import json
import csv

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from api_gateway.database import get_db_session, Customer, APIKey, UsageLog, PricingConfig
from api_gateway.auth import hash_api_key
from api_gateway.usage import get_usage_summary, check_budget


def generate_api_key() -> str:
    """Generate a secure API key."""
    return f"sk_{secrets.token_urlsafe(32)}"


def create_customer(name: str, email: str, monthly_budget: Optional[float] = None):
    """Create a new customer."""
    db = get_db_session()
    try:
        # Check if email already exists
        existing = db.query(Customer).filter(Customer.email == email).first()
        if existing:
            print(f"Error: Customer with email {email} already exists")
            return
        
        customer = Customer(
            name=name,
            email=email,
            monthly_budget=monthly_budget,
            active=True
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)
        
        print(f"✓ Created customer: {customer.name} (ID: {customer.id})")
        print(f"  Email: {customer.email}")
        if monthly_budget:
            print(f"  Monthly Budget: ${monthly_budget:.2f}")
    except Exception as e:
        db.rollback()
        print(f"Error creating customer: {e}")
    finally:
        db.close()


def generate_key(customer_id: int):
    """Generate an API key for a customer."""
    db = get_db_session()
    try:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            print(f"Error: Customer with ID {customer_id} not found")
            return
        
        # Generate key
        api_key = generate_api_key()
        key_hash = hash_api_key(api_key)
        
        # Store in database
        db_key = APIKey(
            customer_id=customer_id,
            key_hash=key_hash,
            active=True
        )
        db.add(db_key)
        db.commit()
        db.refresh(db_key)
        
        print(f"✓ Generated API key for {customer.name} (ID: {customer.id})")
        print(f"  Key ID: {db_key.id}")
        print(f"  API Key: {api_key}")
        print(f"  ⚠️  Save this key securely - it will not be shown again!")
    except Exception as e:
        db.rollback()
        print(f"Error generating key: {e}")
    finally:
        db.close()


def revoke_key(key_id: int):
    """Revoke an API key."""
    db = get_db_session()
    try:
        db_key = db.query(APIKey).filter(APIKey.id == key_id).first()
        if not db_key:
            print(f"Error: API key with ID {key_id} not found")
            return
        
        db_key.active = False
        db.commit()
        
        customer = db.query(Customer).filter(Customer.id == db_key.customer_id).first()
        print(f"✓ Revoked API key {key_id} for {customer.name}")
    except Exception as e:
        db.rollback()
        print(f"Error revoking key: {e}")
    finally:
        db.close()


def list_customers():
    """List all customers."""
    db = get_db_session()
    try:
        customers = db.query(Customer).order_by(Customer.id).all()
        if not customers:
            print("No customers found")
            return
        
        print(f"\n{'ID':<5} {'Name':<30} {'Email':<40} {'Budget':<15} {'Active':<10}")
        print("-" * 100)
        for customer in customers:
            budget_str = f"${customer.monthly_budget:.2f}" if customer.monthly_budget else "None"
            active_str = "Yes" if customer.active else "No"
            print(f"{customer.id:<5} {customer.name:<30} {customer.email:<40} {budget_str:<15} {active_str:<10}")
        print()
    except Exception as e:
        print(f"Error listing customers: {e}")
    finally:
        db.close()


def list_keys(customer_id: int):
    """List API keys for a customer."""
    db = get_db_session()
    try:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            print(f"Error: Customer with ID {customer_id} not found")
            return
        
        keys = db.query(APIKey).filter(APIKey.customer_id == customer_id).order_by(APIKey.created_at.desc()).all()
        if not keys:
            print(f"No API keys found for {customer.name}")
            return
        
        print(f"\nAPI Keys for {customer.name} (ID: {customer_id}):")
        print(f"{'ID':<5} {'Created':<20} {'Expires':<20} {'Active':<10}")
        print("-" * 60)
        for key in keys:
            expires_str = key.expires_at.strftime("%Y-%m-%d") if key.expires_at else "Never"
            active_str = "Yes" if key.active else "No"
            print(f"{key.id:<5} {key.created_at.strftime('%Y-%m-%d %H:%M'):<20} {expires_str:<20} {active_str:<10}")
        print()
    except Exception as e:
        print(f"Error listing keys: {e}")
    finally:
        db.close()


def usage_report(customer_id: int, start_date: Optional[str] = None, end_date: Optional[str] = None):
    """View usage report for a customer."""
    db = get_db_session()
    try:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            print(f"Error: Customer with ID {customer_id} not found")
            return
        
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        
        summary = get_usage_summary(customer_id, db, start_dt, end_dt)
        
        print(f"\nUsage Report for {customer.name} (ID: {customer_id})")
        if start_dt:
            print(f"Start Date: {start_dt.strftime('%Y-%m-%d')}")
        if end_dt:
            print(f"End Date: {end_dt.strftime('%Y-%m-%d')}")
        print("-" * 60)
        print(f"Total Requests: {summary['total_requests']}")
        print(f"Total Cost: ${summary['total_cost']:.2f}")
        
        if summary['model_breakdown']:
            print("\nBreakdown by Model:")
            print(f"{'Model':<30} {'Requests':<15} {'Cost':<15}")
            print("-" * 60)
            for model, stats in summary['model_breakdown'].items():
                print(f"{model:<30} {stats['requests']:<15} ${stats['cost']:.2f}")
        print()
    except Exception as e:
        print(f"Error generating usage report: {e}")
    finally:
        db.close()


def check_budget_status(customer_id: int):
    """Check budget status for a customer."""
    db = get_db_session()
    try:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            print(f"Error: Customer with ID {customer_id} not found")
            return
        
        within_budget, spending, budget_limit = check_budget(customer_id, db)
        
        print(f"\nBudget Status for {customer.name} (ID: {customer_id})")
        print("-" * 60)
        if budget_limit:
            print(f"Monthly Budget: ${budget_limit:.2f}")
            print(f"Current Spending (30 days): ${spending:.2f}")
            print(f"Remaining: ${budget_limit - spending:.2f}")
            print(f"Status: {'✓ Within Budget' if within_budget else '✗ Budget Exceeded'}")
        else:
            print(f"No budget set")
            print(f"Current Spending (30 days): ${spending:.2f}")
        print()
    except Exception as e:
        print(f"Error checking budget: {e}")
    finally:
        db.close()


def export_usage(customer_id: int, format_type: str = "csv", start_date: Optional[str] = None, end_date: Optional[str] = None):
    """Export usage data for a customer."""
    db = get_db_session()
    try:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            print(f"Error: Customer with ID {customer_id} not found")
            return
        
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        
        query = db.query(UsageLog).filter(UsageLog.customer_id == customer_id)
        if start_dt:
            query = query.filter(UsageLog.timestamp >= start_dt)
        if end_dt:
            query = query.filter(UsageLog.timestamp <= end_dt)
        
        logs = query.order_by(UsageLog.timestamp).all()
        
        filename = f"usage_{customer_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format_type}"
        
        if format_type == "csv":
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Timestamp', 'Endpoint', 'Model', 'Cost', 'Request Count'])
                for log in logs:
                    writer.writerow([
                        log.timestamp.isoformat(),
                        log.endpoint,
                        log.model or '',
                        log.cost,
                        log.request_count
                    ])
        elif format_type == "json":
            data = {
                "customer_id": customer_id,
                "customer_name": customer.name,
                "start_date": start_dt.isoformat() if start_dt else None,
                "end_date": end_dt.isoformat() if end_dt else None,
                "records": [
                    {
                        "timestamp": log.timestamp.isoformat(),
                        "endpoint": log.endpoint,
                        "model": log.model,
                        "cost": log.cost,
                        "request_count": log.request_count
                    }
                    for log in logs
                ]
            }
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
        else:
            print(f"Error: Unsupported format {format_type}")
            return
        
        print(f"✓ Exported usage data to {filename}")
        print(f"  Records: {len(logs)}")
    except Exception as e:
        print(f"Error exporting usage: {e}")
    finally:
        db.close()


def set_pricing(model_name: str, per_request_cost: float, per_model_cost: float):
    """Set pricing for a model."""
    db = get_db_session()
    try:
        pricing = db.query(PricingConfig).filter(PricingConfig.model_name == model_name).first()
        
        if pricing:
            pricing.per_request_cost = per_request_cost
            pricing.per_model_cost = per_model_cost
            pricing.updated_at = datetime.utcnow()
            print(f"✓ Updated pricing for {model_name}")
        else:
            pricing = PricingConfig(
                model_name=model_name,
                per_request_cost=per_request_cost,
                per_model_cost=per_model_cost,
                active=True
            )
            db.add(pricing)
            print(f"✓ Created pricing for {model_name}")
        
        db.commit()
        print(f"  Per Request: ${per_request_cost:.4f}")
        print(f"  Per Model: ${per_model_cost:.4f}")
    except Exception as e:
        db.rollback()
        print(f"Error setting pricing: {e}")
    finally:
        db.close()


def list_models():
    """List available models from Ollama."""
    import httpx
    import asyncio
    
    async def get_models():
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get("http://localhost:11434/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    models = data.get("models", [])
                    if models:
                        print("\nAvailable Models:")
                        print(f"{'Name':<40} {'Size':<20} {'Modified':<20}")
                        print("-" * 80)
                        for model in models:
                            name = model.get("name", "")
                            size = model.get("size", 0)
                            modified = model.get("modified_at", "")
                            size_str = f"{size / 1e9:.2f} GB" if size else "Unknown"
                            print(f"{name:<40} {size_str:<20} {modified[:19] if modified else 'Unknown':<20}")
                        print()
                    else:
                        print("No models found. Use 'ollama pull <model>' to download models.")
                else:
                    print("Error: Could not connect to Ollama. Is it running?")
        except Exception as e:
            print(f"Error listing models: {e}")
            print("Make sure Ollama is running on localhost:11434")
    
    asyncio.run(get_models())


def main():
    parser = argparse.ArgumentParser(description="Ollama API Gateway Management CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Create customer
    parser_create = subparsers.add_parser("create-customer", help="Create a new customer")
    parser_create.add_argument("name", help="Customer name")
    parser_create.add_argument("email", help="Customer email")
    parser_create.add_argument("--budget", type=float, help="Monthly budget in dollars")
    
    # Generate key
    parser_key = subparsers.add_parser("generate-key", help="Generate API key for customer")
    parser_key.add_argument("customer_id", type=int, help="Customer ID")
    
    # Revoke key
    parser_revoke = subparsers.add_parser("revoke-key", help="Revoke an API key")
    parser_revoke.add_argument("key_id", type=int, help="API Key ID")
    
    # List customers
    subparsers.add_parser("list-customers", help="List all customers")
    
    # List keys
    parser_keys = subparsers.add_parser("list-keys", help="List API keys for customer")
    parser_keys.add_argument("customer_id", type=int, help="Customer ID")
    
    # Usage report
    parser_usage = subparsers.add_parser("usage-report", help="View usage report")
    parser_usage.add_argument("customer_id", type=int, help="Customer ID")
    parser_usage.add_argument("--start-date", help="Start date (ISO format)")
    parser_usage.add_argument("--end-date", help="End date (ISO format)")
    
    # Check budget
    parser_budget = subparsers.add_parser("check-budget", help="Check budget status")
    parser_budget.add_argument("customer_id", type=int, help="Customer ID")
    
    # Export usage
    parser_export = subparsers.add_parser("export-usage", help="Export usage data")
    parser_export.add_argument("customer_id", type=int, help="Customer ID")
    parser_export.add_argument("--format", choices=["csv", "json"], default="csv", help="Export format")
    parser_export.add_argument("--start-date", help="Start date (ISO format)")
    parser_export.add_argument("--end-date", help="End date (ISO format)")
    
    # Set pricing
    parser_pricing = subparsers.add_parser("set-pricing", help="Set pricing for a model")
    parser_pricing.add_argument("model", help="Model name")
    parser_pricing.add_argument("per_request", type=float, help="Cost per request")
    parser_pricing.add_argument("per_model", type=float, help="Cost per model")
    
    # List models
    subparsers.add_parser("list-models", help="List available Ollama models")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == "create-customer":
        create_customer(args.name, args.email, args.budget)
    elif args.command == "generate-key":
        generate_key(args.customer_id)
    elif args.command == "revoke-key":
        revoke_key(args.key_id)
    elif args.command == "list-customers":
        list_customers()
    elif args.command == "list-keys":
        list_keys(args.customer_id)
    elif args.command == "usage-report":
        usage_report(args.customer_id, args.start_date, args.end_date)
    elif args.command == "check-budget":
        check_budget_status(args.customer_id)
    elif args.command == "export-usage":
        export_usage(args.customer_id, args.format, args.start_date, args.end_date)
    elif args.command == "set-pricing":
        set_pricing(args.model, args.per_request, args.per_model)
    elif args.command == "list-models":
        list_models()


if __name__ == "__main__":
    main()

