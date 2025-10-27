"""
Daily API limits service
"""

from models import db, UserPlan, DailyUsage
from datetime import datetime

def get_or_create_user_plan(company_id):
    """Get or create a user plan for a company"""
    plan = UserPlan.query.filter_by(company_id=company_id).first()
    if not plan:
        plan = UserPlan(company_id=company_id, plan_name='free', daily_limit=100)
        db.session.add(plan)
        db.session.commit()
    return plan

def get_daily_usage(company_id, usage_date=None):
    """Get daily usage for a company on a specific date"""
    if usage_date is None:
        usage_date = datetime.now().date()
    
    usage = DailyUsage.query.filter_by(company_id=company_id, usage_date=usage_date).first()
    if not usage:
        usage = DailyUsage(company_id=company_id, usage_date=usage_date, call_count=0)
        db.session.add(usage)
        db.session.commit()
    return usage

def check_daily_limit(company_id):
    """Check if company has exceeded daily limit"""
    plan = get_or_create_user_plan(company_id)
    usage = get_daily_usage(company_id)
    
    return usage.call_count < plan.daily_limit, usage.call_count, plan.daily_limit

def increment_daily_usage(company_id):
    """Increment daily usage count for a company"""
    usage = get_daily_usage(company_id)
    usage.call_count += 1
    usage.last_reset = datetime.utcnow()
    db.session.commit()
    return usage.call_count

def reset_daily_usage_if_needed(company_id):
    """Reset daily usage if it's a new day"""
    today = datetime.now().date()
    usage = DailyUsage.query.filter_by(company_id=company_id, usage_date=today).first()
    
    if not usage:
        # Check if there's usage from previous days and reset
        old_usage = DailyUsage.query.filter_by(company_id=company_id).order_by(DailyUsage.usage_date.desc()).first()
        if old_usage and old_usage.usage_date < today:
            # Create new usage record for today
            usage = DailyUsage(company_id=company_id, usage_date=today, call_count=0)
            db.session.add(usage)
            db.session.commit()
    
    return usage

def get_usage_status(company_id):
    """Get current usage status for a company"""
    reset_daily_usage_if_needed(company_id)
    can_proceed, current_usage, daily_limit = check_daily_limit(company_id)
    plan = get_or_create_user_plan(company_id)
    
    return {
        'company_id': company_id,
        'plan_name': plan.plan_name,
        'daily_limit': daily_limit,
        'current_usage': current_usage,
        'remaining_calls': daily_limit - current_usage,
        'can_proceed': can_proceed,
        'reset_time': 'midnight'
    }

def update_user_plan(company_id, plan_name='free', daily_limit=100):
    """Update user plan for a company"""
    plan = get_or_create_user_plan(company_id)
    plan.plan_name = plan_name
    plan.daily_limit = daily_limit
    plan.updated_date = datetime.utcnow()
    db.session.commit()
    
    return {
        'success': True,
        'message': f'Plan updated for company {company_id}',
        'plan_name': plan_name,
        'daily_limit': daily_limit
    }
