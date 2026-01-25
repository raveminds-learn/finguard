"""
LanceDB Database Manager
Handles vector storage and similarity search
"""

import lancedb
from datetime import datetime
from typing import Optional, List, Dict
import pyarrow as pa
import os

class LanceDBManager:
    """Manages all LanceDB operations"""
    
    def __init__(self, db_path="./data/lancedb"):
        """Initialize LanceDB connection"""
        self.db_path = db_path
        os.makedirs(db_path, exist_ok=True)
        self.db = lancedb.connect(db_path)
        self.setup_tables()
    
    def setup_tables(self):
        """Initialize tables if they don't exist"""
        
        # Define schema for transactions table
        transaction_schema = pa.schema([
            pa.field("transaction_id", pa.string()),
            pa.field("user_hash", pa.string()),
            pa.field("amount", pa.float64()),
            pa.field("merchant_category", pa.string()),
            pa.field("location_city", pa.string()),
            pa.field("device_type", pa.string()),
            pa.field("payment_method_type", pa.string()),
            pa.field("timestamp", pa.string()),
            pa.field("hour_of_day", pa.int64()),
            pa.field("day_of_week", pa.string()),
            pa.field("behavior_text", pa.string()),
            pa.field("vector", pa.list_(pa.float32(), 384)),  # 384-dim embeddings
            pa.field("fraud_score", pa.float64()),
            pa.field("risk_level", pa.string()),
            pa.field("is_flagged", pa.bool_()),
            pa.field("investigation_notes", pa.string()),
        ])
        
        # Fraud patterns schema
        pattern_schema = pa.schema([
            pa.field("pattern_id", pa.string()),
            pa.field("pattern_name", pa.string()),
            pa.field("pattern_description", pa.string()),
            pa.field("vector", pa.list_(pa.float32(), 384)),
            pa.field("severity", pa.string()),
            pa.field("created_at", pa.string()),
        ])
        
        # Create or open transactions table
        if "transactions" not in self.db.table_names():
            self.transactions_table = self.db.create_table(
                "transactions",
                schema=transaction_schema
            )
            print("Created 'transactions' table")
        else:
            self.transactions_table = self.db.open_table("transactions")
            print("Opened existing 'transactions' table")
        
        # Create or open fraud patterns table
        if "fraud_patterns" not in self.db.table_names():
            self.patterns_table = self.db.create_table(
                "fraud_patterns",
                schema=pattern_schema
            )
            self._seed_fraud_patterns()
            print("Created and seeded 'fraud_patterns' table")
        else:
            self.patterns_table = self.db.open_table("fraud_patterns")
            print("Opened existing 'fraud_patterns' table")
    
    def _seed_fraud_patterns(self):
        """Seed with known fraud patterns"""
        from backend.vectorization import get_embedding
        
        known_patterns = [
            {
                "pattern_id": "PATTERN_001",
                "pattern_name": "Card Testing",
                "pattern_description": "Multiple small transactions under $50 across different merchants within short time, testing stolen card validity before larger purchases",
                "severity": "High",
                "created_at": datetime.now().isoformat()
            },
            {
                "pattern_id": "PATTERN_002",
                "pattern_name": "Account Takeover",
                "pattern_description": "Sudden change in transaction behavior with new device, different location, unusual merchants, password reset followed by purchases",
                "severity": "Critical",
                "created_at": datetime.now().isoformat()
            },
            {
                "pattern_id": "PATTERN_003",
                "pattern_name": "Low-and-Slow Exfiltration",
                "pattern_description": "Small recurring transactions over weeks, barely below detection thresholds, targeting multiple accounts with coordinated timing",
                "severity": "Medium",
                "created_at": datetime.now().isoformat()
            },
            {
                "pattern_id": "PATTERN_004",
                "pattern_name": "Velocity Attack",
                "pattern_description": "Rapid succession of transactions across multiple accounts within hours, coordinated fraud with same IP cluster or device fingerprint",
                "severity": "High",
                "created_at": datetime.now().isoformat()
            },
            {
                "pattern_id": "PATTERN_005",
                "pattern_name": "Synthetic Identity Fraud",
                "pattern_description": "Gradual legitimate-looking transactions building trust over months, then sudden large purchases or cash advances",
                "severity": "Medium",
                "created_at": datetime.now().isoformat()
            }
        ]
        
        # Generate embeddings for each pattern
        for pattern in known_patterns:
            pattern['vector'] = get_embedding(pattern['pattern_description'])
        
        self.patterns_table.add(known_patterns)
        print(f"   Seeded {len(known_patterns)} fraud patterns")
    
    def add_transaction(self, transaction_data: Dict):
        """Add new transaction to database"""
        try:
            # Ensure all required fields are present
            required_fields = [
                'transaction_id', 'user_hash', 'amount', 'merchant_category',
                'location_city', 'device_type', 'payment_method_type', 'timestamp',
                'hour_of_day', 'day_of_week', 'behavior_text', 'vector'
            ]
            
            for field in required_fields:
                if field not in transaction_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Add default values for risk fields if not present
            transaction_data.setdefault('fraud_score', None)
            transaction_data.setdefault('risk_level', None)
            transaction_data.setdefault('is_flagged', False)
            transaction_data.setdefault('investigation_notes', None)
            
            self.transactions_table.add([transaction_data])
            return True
        except Exception as e:
            print(f"Error adding transaction: {e}")
            return False
    
    def search_similar_transactions(self, query_vector: List[float], limit=20, days_back=30):
        """Find similar transactions using vector search"""
        from datetime import timedelta
        
        try:
            cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()
            
            # LanceDB search
            results = (
                self.transactions_table
                .search(query_vector)
                .where(f"timestamp >= '{cutoff_date}'", prefilter=True)
                .limit(limit)
                .to_pandas()
            )
            
            return results
        except Exception as e:
            print(f"Error searching transactions: {e}")
            import pandas as pd
            return pd.DataFrame()
    
    def search_fraud_patterns(self, query_vector: List[float], limit=5):
        """Match against known fraud patterns"""
        try:
            results = (
                self.patterns_table
                .search(query_vector)
                .limit(limit)
                .to_pandas()
            )
            
            return results
        except Exception as e:
            print(f"Error searching fraud patterns: {e}")
            import pandas as pd
            return pd.DataFrame()
    
    def get_transaction_by_id(self, transaction_id: str):
        """Get specific transaction by ID"""
        try:
            df = self.transactions_table.to_pandas()
            result = df[df['transaction_id'] == transaction_id]
            
            if len(result) > 0:
                return result.iloc[0].to_dict()
            return None
        except Exception as e:
            print(f"Error getting transaction: {e}")
            return None
    
    def get_flagged_transactions(self, limit=100):
        """Get all flagged high-risk transactions"""
        try:
            df = self.transactions_table.to_pandas()
            flagged = df[df['is_flagged'] == True].head(limit)
            return flagged
        except Exception as e:
            print(f"Error getting flagged transactions: {e}")
            import pandas as pd
            return pd.DataFrame()
    
    def get_statistics(self):
        """Get dashboard statistics"""
        try:
            df = self.transactions_table.to_pandas()
            
            if len(df) == 0:
                return {
                    'total_transactions': 0,
                    'flagged_count': 0,
                    'avg_fraud_score': 0,
                    'high_risk_count': 0
                }
            
            # Calculate stats
            flagged_count = int(df['is_flagged'].sum()) if 'is_flagged' in df.columns else 0
            
            # Handle fraud_score - it might have None values
            if 'fraud_score' in df.columns:
                fraud_scores = df['fraud_score'].dropna()
                avg_fraud_score = float(fraud_scores.mean()) if len(fraud_scores) > 0 else 0
            else:
                avg_fraud_score = 0
            
            high_risk_count = int(len(df[df['risk_level'] == 'High'])) if 'risk_level' in df.columns else 0
            
            return {
                'total_transactions': len(df),
                'flagged_count': flagged_count,
                'avg_fraud_score': avg_fraud_score,
                'high_risk_count': high_risk_count
            }
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {
                'total_transactions': 0,
                'flagged_count': 0,
                'avg_fraud_score': 0,
                'high_risk_count': 0
            }
    
    def get_all_transactions(self):
        """Get all transactions as DataFrame"""
        try:
            return self.transactions_table.to_pandas()
        except Exception as e:
            print(f"Error getting all transactions: {e}")
            import pandas as pd
            return pd.DataFrame()

# Global instance
_db_manager = None

def get_db():
    """Get or create database manager singleton"""
    global _db_manager
    if _db_manager is None:
        _db_manager = LanceDBManager()
    return _db_manager
