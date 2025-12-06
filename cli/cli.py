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
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from api_gateway.database import get_db_session_sync, Customer, APIKey, UsageLog, PricingConfig, ModelMetadata, DeviceRegistration
from api_gateway.auth import hash_api_key
from api_gateway.usage import get_usage_summary, check_budget


def generate_api_key() -> str:
    """Generate a secure API key."""
    return f"sk_{secrets.token_urlsafe(32)}"


def create_customer(name: str, email: str, monthly_budget: Optional[float] = None):
    """Create a new customer."""
    db = get_db_session_sync()
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


def send_email_via_gmail(to_email: str, subject: str, body_plain: str, body_html: Optional[str] = None, gmail_user: str = None, gmail_password: str = None) -> bool:
    """Send email via Gmail SMTP."""
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = gmail_user
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Add plain text version
        msg.attach(MIMEText(body_plain, 'plain'))
        
        # Add HTML version if provided
        if body_html:
            msg.attach(MIMEText(body_html, 'html'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(gmail_user, gmail_password)
        text = msg.as_string()
        server.sendmail(gmail_user, to_email, text)
        server.quit()
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def generate_key(customer_id: int, send_email: bool = False, gmail_user: Optional[str] = None, gmail_password: Optional[str] = None):
    """Generate an API key for a customer."""
    db = get_db_session_sync()
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
        
        # Send email if requested
        if send_email:
            if not gmail_user or not gmail_password:
                print("  ⚠️  Gmail credentials not provided. Skipping email.")
            else:
                subject = "Your API Key for Bet Assistant"
                
                # Plain text version
                body_plain = f"""Hello {customer.name},

Your API key has been generated successfully.

API Key: {api_key}
Key ID: {db_key.id}

You can use this key to access the Bet Assistant API at:
https://bet.laserpointlabs.com

Important: Keep this key secure and do not share it with anyone.

If you did not request this key, please contact support immediately.

Best regards,
Bet Assistant Team
"""
                
                # HTML version with mobile-friendly copy button
                body_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 15px;
        }}
        .api-key-container {{
            margin: 25px 0;
        }}
        .api-key-box {{
            background-color: #f8f9fa;
            border: 3px solid #007bff;
            border-radius: 12px;
            padding: 25px 15px;
            margin: 15px 0;
            text-align: center;
            -webkit-tap-highlight-color: rgba(0, 123, 255, 0.3);
        }}
        .api-key-label {{
            font-size: 11px;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            margin-bottom: 15px;
            font-weight: 600;
        }}
        .api-key-value {{
            font-family: 'Courier New', 'Monaco', monospace;
            font-size: 26px;
            font-weight: bold;
            color: #fff;
            letter-spacing: 1px;
            word-break: break-all;
            padding: 40px 25px;
            background-color: #007bff;
            border-radius: 15px;
            border: none;
            margin: 20px 0;
            text-align: center;
            min-height: 120px;
            display: block;
            -webkit-user-select: all;
            -moz-user-select: all;
            -ms-user-select: all;
            user-select: all;
            -webkit-tap-highlight-color: rgba(255, 255, 255, 0.5);
            box-shadow: 0 6px 12px rgba(0, 123, 255, 0.3);
            line-height: 1.4;
        }}
        .api-key-value:active {{
            background-color: #0056b3;
        }}
        .copy-button-link {{
            display: block;
            text-decoration: none;
            margin: 20px 0;
        }}
        .copy-button-large {{
            background-color: #28a745;
            color: white;
            padding: 25px 30px;
            border-radius: 12px;
            font-size: 22px;
            font-weight: bold;
            text-align: center;
            box-shadow: 0 4px 12px rgba(40, 167, 69, 0.3);
            -webkit-tap-highlight-color: rgba(40, 167, 69, 0.5);
            transition: all 0.2s;
        }}
        .copy-button-large:active {{
            background-color: #218838;
            transform: scale(0.98);
        }}
        .copy-hint {{
            font-size: 16px;
            color: #666;
            margin-top: 15px;
            font-weight: 500;
        }}
        .info-box {{
            background-color: #e8f4f8;
            border-left: 4px solid #2196F3;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .warning-box {{
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        a {{
            color: #2196F3;
            text-decoration: none;
        }}
        @media only screen and (max-width: 600px) {{
            body {{
                padding: 10px;
            }}
            .api-key-value {{
                font-size: 24px;
                padding: 45px 25px;
                min-height: 140px;
            }}
            .copy-hint {{
                font-size: 22px;
                margin-top: 25px;
            }}
        }}
    </style>
</head>
<body>
    <h2>Hello {customer.name},</h2>
    
    <p>Your API key has been generated successfully.</p>
    
    <div class="api-key-container">
        <div class="api-key-box">
            <div class="api-key-label">Your API Key</div>
            <a href="https://bet.laserpointlabs.com?key={api_key}" class="copy-button-link">
                <div class="copy-button-large">📋 Tap Here to Get Your API Key</div>
            </a>
            <div class="api-key-value">{api_key}</div>
        </div>
    </div>
    
    <div class="info-box">
        <strong>Key ID:</strong> {db_key.id}<br>
        <strong>Access URL:</strong> <a href="https://bet.laserpointlabs.com">https://bet.laserpointlabs.com</a>
    </div>
    
    <div class="warning-box">
        <strong>⚠️ Security Reminder:</strong><br>
        Keep this key secure and do not share it with anyone. If you did not request this key, please contact support immediately.
    </div>
    
    <p>Best regards,<br>
    <strong>Bet Assistant Team</strong></p>
</body>
</html>
"""
                
                if send_email_via_gmail(customer.email, subject, body_plain, body_html, gmail_user, gmail_password):
                    print(f"  ✓ API key sent via email to {customer.email}")
                else:
                    print(f"  ✗ Failed to send email. API key displayed above.")
        
        print(f"  ⚠️  Save this key securely - it will not be shown again!")
    except Exception as e:
        db.rollback()
        print(f"Error generating key: {e}")
    finally:
        db.close()


def revoke_key(key_id: int):
    """Revoke an API key."""
    db = get_db_session_sync()
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


def update_customer(customer_id: int, name: Optional[str] = None, email: Optional[str] = None, 
                    monthly_budget: Optional[float] = None, active: Optional[bool] = None):
    """Update a customer's information."""
    db = get_db_session_sync()
    try:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            print(f"Error: Customer with ID {customer_id} not found")
            return
        
        updated = False
        
        if name is not None:
            customer.name = name
            updated = True
            print(f"✓ Updated name: {name}")
        
        if email is not None:
            # Check if email already exists for another customer
            existing = db.query(Customer).filter(
                Customer.email == email,
                Customer.id != customer_id
            ).first()
            if existing:
                print(f"Error: Email {email} is already in use by another customer")
                return
            customer.email = email
            updated = True
            print(f"✓ Updated email: {email}")
        
        if monthly_budget is not None:
            customer.monthly_budget = monthly_budget
            updated = True
            print(f"✓ Updated monthly budget: ${monthly_budget:.2f}")
        
        if active is not None:
            customer.active = active
            updated = True
            status = "activated" if active else "deactivated"
            print(f"✓ Customer {status}")
        
        if updated:
            db.commit()
            print(f"\n✓ Customer updated successfully")
            print(f"  ID: {customer.id}")
            print(f"  Name: {customer.name}")
            print(f"  Email: {customer.email}")
            if customer.monthly_budget:
                print(f"  Monthly Budget: ${customer.monthly_budget:.2f}")
            print(f"  Active: {'Yes' if customer.active else 'No'}")
        else:
            print("No changes specified. Use --name, --email, --budget, or --active to update.")
    except Exception as e:
        db.rollback()
        print(f"Error updating customer: {e}")
    finally:
        db.close()


def delete_customer(customer_id: int, force: bool = False):
    """Delete a customer and all associated data."""
    db = get_db_session_sync()
    try:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            print(f"Error: Customer with ID {customer_id} not found")
            return
        
        # Count associated data
        key_count = db.query(APIKey).filter(APIKey.customer_id == customer_id).count()
        usage_count = db.query(UsageLog).filter(UsageLog.customer_id == customer_id).count()
        
        if not force:
            print(f"\n⚠️  Warning: This will delete:")
            print(f"  Customer: {customer.name} (ID: {customer_id})")
            print(f"  API Keys: {key_count}")
            print(f"  Usage Logs: {usage_count}")
            print(f"\nThis action cannot be undone!")
            response = input("Type 'DELETE' to confirm: ")
            if response != "DELETE":
                print("Deletion cancelled")
                return
        
        # Delete usage logs first (they have foreign key constraints)
        db.query(UsageLog).filter(UsageLog.customer_id == customer_id).delete()
        
        # Delete customer (cascade will handle API keys)
        db.delete(customer)
        db.commit()
        
        print(f"✓ Deleted customer {customer.name} (ID: {customer_id})")
        print(f"  Removed {key_count} API key(s)")
        print(f"  Removed {usage_count} usage log(s)")
    except Exception as e:
        db.rollback()
        print(f"Error deleting customer: {e}")
    finally:
        db.close()


def refresh_key(key_id: int):
    """Refresh an API key by revoking the old one and generating a new one."""
    db = get_db_session_sync()
    try:
        old_key = db.query(APIKey).filter(APIKey.id == key_id).first()
        if not old_key:
            print(f"Error: API key with ID {key_id} not found")
            return
        
        customer = db.query(Customer).filter(Customer.id == old_key.customer_id).first()
        if not customer:
            print(f"Error: Customer not found for API key {key_id}")
            return
        
        # Revoke old key
        old_key.active = False
        db.commit()
        
        # Generate new key
        api_key = generate_api_key()
        key_hash = hash_api_key(api_key)
        
        new_key = APIKey(
            customer_id=customer.id,
            key_hash=key_hash,
            active=True
        )
        db.add(new_key)
        db.commit()
        db.refresh(new_key)
        
        print(f"✓ Refreshed API key for {customer.name} (ID: {customer.id})")
        print(f"  Old Key ID: {key_id} (revoked)")
        print(f"  New Key ID: {new_key.id}")
        print(f"  New API Key: {api_key}")
        print(f"  ⚠️  Save this key securely - it will not be shown again!")
    except Exception as e:
        db.rollback()
        print(f"Error refreshing key: {e}")
    finally:
        db.close()


def list_customers():
    """List all customers."""
    db = get_db_session_sync()
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
    db = get_db_session_sync()
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
    db = get_db_session_sync()
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
    db = get_db_session_sync()
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
    db = get_db_session_sync()
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
    db = get_db_session_sync()
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


def sync_models():
    """Sync available models from Ollama to database."""
    import httpx
    import asyncio
    
    async def sync():
        db = get_db_session_sync()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get("http://localhost:11434/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    models = data.get("models", [])
                    
                    if not models:
                        print("No models found in Ollama.")
                        return
                    
                    synced_count = 0
                    for model in models:
                        model_name = model.get("name", "")
                        if not model_name:
                            continue
                        
                        # Check if model metadata already exists
                        existing = db.query(ModelMetadata).filter(
                            ModelMetadata.model_name == model_name
                        ).first()
                        
                        if not existing:
                            # Create new metadata entry
                            metadata = ModelMetadata(
                                model_name=model_name,
                                description=f"Ollama model: {model_name}",
                                context_window=None  # Can be updated later
                            )
                            db.add(metadata)
                            synced_count += 1
                    
                    db.commit()
                    print(f"✓ Synced {synced_count} new model(s) to database")
                    print(f"  Total models in database: {len(models)}")
                else:
                    print("Error: Could not connect to Ollama. Is it running?")
        except Exception as e:
            db.rollback()
            print(f"Error syncing models: {e}")
            print("Make sure Ollama is running on localhost:11434")
        finally:
            db.close()
    
    asyncio.run(sync())


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


def list_devices(customer_id: Optional[int] = None):
    """List registered devices, optionally filtered by customer."""
    db = get_db_session_sync()
    try:
        query = db.query(DeviceRegistration).join(APIKey).join(Customer)
        
        if customer_id:
            query = query.filter(Customer.id == customer_id)
        
        devices = query.all()
        
        if not devices:
            print("No registered devices found.")
            return
        
        print(f"\n{'='*80}")
        print(f"{'ID':<5} {'Customer':<20} {'Device Name':<25} {'Type':<10} {'Active':<8} {'Last Used'}")
        print(f"{'='*80}")
        
        for device in devices:
            customer = device.api_key.customer
            last_used = device.last_used.strftime("%Y-%m-%d %H:%M") if device.last_used else "Never"
            status = "Yes" if device.active else "No"
            
            print(f"{device.id:<5} {customer.name:<20} {(device.device_name or 'Unknown'):<25} {(device.device_type or 'N/A'):<10} {status:<8} {last_used}")
        
        print(f"{'='*80}")
        print(f"Total: {len(devices)} device(s)")
        
    except Exception as e:
        print(f"Error listing devices: {e}")
    finally:
        db.close()


def revoke_device(device_id: int):
    """Revoke a device registration by ID."""
    db = get_db_session_sync()
    try:
        device = db.query(DeviceRegistration).filter(DeviceRegistration.id == device_id).first()
        
        if not device:
            print(f"Error: Device with ID {device_id} not found")
            return
        
        customer = device.api_key.customer
        device_name = device.device_name or "Unknown"
        
        device.active = False
        db.commit()
        
        print(f"✓ Revoked device '{device_name}' (ID: {device_id}) for customer {customer.name}")
        
    except Exception as e:
        db.rollback()
        print(f"Error revoking device: {e}")
    finally:
        db.close()


def delete_device(device_id: int):
    """Permanently delete a device registration."""
    db = get_db_session_sync()
    try:
        device = db.query(DeviceRegistration).filter(DeviceRegistration.id == device_id).first()
        
        if not device:
            print(f"Error: Device with ID {device_id} not found")
            return
        
        customer = device.api_key.customer
        device_name = device.device_name or "Unknown"
        
        db.delete(device)
        db.commit()
        
        print(f"✓ Deleted device '{device_name}' (ID: {device_id}) for customer {customer.name}")
        
    except Exception as e:
        db.rollback()
        print(f"Error deleting device: {e}")
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        description="Ollama API Gateway Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a customer
  python cli/cli.py create-customer "John Doe" john@example.com --budget 100.00
  
  # Update a customer
  python cli/cli.py update-customer 1 --name "Jane Doe" --budget 200.00
  
  # Delete a customer (with confirmation)
  python cli/cli.py delete-customer 1
  
  # Generate an API key
  python cli/cli.py generate-key 1
  
  # Refresh an API key (revoke old, create new)
  python cli/cli.py refresh-key 5
  
  # List all customers
  python cli/cli.py list-customers
  
  # View usage report
  python cli/cli.py usage-report 1 --start-date 2024-01-01 --end-date 2024-01-31
        """
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute", metavar="COMMAND")
    
    # Create customer
    parser_create = subparsers.add_parser("create-customer", help="Create a new customer")
    parser_create.add_argument("name", help="Customer name")
    parser_create.add_argument("email", help="Customer email")
    parser_create.add_argument("--budget", type=float, help="Monthly budget in dollars")
    
    # Update customer
    parser_update = subparsers.add_parser("update-customer", help="Update customer information")
    parser_update.add_argument("customer_id", type=int, help="Customer ID")
    parser_update.add_argument("--name", help="New customer name")
    parser_update.add_argument("--email", help="New customer email")
    parser_update.add_argument("--budget", type=float, help="New monthly budget in dollars")
    parser_update.add_argument("--active", type=lambda x: x.lower() == 'true', help="Set active status (true/false)")
    
    # Delete customer
    parser_delete = subparsers.add_parser("delete-customer", help="Delete a customer and all associated data")
    parser_delete.add_argument("customer_id", type=int, help="Customer ID")
    parser_delete.add_argument("--force", action="store_true", help="Skip confirmation prompt")
    
    # Generate key
    parser_key = subparsers.add_parser("generate-key", help="Generate a new API key for customer")
    parser_key.add_argument("customer_id", type=int, help="Customer ID")
    parser_key.add_argument("--send-email", action="store_true", help="Send API key via email to customer")
    parser_key.add_argument("--gmail-user", help="Gmail address for sending (or set GMAIL_USER env var)")
    parser_key.add_argument("--gmail-password", help="Gmail app password (or set GMAIL_PASSWORD env var)")
    
    # Refresh key
    parser_refresh = subparsers.add_parser("refresh-key", help="Refresh an API key (revoke old, create new)")
    parser_refresh.add_argument("key_id", type=int, help="API Key ID to refresh")
    
    # Revoke key
    parser_revoke = subparsers.add_parser("revoke-key", help="Revoke an API key")
    parser_revoke.add_argument("key_id", type=int, help="API Key ID")
    
    # List customers
    subparsers.add_parser("list-customers", help="List all customers")
    
    # List keys
    parser_keys = subparsers.add_parser("list-keys", help="List API keys for a customer")
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
    
    # Sync models
    subparsers.add_parser("sync-models", help="Sync available models from Ollama to database")
    
    # Device management
    parser_devices = subparsers.add_parser("list-devices", help="List registered devices")
    parser_devices.add_argument("--customer-id", type=int, help="Filter by customer ID")
    
    parser_revoke_device = subparsers.add_parser("revoke-device", help="Revoke a device registration")
    parser_revoke_device.add_argument("device_id", type=int, help="Device ID to revoke")
    
    parser_delete_device = subparsers.add_parser("delete-device", help="Permanently delete a device registration")
    parser_delete_device.add_argument("device_id", type=int, help="Device ID to delete")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == "create-customer":
        create_customer(args.name, args.email, args.budget)
    elif args.command == "update-customer":
        update_customer(
            args.customer_id,
            name=args.name,
            email=args.email,
            monthly_budget=args.budget,
            active=args.active
        )
    elif args.command == "delete-customer":
        delete_customer(args.customer_id, force=args.force)
    elif args.command == "generate-key":
        gmail_user = args.gmail_user or os.getenv("GMAIL_USER")
        gmail_password = args.gmail_password or os.getenv("GMAIL_PASSWORD")
        generate_key(args.customer_id, send_email=args.send_email, gmail_user=gmail_user, gmail_password=gmail_password)
    elif args.command == "refresh-key":
        refresh_key(args.key_id)
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
    elif args.command == "sync-models":
        sync_models()
    elif args.command == "list-devices":
        list_devices(args.customer_id)
    elif args.command == "revoke-device":
        revoke_device(args.device_id)
    elif args.command == "delete-device":
        delete_device(args.device_id)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

