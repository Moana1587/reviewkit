"""
Cleanup script for GPT resources
This script removes all OpenAI threads, assistants, files, and database records
"""

import os
import sys
from dotenv import load_dotenv

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Load environment variables
load_dotenv()

from app.app import app
from app.openai_service import OpenAIService

def cleanup_all():
    """Clean up all GPT resources for all companies"""
    print("\n" + "="*60)
    print("GPT RESOURCES CLEANUP - ALL COMPANIES")
    print("="*60)
    print("\nThis will delete:")
    print("  • All OpenAI threads (conversation history)")
    print("  • All OpenAI assistants")
    print("  • All uploaded files to OpenAI")
    print("  • All database records in openai_creds table")
    print("\n⚠️  WARNING: This action cannot be undone!")
    print("="*60 + "\n")
    
    confirm = input("Are you sure you want to proceed? (type 'yes' to confirm): ")
    
    if confirm.lower() != 'yes':
        print("\n❌ Cleanup cancelled.")
        return
    
    with app.app_context():
        service = OpenAIService()
        print("\n🧹 Starting cleanup process...\n")
        report = service.cleanup_all_gpt_resources()
        
        if "error" in report:
            print(f"\n❌ Error: {report['error']}")
        else:
            print("\n✅ Cleanup completed!")

def cleanup_company(company_id):
    """Clean up GPT resources for a specific company"""
    print("\n" + "="*60)
    print(f"GPT RESOURCES CLEANUP - COMPANY: {company_id}")
    print("="*60)
    print(f"\nThis will delete for company '{company_id}':")
    print("  • OpenAI thread (conversation history)")
    print("  • OpenAI assistant")
    print("  • Uploaded file to OpenAI")
    print("  • Database record in openai_creds table")
    print("\n⚠️  WARNING: This action cannot be undone!")
    print("="*60 + "\n")
    
    confirm = input("Are you sure you want to proceed? (type 'yes' to confirm): ")
    
    if confirm.lower() != 'yes':
        print("\n❌ Cleanup cancelled.")
        return
    
    with app.app_context():
        service = OpenAIService()
        print("\n🧹 Starting cleanup process...\n")
        report = service.cleanup_company_gpt_resources(company_id)
        
        print("\n" + "="*50)
        print("CLEANUP SUMMARY")
        print("="*50)
        print(f"Company ID: {report['company_id']}")
        print(f"Thread deleted: {'✓' if report['thread_deleted'] else '✗'}")
        print(f"Assistant deleted: {'✓' if report['assistant_deleted'] else '✗'}")
        print(f"File deleted: {'✓' if report['file_deleted'] else '✗'}")
        print(f"DB record cleaned: {'✓' if report['db_record_cleaned'] else '✗'}")
        
        if report['errors']:
            print(f"\nErrors encountered: {len(report['errors'])}")
            for error in report['errors']:
                print(f"  - {error}")
        else:
            print("\n✅ Cleanup completed successfully!")
        print("="*50)

def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("\nUsage:")
        print("  python cleanup_gpt.py all              # Clean up all companies")
        print("  python cleanup_gpt.py <company_id>     # Clean up specific company")
        print("\nExamples:")
        print("  python cleanup_gpt.py all")
        print("  python cleanup_gpt.py 127")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command.lower() == 'all':
        cleanup_all()
    else:
        cleanup_company(command)

if __name__ == "__main__":
    main()

