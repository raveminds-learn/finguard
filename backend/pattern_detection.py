"""
Pattern Detection Engine
Analyzes transactions for fraud patterns
"""

from backend.database import get_db
from datetime import datetime
from typing import Dict, List
import pandas as pd

def detect_patterns(transaction: Dict, transaction_vector: List[float]) -> Dict:
    """
    Analyze transaction against historical patterns
    
    Returns:
        Dict containing pattern analysis, fraud matches, and risk indicators
    """
    db = get_db()
    
    # 1. Search for similar historical transactions
    similar_txns = db.search_similar_transactions(
        query_vector=transaction_vector,
        limit=20,
        days_back=30
    )
    
    # 2. Search for matching known fraud patterns
    fraud_patterns = db.search_fraud_patterns(
        query_vector=transaction_vector,
        limit=3
    )
    
    # 3. Analyze results
    pattern_analysis = analyze_similar_transactions(similar_txns, transaction)
    fraud_match = analyze_fraud_patterns(fraud_patterns)
    
    # 4. Calculate risk indicators
    risk_indicators = calculate_risk_indicators(pattern_analysis, fraud_match, transaction)
    
    return {
        'pattern_analysis': pattern_analysis,
        'fraud_match': fraud_match,
        'risk_indicators': risk_indicators,
        'similar_transactions': similar_txns.to_dict('records') if len(similar_txns) > 0 else []
    }

def analyze_similar_transactions(similar_txns_df: pd.DataFrame, current_txn: Dict) -> Dict:
    """
    Analyze patterns in similar historical transactions
    """
    
    if len(similar_txns_df) == 0:
        return {
            'similar_count': 0,
            'unique_users': 0,
            'avg_similarity': 0,
            'time_span_days': 0,
            'amount_range': {'min': 0, 'max': 0, 'avg': 0}
        }
    
    # Filter for high similarity
    # LanceDB returns distance (lower = more similar)
    # Distance < 0.3 means similarity > 0.7
    high_similarity = similar_txns_df[similar_txns_df['_distance'] < 0.3]
    
    if len(high_similarity) == 0:
        return {
            'similar_count': 0,
            'unique_users': 0,
            'avg_similarity': 0,
            'time_span_days': 0,
            'amount_range': {'min': 0, 'max': 0, 'avg': 0}
        }
    
    # Analyze patterns
    unique_users = high_similarity['user_hash'].nunique()
    
    # Convert distance to similarity (similarity = 1 - distance)
    avg_similarity = 1 - high_similarity['_distance'].mean()
    
    # Time span analysis
    try:
        timestamps = pd.to_datetime(high_similarity['timestamp'])
        time_span = (timestamps.max() - timestamps.min()).days if len(timestamps) > 1 else 0
    except:
        time_span = 0
    
    # Amount analysis
    amounts = high_similarity['amount']
    
    return {
        'similar_count': len(high_similarity),
        'unique_users': unique_users,
        'avg_similarity': float(avg_similarity),
        'time_span_days': time_span,
        'amount_range': {
            'min': float(amounts.min()),
            'max': float(amounts.max()),
            'avg': float(amounts.mean())
        },
        'merchant_diversity': high_similarity['merchant_category'].nunique(),
        'device_diversity': high_similarity['device_type'].nunique()
    }

def analyze_fraud_patterns(fraud_patterns_df: pd.DataFrame) -> Dict:
    """
    Match against known fraud patterns
    """
    
    if len(fraud_patterns_df) == 0:
        return {
            'matched': False,
            'pattern_name': None,
            'confidence': 0,
            'severity': None,
            'pattern_description': None
        }
    
    # Get best match (first result has lowest distance)
    best_match = fraud_patterns_df.iloc[0]
    
    # Convert distance to confidence
    confidence = 1 - best_match['_distance']
    
    # Consider it a match if confidence > 0.7
    is_match = confidence > 0.7
    
    return {
        'matched': is_match,
        'pattern_name': best_match['pattern_name'],
        'pattern_description': best_match['pattern_description'],
        'severity': best_match['severity'],
        'confidence': float(confidence)
    }

def calculate_risk_indicators(pattern_analysis: Dict, fraud_match: Dict, transaction: Dict) -> Dict:
    """
    Calculate specific risk indicators based on patterns
    """
    
    indicators = {
        'multiple_accounts': False,
        'time_dilated': False,
        'amount_clustering': False,
        'high_fraud_match': False,
        'merchant_hopping': False,
        'device_switching': False,
        'requires_investigation': False
    }
    
    # Check for multiple accounts involved
    if pattern_analysis['unique_users'] > 5:
        indicators['multiple_accounts'] = True
    
    # Check for time-dilated pattern
    if pattern_analysis['time_span_days'] > 7 and pattern_analysis['similar_count'] > 5:
        indicators['time_dilated'] = True
    
    # Check for amount clustering (similar amounts)
    if pattern_analysis['similar_count'] > 3:
        amount_range = pattern_analysis['amount_range']
        variance = amount_range['max'] - amount_range['min']
        # Tight clustering = potential card testing
        if variance < 20:
            indicators['amount_clustering'] = True
    
    # Check fraud pattern match
    if fraud_match['matched']:
        indicators['high_fraud_match'] = True
    
    # Check merchant hopping
    if pattern_analysis.get('merchant_diversity', 0) > 5:
        indicators['merchant_hopping'] = True
    
    # Check device switching
    if pattern_analysis.get('device_diversity', 0) > 2:
        indicators['device_switching'] = True
    
    # Determine if LLM investigation is needed
    indicators['requires_investigation'] = (
        indicators['multiple_accounts'] or
        indicators['high_fraud_match'] or
        indicators['time_dilated'] or
        (pattern_analysis['similar_count'] > 10)
    )
    
    return indicators

def get_pattern_summary(detection_results: Dict) -> str:
    """
    Generate human-readable pattern summary
    """
    pattern = detection_results['pattern_analysis']
    fraud = detection_results['fraud_match']
    risk = detection_results['risk_indicators']
    
    summary_parts = []
    
    # Similar patterns
    if pattern['similar_count'] > 0:
        summary_parts.append(
            f"Found {pattern['similar_count']} similar transactions "
            f"across {pattern['unique_users']} accounts "
            f"spanning {pattern['time_span_days']} days"
        )
    
    # Fraud pattern match
    if fraud['matched']:
        summary_parts.append(
            f"Matches known '{fraud['pattern_name']}' pattern "
            f"({fraud['severity']} severity, {fraud['confidence']:.0%} confidence)"
        )
    
    # Risk indicators
    active_risks = [k for k, v in risk.items() if v and k != 'requires_investigation']
    if active_risks:
        summary_parts.append(f"Risk indicators: {', '.join(active_risks)}")
    
    return ". ".join(summary_parts) if summary_parts else "No significant patterns detected"
