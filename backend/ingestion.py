"""
Transaction Ingestion Module
Processes and anonymizes incoming transactions
"""

import hashlib
from datetime import datetime
from typing import Dict

def hash_user_id(user_id: str) -> str:
    """
    One-way hash for user privacy
    SHA-256 ensures irreversibility
    """
    return hashlib.sha256(user_id.encode()).hexdigest()[:16]

def categorize_merchant(merchant: str) -> str:
    """
    Categorize merchant into broad categories
    Reduces specificity for privacy
    """
    merchant_lower = merchant.lower()
    
    categories = {
        'electronics': ['electronics', 'tech', 'gadget', 'computer', 'phone', 'tablet'],
        'grocery': ['grocery', 'food', 'market', 'supermarket', 'store'],
        'retail': ['retail', 'shop', 'clothing', 'fashion', 'apparel'],
        'online': ['online', 'web', 'internet', 'ecommerce', 'amazon'],
        'travel': ['airline', 'hotel', 'travel', 'booking', 'flight'],
        'entertainment': ['movie', 'game', 'entertainment', 'streaming', 'music'],
        'restaurant': ['restaurant', 'cafe', 'coffee', 'dining', 'pizza', 'burger'],
        'gas': ['gas', 'fuel', 'petrol', 'station'],
        'pharmacy': ['pharmacy', 'drug', 'cvs', 'walgreens', 'medicine'],
        'home': ['home', 'depot', 'hardware', 'garden', 'furniture']
    }
    
    for category, keywords in categories.items():
        if any(kw in merchant_lower for kw in keywords):
            return category
    
    return 'other'

def extract_device_type(device: str) -> str:
    """Extract device type category"""
    device_lower = device.lower()
    
    if 'iphone' in device_lower or 'android' in device_lower or 'samsung' in device_lower:
        return 'mobile'
    elif 'ipad' in device_lower or 'tablet' in device_lower:
        return 'tablet'
    elif 'mac' in device_lower or 'windows' in device_lower or 'laptop' in device_lower:
        return 'desktop'
    else:
        return 'unknown'

def extract_payment_type(payment_method: str) -> str:
    """Extract payment type category"""
    payment_lower = payment_method.lower()
    
    if 'credit' in payment_lower:
        return 'credit_card'
    elif 'debit' in payment_lower:
        return 'debit_card'
    elif 'paypal' in payment_lower:
        return 'paypal'
    elif 'venmo' in payment_lower or 'zelle' in payment_lower:
        return 'p2p'
    else:
        return 'other'

def parse_timestamp(timestamp_str: str) -> Dict:
    """
    Parse timestamp and extract temporal features
    """
    # Handle both ISO format and Z suffix
    timestamp_str = timestamp_str.replace('Z', '+00:00')
    
    try:
        dt = datetime.fromisoformat(timestamp_str)
    except:
        # Fallback to current time if parsing fails
        dt = datetime.now()
    
    return {
        'timestamp': dt.isoformat(),
        'hour_of_day': dt.hour,
        'day_of_week': dt.strftime('%A')
    }

def validate_transaction(transaction: Dict) -> bool:
    """
    Validate required fields are present
    """
    required_fields = [
        'transaction_id',
        'user_id',
        'amount',
        'merchant',
        'location',
        'timestamp',
        'device',
        'payment_method'
    ]
    
    for field in required_fields:
        if field not in transaction:
            print(f"❌ Missing required field: {field}")
            return False
    
    return True

def ingest_transaction(raw_transaction: Dict) -> Dict:
    """
    Process and anonymize incoming transaction
    
    Privacy features:
    - User ID hashed (irreversible)
    - Merchant categorized (not exact name)
    - Location reduced to city only
    - Device type categorized
    - Payment method categorized
    
    Args:
        raw_transaction: Raw transaction from banking system
    
    Returns:
        Processed and anonymized transaction
    """
    
    # Validate input
    if not validate_transaction(raw_transaction):
        raise ValueError("Invalid transaction: missing required fields")
    
    # Parse timestamp
    time_features = parse_timestamp(raw_transaction['timestamp'])
    
    # Create anonymized transaction
    processed = {
        'transaction_id': raw_transaction['transaction_id'],
        'user_hash': hash_user_id(raw_transaction['user_id']),
        'amount': float(raw_transaction['amount']),
        'merchant_category': categorize_merchant(raw_transaction['merchant']),
        'location_city': raw_transaction['location'].split(',')[0].strip(),
        'device_type': extract_device_type(raw_transaction['device']),
        'payment_method_type': extract_payment_type(raw_transaction['payment_method']),
        'timestamp': time_features['timestamp'],
        'hour_of_day': time_features['hour_of_day'],
        'day_of_week': time_features['day_of_week'],
        
        # Initialize risk fields (will be filled during analysis)
        'fraud_score': None,
        'risk_level': None,
        'is_flagged': False,
        'investigation_notes': None
    }
    
    return processed

def batch_ingest(raw_transactions: list) -> list:
    """
    Process multiple transactions
    """
    processed = []
    
    for i, raw_txn in enumerate(raw_transactions):
        try:
            processed_txn = ingest_transaction(raw_txn)
            processed.append(processed_txn)
        except Exception as e:
            print(f"❌ Error processing transaction {i+1}: {e}")
            continue
    
    return processed
