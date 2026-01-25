"""
Risk Scoring Module
Combines pattern analysis and LLM assessment into final fraud score
"""

from typing import Dict, List

def calculate_fraud_score(
    pattern_analysis: Dict, 
    fraud_match: Dict, 
    risk_indicators: Dict, 
    llm_result: Dict
) -> Dict:
    """
    Combine all signals into final fraud score
    
    Uses hybrid approach:
    - 40% rule-based scoring (pattern analysis)
    - 60% AI-based scoring (LLM confidence)
    
    Returns:
        Dict with fraud_risk_score, risk_level, and breakdown
    """
    
    # ===== RULE-BASED SCORING (40% weight) =====
    rule_score = 0
    
    # Pattern-based rules
    unique_users = pattern_analysis['unique_users']
    similar_count = pattern_analysis['similar_count']
    time_span = pattern_analysis['time_span_days']
    
    # Multiple accounts indicator (max 35 points)
    if unique_users > 10:
        rule_score += 35
    elif unique_users > 5:
        rule_score += 25
    elif unique_users > 2:
        rule_score += 15
    
    # High similarity count (max 25 points)
    if similar_count > 15:
        rule_score += 25
    elif similar_count > 10:
        rule_score += 15
    elif similar_count > 5:
        rule_score += 10
    
    # Time-dilated pattern (20 points)
    if risk_indicators['time_dilated']:
        rule_score += 20
    
    # Amount clustering (20 points)
    if risk_indicators['amount_clustering']:
        rule_score += 20
    
    # Merchant hopping (15 points)
    if risk_indicators['merchant_hopping']:
        rule_score += 15
    
    # Device switching (15 points)
    if risk_indicators['device_switching']:
        rule_score += 15
    
    # Fraud pattern match (max 40 points based on severity)
    if fraud_match['matched']:
        severity = fraud_match.get('severity', 'Medium')
        confidence = fraud_match['confidence']
        
        if severity == 'Critical':
            rule_score += int(40 * confidence)
        elif severity == 'High':
            rule_score += int(30 * confidence)
        else:
            rule_score += int(20 * confidence)
    
    # Cap rule score at 100
    rule_score = min(rule_score, 100)
    
    # ===== LLM CONFIDENCE (60% weight) =====
    llm_score = llm_result.get('confidence', 50)
    
    # Ensure llm_score is in 0-100 range
    llm_score = max(0, min(100, llm_score))
    
    # ===== COMBINED SCORE =====
    final_score = int((rule_score * 0.4) + (llm_score * 0.6))
    
    # Determine risk level
    if final_score >= 75:
        risk_level = "High"
    elif final_score >= 50:
        risk_level = "Medium"
    else:
        risk_level = "Low"
    
    return {
        'fraud_risk_score': final_score,
        'risk_level': risk_level,
        'rule_based_score': rule_score,
        'llm_confidence': llm_score,
        'breakdown': {
            'pattern_signals': rule_score,
            'ai_assessment': llm_score,
            'weight_rule': 0.4,
            'weight_ai': 0.6
        }
    }

def generate_recommendations(
    risk_score: Dict, 
    llm_result: Dict, 
    transaction: Dict,
    pattern_analysis: Dict
) -> List[str]:
    """
    Generate actionable recommendations based on risk level
    """
    
    recommendations = []
    
    # Start with LLM recommendations if available
    llm_recs = llm_result.get('recommendations', [])
    if llm_recs:
        recommendations.extend(llm_recs[:3])  # Max 3 from LLM
    
    # Add specific recommendations based on risk level
    fraud_score = risk_score['fraud_risk_score']
    user_hash = transaction['user_hash'][:8]  # First 8 chars for display
    
    if fraud_score >= 75:
        # HIGH RISK
        recommendations.extend([
            f"🚨 URGENT: Flag account {user_hash}... for immediate review",
            "Temporarily block/hold account pending investigation",
            "Notify fraud investigation team within 15 minutes",
            "Review all transactions from this account in last 30 days",
            f"Check related accounts ({pattern_analysis['unique_users']} accounts in pattern)"
        ])
    elif fraud_score >= 50:
        # MEDIUM RISK
        recommendations.extend([
            f"⚠️ Flag account {user_hash}... for manual review within 24 hours",
            "Implement step-up authentication for next 3 transactions",
            "Monitor account closely for next 7 days",
            "Review recent transaction history (last 14 days)",
            "Set transaction amount limit temporarily"
        ])
    else:
        # LOW RISK
        recommendations.extend([
            "Continue normal monitoring",
            "No immediate action required",
            "Log for historical pattern analysis"
        ])
    
    # Add pattern-specific recommendations
    if pattern_analysis['similar_count'] > 10:
        recommendations.append(
            f"Investigate {pattern_analysis['similar_count']} similar transactions "
            f"across {pattern_analysis['unique_users']} accounts"
        )
    
    # Remove duplicates while preserving order
    seen = set()
    unique_recommendations = []
    for rec in recommendations:
        if rec not in seen:
            seen.add(rec)
            unique_recommendations.append(rec)
    
    # Return top 5 recommendations
    return unique_recommendations[:5]

def generate_explanation(
    risk_score: Dict,
    pattern_analysis: Dict,
    fraud_match: Dict,
    llm_result: Dict
) -> str:
    """
    Generate human-readable explanation of fraud score
    """
    
    explanation_parts = []
    
    # Risk level statement
    fraud_score_val = risk_score['fraud_risk_score']
    risk_level = risk_score['risk_level']
    
    explanation_parts.append(
        f"Fraud risk score: {fraud_score_val}/100 ({risk_level} Risk)."
    )
    
    # Pattern analysis
    if pattern_analysis['similar_count'] > 0:
        explanation_parts.append(
            f"Found {pattern_analysis['similar_count']} similar transactions "
            f"across {pattern_analysis['unique_users']} different accounts "
            f"over {pattern_analysis['time_span_days']} days."
        )
    
    # Fraud pattern match
    if fraud_match['matched']:
        explanation_parts.append(
            f"Matches known '{fraud_match['pattern_name']}' pattern "
            f"({fraud_match['severity']} severity) with {fraud_match['confidence']:.0%} confidence."
        )
    
    # LLM reasoning
    if llm_result.get('reasoning'):
        explanation_parts.append(llm_result['reasoning'])
    
    return " ".join(explanation_parts)

def create_fraud_alert(
    transaction: Dict,
    risk_score: Dict,
    pattern_analysis: Dict,
    fraud_match: Dict,
    llm_result: Dict,
    recommendations: List[str]
) -> Dict:
    """
    Create final fraud alert output matching expected format
    """
    
    alert = {
        'transaction_id': transaction['transaction_id'],
        'fraud_risk_score': risk_score['fraud_risk_score'],
        'risk_level': risk_score['risk_level'],
        'reasoning': generate_explanation(risk_score, pattern_analysis, fraud_match, llm_result),
        'behavioral_analysis': {
            'similar_patterns_found': pattern_analysis['similar_count'],
            'time_span_days': pattern_analysis['time_span_days'],
            'accounts_involved': pattern_analysis['unique_users'],
            'vector_similarity_score': pattern_analysis['avg_similarity'],
            'known_fraud_pattern': fraud_match['pattern_name'] or 'None detected'
        },
        'investigation_notes': llm_result.get('reasoning', 'No investigation performed'),
        'recommendations': recommendations,
        'confidence': risk_score['llm_confidence'] / 100,
        'status': 'flagged_for_review' if risk_score['fraud_risk_score'] >= 70 else 'monitor',
        'timestamp': transaction['timestamp']
    }
    
    return alert
