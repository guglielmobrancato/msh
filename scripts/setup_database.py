"""
Database Setup Script
Initialize PostgreSQL database with all required tables.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.database import init_database, drop_all_tables, get_db
from config import settings


def main():
    """Initialize the database."""
    print("\n" + "="*60)
    print("🛡️  DATABASE SETUP - ANCILE AI")
    print("="*60 + "\n")
    
    print(f"Environment: {settings.environment}")
    print(f"Database URL: {settings.database_url.split('@')[0]}@***")
    
    # Confirm in production
    if settings.environment == "production":
        response = input("\n⚠️  Running in PRODUCTION mode. Continue? (yes/no): ")
        if response.lower() != "yes":
            print("Aborted.")
            return
    
    # Ask if user wants to drop existing tables
    response = input("\n⚠️  Drop existing tables? This will DELETE all data! (yes/no): ")
    if response.lower() == "yes":
        if settings.environment == "production":
            confirm = input("⚠️⚠️⚠️  CONFIRM: Delete production data? Type 'DELETE' to confirm: ")
            if confirm != "DELETE":
                print("Aborted.")
                return
        
        drop_all_tables()
    
    # Create tables
    init_database()
    
    # Test connection
    print("\n🔍 Testing database connection...")
    try:
        with get_db() as db:
            # Try a simple query
            from models.schemas import Article
            count = db.query(Article).count()
            print(f"✅ Connection successful. Articles in database: {count}")
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return
    
    print("\n" + "="*60)
    print("✅ DATABASE SETUP COMPLETE")
    print("="*60 + "\n")
    
    print("Next steps:")
    print("1. Configure your .env file with API keys")
    print("2. Run a test pipeline: python scripts/run_pipeline.py --dry-run")
    print("3. Set up cron job for automated execution\n")


if __name__ == "__main__":
    main()
