"""
Usage tracking and cost calculation.
"""
from sqlalchemy.orm import Session
from database import UsageLog, PricingConfig, Customer
from datetime import datetime, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def calculate_cost(model: Optional[str], endpoint: str, db: Session) -> float:
    """
    Calculate cost for a request based on pricing configuration.
    
    Returns: cost in dollars
    """
    cost = 0.0
    
    # Get pricing config for the model
    if model:
        pricing = db.query(PricingConfig).filter(
            PricingConfig.model_name == model,
            PricingConfig.active == True
        ).first()
        
        if pricing:
            cost += pricing.per_request_cost
            cost += pricing.per_model_cost
        else:
            # Default pricing if model not configured
            cost = 0.01  # Default $0.01 per request
    
    return cost


def log_usage(
    customer_id: int,
    api_key_id: int,
    endpoint: str,
    model: Optional[str],
    cost: float,
    db: Session,
    metadata: Optional[str] = None
) -> UsageLog:
    """Log a usage event."""
    usage_log = UsageLog(
        customer_id=customer_id,
        api_key_id=api_key_id,
        endpoint=endpoint,
        model=model,
        request_count=1,
        cost=cost,
        timestamp=datetime.utcnow(),
        extra_data=metadata
    )
    db.add(usage_log)
    db.commit()
    db.refresh(usage_log)
    return usage_log


def check_budget(customer_id: int, db: Session, period_days: int = 30) -> tuple[bool, float, Optional[float]]:
    """
    Check if customer is within budget.
    
    Returns: (within_budget, current_spending, budget_limit)
    """
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        return False, 0.0, None
    
    # Calculate spending for the period
    start_date = datetime.utcnow() - timedelta(days=period_days)
    total_spending = db.query(
        db.func.sum(UsageLog.cost)
    ).filter(
        UsageLog.customer_id == customer_id,
        UsageLog.timestamp >= start_date
    ).scalar() or 0.0
    
    # Check against budget
    if customer.monthly_budget:
        within_budget = total_spending < customer.monthly_budget
        return within_budget, total_spending, customer.monthly_budget
    
    return True, total_spending, None


def get_usage_summary(
    customer_id: int,
    db: Session,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> dict:
    """Get usage summary for a customer."""
    query = db.query(UsageLog).filter(UsageLog.customer_id == customer_id)
    
    if start_date:
        query = query.filter(UsageLog.timestamp >= start_date)
    if end_date:
        query = query.filter(UsageLog.timestamp <= end_date)
    
    logs = query.all()
    
    total_requests = len(logs)
    total_cost = sum(log.cost for log in logs)
    
    # Group by model
    model_usage = {}
    for log in logs:
        model = log.model or "unknown"
        if model not in model_usage:
            model_usage[model] = {"requests": 0, "cost": 0.0}
        model_usage[model]["requests"] += 1
        model_usage[model]["cost"] += log.cost
    
    return {
        "total_requests": total_requests,
        "total_cost": total_cost,
        "model_breakdown": model_usage,
        "start_date": start_date.isoformat() if start_date else None,
        "end_date": end_date.isoformat() if end_date else None
    }

