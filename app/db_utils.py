"""
Database utility functions
"""

import os
import pymysql
from models import db, OpenAICreds, UserPlan, DailyUsage
from datetime import datetime

# MySQL configuration
mysql_config = {
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('HOST'),
    'database': os.getenv('DB_NAME')
}

def get_mysql_connection():
    """Get MySQL database connection"""
    return pymysql.connect(
        user=mysql_config['user'],
        password=mysql_config['password'],
        host=mysql_config['host'],
        database=mysql_config['database']
    )

def check_and_create_table(table_name):
    """Check if table exists and create if it doesn't"""
    inspector = db.inspect(db.engine)
    if not inspector.has_table(table_name):
        db.create_all()

def initialize_database():
    """Initialize all database tables"""
    check_and_create_table(OpenAICreds.__tablename__)
    check_and_create_table(UserPlan.__tablename__)
    check_and_create_table(DailyUsage.__tablename__)

def fetch_reviews_for_company(conn, company_id):
    """Fetch all reviews for a company and format them for vector store"""
    with conn.cursor() as cursor:
        # Get company name
        cursor.execute("SELECT location_title FROM tbl_location WHERE location_id = %s", (company_id,))
        company_result = cursor.fetchone()
        if not company_result:
            return None, None
        
        company_name = company_result[0]
        
        # Get all reviews for the company
        cursor.execute("""
            SELECT displayName, starRating_number, comment, createTime, reviewId
            FROM tbl_location_review 
            WHERE location_id = %s AND (is_deleted = 0 OR is_deleted IS NULL)
            ORDER BY createTime DESC
        """, (company_id,))
        
        reviews = cursor.fetchall()
        return company_name, reviews
