"""
Database models for ReviewKit application
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Initialize SQLAlchemy
db = SQLAlchemy()

class OpenAICreds(db.Model):
    """Model for storing OpenAI credentials and file associations"""
    __tablename__ = 'openai_creds'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.String(80), unique=True, nullable=False)
    updated_date = db.Column(db.DateTime, nullable=True)
    assistant_id = db.Column(db.String(80), nullable=True)
    file_id = db.Column(db.String(80), nullable=True)
    vector_id = db.Column(db.String(80), nullable=True)
    thread_id = db.Column(db.String(80), nullable=True)

class UserPlan(db.Model):
    """Model for storing user subscription plans and limits"""
    __tablename__ = 'user_plans'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.String(80), unique=True, nullable=False)
    plan_name = db.Column(db.String(50), nullable=False, default='free')
    daily_limit = db.Column(db.Integer, nullable=False, default=10)
    created_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_date = db.Column(db.DateTime, nullable=True)

class DailyUsage(db.Model):
    """Model for tracking daily API usage per company"""
    __tablename__ = 'daily_usage'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.String(80), nullable=False)
    usage_date = db.Column(db.Date, nullable=False)
    call_count = db.Column(db.Integer, nullable=False, default=0)
    last_reset = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Ensure one record per company per day
    __table_args__ = (db.UniqueConstraint('company_id', 'usage_date', name='unique_company_date'),)

class SemanticAnalysis(db.Model):
    """Model for storing semantic analysis results"""
    __tablename__ = 'semantic_analysis'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.String(80), nullable=False)
    company_name = db.Column(db.String(255), nullable=False)
    total_reviews = db.Column(db.Integer, nullable=False, default=0)
    analysis_data = db.Column(db.Text, nullable=False)  # JSON string with topics, sentiments, and excerpts
    created_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Ensure one record per company (latest analysis)
    __table_args__ = (db.UniqueConstraint('company_id', name='unique_company_analysis'),)