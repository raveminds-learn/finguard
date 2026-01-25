"""
AI Investigation Agent
Uses Ollama LLM for forensic fraud analysis
"""

import ollama
import json
from typing import Dict

def investigate_with_llm(transaction: Dict, detection_results: Dict) -> Dict:
    """
    Use Ollama LLM for forensic analysis of suspicious transaction
    
    Args:
        transaction: The transaction being analyzed
        detection_results: Results from pattern detection
    
    Returns:
        Dict with LLM's fraud assessment
    """
    
    pattern = detection_results['pattern_analysis']
    fraud_match = detection_results['fraud_match']
    risk = detection_results['risk_indicators']
    
    # Build investigation prompt
    prompt = create_investigation_prompt(transaction, pattern, fraud_match, risk)
    
    try:
        # Call Ollama
        print("Invoking LLM investigation...")
        response = ollama.generate(
            model='mistral:latest',
            prompt=prompt,
            options={
                'temperature': 0.2,  # Low temperature for consistency
                'num_predict': 500,
                'top_p': 0.9
            }
        )
        
        # Parse response
        result = parse_llm_response(response['response'])
        print("LLM investigation complete")
        
        return result
        
    except Exception as e:
        print(f"LLM Investigation Error: {e}")
        
        # Fallback response if LLM fails
        return create_fallback_response(risk, fraud_match)

def create_investigation_prompt(transaction: Dict, pattern: Dict, fraud_match: Dict, risk: Dict) -> str:
    """
    Create structured prompt for LLM investigation
    """
    
    prompt = f"""You are an expert fraud detection AI agent conducting a forensic analysis of a financial transaction.

TRANSACTION UNDER INVESTIGATION:
- Transaction ID: {transaction['transaction_id']}
- Amount: ${transaction['amount']:.2f}
- Merchant Category: {transaction['merchant_category']}
- Device Type: {transaction['device_type']}
- Location: {transaction['location_city']}
- Time: {transaction['hour_of_day']}:00 on {transaction['day_of_week']}
- Payment Method: {transaction['payment_method_type']}

PATTERN ANALYSIS FINDINGS:
- Similar transactions found: {pattern['similar_count']}
- Different accounts involved: {pattern['unique_users']}
- Time span of pattern: {pattern['time_span_days']} days
- Average similarity score: {pattern['avg_similarity']:.2%}
- Amount range: ${pattern['amount_range']['min']:.2f} - ${pattern['amount_range']['max']:.2f}

FRAUD PATTERN MATCH:
- Matched known pattern: {fraud_match['pattern_name'] or 'None'}
- Match confidence: {fraud_match['confidence']:.2%}
- Pattern severity: {fraud_match.get('severity', 'N/A')}
- Description: {fraud_match.get('pattern_description', 'N/A')}

RISK INDICATORS DETECTED:
- Multiple accounts involved: {risk['multiple_accounts']}
- Time-dilated attack pattern: {risk['time_dilated']}
- Amount clustering (card testing): {risk['amount_clustering']}
- High fraud pattern match: {risk['high_fraud_match']}
- Merchant hopping detected: {risk['merchant_hopping']}
- Device switching detected: {risk['device_switching']}

YOUR TASK:
As a fraud investigator, analyze this information and provide your assessment in JSON format:

{{
  "is_fraud": true or false,
  "confidence": 0-100 (your confidence level),
  "fraud_type": "Card Testing" | "Account Takeover" | "Low-and-Slow" | "Velocity Attack" | "Legitimate" | "Unknown",
  "reasoning": "2-3 sentences explaining why you believe this is or isn't fraud",
  "recommendations": ["action 1", "action 2", "action 3"]
}}

IMPORTANT: Respond ONLY with valid JSON, no markdown formatting, no extra text.
"""
    
    return prompt

def parse_llm_response(response_text: str) -> Dict:
    """
    Parse LLM response and extract JSON
    """
    
    # Clean response
    response_text = response_text.strip()
    
    # Remove markdown code blocks if present
    if '```' in response_text:
        # Extract content between code blocks
        parts = response_text.split('```')
        for part in parts:
            part = part.strip()
            if part.startswith('json'):
                part = part[4:].strip()
            # Try to parse this part as JSON
            try:
                result = json.loads(part)
                return validate_llm_result(result)
            except:
                continue
    
    # Try direct JSON parse
    try:
        result = json.loads(response_text)
        return validate_llm_result(result)
    except json.JSONDecodeError as e:
        print(f"Warning: Could not parse LLM response as JSON: {e}")
        
        # Try to extract JSON from text
        import re
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            try:
                result = json.loads(json_match.group())
                return validate_llm_result(result)
            except:
                pass
        
        raise ValueError("Could not parse LLM response")

def validate_llm_result(result: Dict) -> Dict:
    """
    Validate and normalize LLM result
    """
    
    # Ensure all required fields are present
    required_fields = ['is_fraud', 'confidence', 'fraud_type', 'reasoning', 'recommendations']
    
    for field in required_fields:
        if field not in result:
            raise ValueError(f"Missing required field: {field}")
    
    # Normalize confidence to 0-100
    confidence = result['confidence']
    if isinstance(confidence, float) and confidence <= 1.0:
        result['confidence'] = int(confidence * 100)
    else:
        result['confidence'] = int(confidence)
    
    # Ensure recommendations is a list
    if isinstance(result['recommendations'], str):
        result['recommendations'] = [result['recommendations']]
    
    return result

def create_fallback_response(risk: Dict, fraud_match: Dict) -> Dict:
    """
    Create fallback response when LLM fails
    Uses rule-based logic
    """
    
    # Count risk indicators
    risk_count = sum(1 for k, v in risk.items() if v and k != 'requires_investigation')
    
    # Determine fraud likelihood
    is_fraud = risk_count >= 3 or fraud_match['matched']
    confidence = min(risk_count * 20 + (30 if fraud_match['matched'] else 0), 90)
    
    fraud_type = fraud_match['pattern_name'] if fraud_match['matched'] else 'Unknown'
    
    reasoning = f"Rule-based assessment: {risk_count} risk indicators detected. "
    if fraud_match['matched']:
        reasoning += f"Matches {fraud_match['pattern_name']} pattern. "
    reasoning += "LLM analysis unavailable, using fallback logic."
    
    recommendations = [
        "Manual review required (LLM unavailable)",
        "Check transaction history",
        "Verify user identity"
    ]
    
    if is_fraud:
        recommendations.append("Consider temporary account hold")
    
    return {
        'is_fraud': is_fraud,
        'confidence': confidence,
        'fraud_type': fraud_type,
        'reasoning': reasoning,
        'recommendations': recommendations
    }

def batch_investigate(transactions_and_detections: list) -> list:
    """
    Investigate multiple transactions
    """
    results = []
    
    for txn, detection in transactions_and_detections:
        result = investigate_with_llm(txn, detection)
        results.append(result)
    
    return results
