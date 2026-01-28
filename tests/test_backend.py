"""
Basic Tests for FinGuard Components
Run with: python -m pytest tests/
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

def test_imports():
    """Test that all modules can be imported"""
    from backend import database
    from backend import vectorization
    from backend import ingestion
    from backend import pattern_detection
    from backend import investigation
    from backend import risk_scoring
    assert True

def test_ingestion():
    """Test transaction ingestion"""
    from backend.ingestion import ingest_transaction
    
    raw_txn = {
        "transaction_id": "TEST_001",
        "user_id": "USER_TEST",
        "amount": 50.00,
        "merchant": "Test Store",
        "location": "Test City, TX",
        "timestamp": "2026-01-24T12:00:00Z",
        "device": "iPhone",
        "payment_method": "Credit Card ending in 1234"
    }
    
    processed = ingest_transaction(raw_txn)
    
    assert processed['transaction_id'] == "TEST_001"
    assert processed['amount'] == 50.00
    assert 'user_hash' in processed
    assert 'merchant_category' in processed
    assert processed['user_hash'] != "USER_TEST"  # Should be hashed

def test_vectorization():
    """Test embedding generation"""
    from backend.vectorization import get_embedding, create_behavior_text
    
    transaction = {
        'amount': 50.00,
        'merchant_category': 'electronics',
        'location_city': 'New York',
        'device_type': 'mobile',
        'payment_method_type': 'credit_card',
        'hour_of_day': 14,
        'day_of_week': 'Monday'
    }
    
    behavior_text = create_behavior_text(transaction)
    assert len(behavior_text) > 0
    assert 'electronics' in behavior_text
    
    vector = get_embedding(behavior_text)
    assert len(vector) == 384  # Expected dimension

def test_amount_bucketing():
    """Test privacy-preserving amount bucketing"""
    from backend.vectorization import get_amount_bucket
    
    assert get_amount_bucket(5.0) == "micro (under $10)"
    assert get_amount_bucket(25.0) == "small ($10-$50)"
    assert get_amount_bucket(100.0) == "medium ($50-$200)"
    assert get_amount_bucket(500.0) == "large ($200-$1000)"
    assert get_amount_bucket(2000.0) == "very large (over $1000)"

def test_user_hashing():
    """Test user ID hashing for privacy"""
    from backend.ingestion import hash_user_id
    
    user_id = "USER_123"
    hash1 = hash_user_id(user_id)
    hash2 = hash_user_id(user_id)
    
    # Same input should give same hash
    assert hash1 == hash2
    
    # Hash should be different from input
    assert hash1 != user_id
    
    # Hash should be fixed length
    assert len(hash1) == 16

if __name__ == "__main__":
    print("Running FinGuard tests...")
    
    test_imports()
    print("Import test passed")
    
    test_ingestion()
    print("Ingestion test passed")
    
    test_vectorization()
    print("Vectorization test passed")
    
    test_amount_bucketing()
    print("Amount bucketing test passed")
    
    test_user_hashing()
    print("User hashing test passed")
    
    print("\nAll tests passed!")
