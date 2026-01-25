"""
Database Setup Script
Initializes LanceDB and seeds with fraud patterns
"""

import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from backend.database import get_db

def setup_database():
    """Initialize database and create tables"""
    
    print("="*60)
    print("FinGuard Database Setup")
    print("="*60)
    
    print("\nInitializing LanceDB...")
    
    try:
        # This will create tables and seed fraud patterns
        db = get_db()
        
        print("\nDatabase setup complete!")
        print("\nDatabase location: ./data/lancedb")
        print("\nTables created:")
        print("  - transactions (for storing transaction vectors)")
        print("  - fraud_patterns (seeded with 5 known fraud patterns)")
        
        # Get stats
        stats = db.get_statistics()
        print(f"\nCurrent state:")
        print(f"  - Transactions: {stats['total_transactions']}")
        print(f"  - Fraud patterns: 5 (seeded)")
        
        print("\n" + "="*60)
        print("Setup successful! You can now:")
        print("  1. Run: python main.py --sample")
        print("  2. Run: streamlit run dashboard/app.py")
        print("="*60)
        
    except Exception as e:
        print(f"\nError during setup: {e}")
        print("\nPlease ensure:")
        print("  - You have installed all requirements: pip install -r requirements.txt")
        print("  - The data/lancedb directory is writable")
        return False
    
    return True

if __name__ == "__main__":
    success = setup_database()
    sys.exit(0 if success else 1)
