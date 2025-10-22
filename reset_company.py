"""
Reset company 134 (or any company) by clearing its assistant and thread
This will force the app to recreate everything fresh on next request
"""
import sqlite3
import sys

def reset_company(company_id):
    """Reset a company's assistant and thread"""
    conn = sqlite3.connect('app/instance/data.sqlite')
    cursor = conn.cursor()
    
    # Check if company exists
    cursor.execute("SELECT company_id, assistant_id, file_id, thread_id FROM openai_creds WHERE company_id = ?", (company_id,))
    record = cursor.fetchone()
    
    if not record:
        print(f"✗ No record found for company {company_id}")
        conn.close()
        return False
    
    print(f"Found record for company {company_id}:")
    print(f"  Assistant ID: {record[1]}")
    print(f"  File ID: {record[2]}")
    print(f"  Thread ID: {record[3]}")
    print()
    
    # Clear assistant_id and thread_id (keep file_id as it's still valid)
    cursor.execute("""
        UPDATE openai_creds 
        SET assistant_id = NULL, thread_id = NULL 
        WHERE company_id = ?
    """, (company_id,))
    
    conn.commit()
    conn.close()
    
    print(f"✓ Reset complete for company {company_id}")
    print(f"  Assistant ID: CLEARED (will be recreated)")
    print(f"  Thread ID: CLEARED (will be recreated)")
    print(f"  File ID: KEPT (still valid)")
    print()
    print("Next time you send a message for this company, a fresh assistant and thread will be created.")
    
    return True

if __name__ == "__main__":
    company_id = sys.argv[1] if len(sys.argv) > 1 else "134"
    
    print("="*80)
    print(f"RESETTING COMPANY {company_id}")
    print("="*80)
    print()
    
    reset_company(company_id)

