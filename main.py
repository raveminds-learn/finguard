"""
FinGuard Main Orchestration
Complete fraud detection pipeline
"""

import json
import argparse
from datetime import datetime
from typing import Dict

from backend.database import get_db
from backend.ingestion import ingest_transaction, batch_ingest
from backend.vectorization import vectorize_transaction, batch_vectorize
from backend.pattern_detection import detect_patterns
from backend.investigation import investigate_with_llm
from backend.risk_scoring import (
    calculate_fraud_score,
    generate_recommendations,
    create_fraud_alert
)

def process_transaction(raw_transaction: Dict) -> Dict:
    """
    Complete fraud detection pipeline for a single transaction
    
    Pipeline:
    1. Ingest & normalize transaction
    2. Vectorize behavioral patterns
    3. Store in vector database
    4. Detect similar patterns
    5. AI investigation (if needed)
    6. Calculate fraud score
    7. Generate alert
    
    Args:
        raw_transaction: Raw transaction from banking system
    
    Returns:
        Fraud alert with risk assessment
    """
    
    print(f"\n{'-'*60}")
    print(f"Processing Transaction: {raw_transaction['transaction_id']}")
    print(f"{'-'*60}")
    
    # Step 1: Ingest & normalize
    print("Step 1: Ingesting transaction...")
    transaction = ingest_transaction(raw_transaction)
    print(f"   Normalized and anonymized")
    
    # Step 2: Vectorize
    print("Step 2: Vectorizing behavioral pattern...")
    transaction = vectorize_transaction(transaction)
    print(f"   Generated 384-dim embedding")

    # Step 3: Pattern detection (use existing history; do not store current txn yet)
    print("Step 3: Detecting fraud patterns...")
    detection_results = detect_patterns(transaction, transaction['vector'])
    pattern = detection_results['pattern_analysis']
    fraud_match = detection_results['fraud_match']
    risk = detection_results['risk_indicators']
    
    print(f"   Similar transactions: {pattern['similar_count']}")
    print(f"   Accounts involved: {pattern['unique_users']}")
    if fraud_match['matched']:
        print(f"   Matched pattern: {fraud_match['pattern_name']} ({fraud_match['confidence']:.0%})")
    
    # Step 4: AI Investigation (if needed)
    if risk['requires_investigation']:
        print("Step 4: AI forensic investigation...")
        llm_result = investigate_with_llm(transaction, detection_results)
        print(f"   LLM verdict: {'FRAUD' if llm_result['is_fraud'] else 'LEGITIMATE'}")
        print(f"   Confidence: {llm_result['confidence']}%")
    else:
        print("Step 4: Skipping AI investigation (low risk)")
        llm_result = {
            'is_fraud': False,
            'confidence': 25,
            'fraud_type': 'Legitimate',
            'reasoning': 'No significant risk indicators detected',
            'recommendations': ['Continue monitoring']
        }
    
    # Step 5: Calculate fraud score
    print("Step 5: Calculating fraud risk score...")
    risk_score = calculate_fraud_score(pattern, fraud_match, risk, llm_result)
    print(f"   Final Score: {risk_score['fraud_risk_score']}/100 ({risk_score['risk_level']} Risk)")
    
    # Step 6: Generate recommendations
    print("Step 6: Generating recommendations...")
    recommendations = generate_recommendations(risk_score, llm_result, transaction, pattern)
    
    # Step 7: Persist scored transaction for the dashboard
    print("Step 7: Storing scored transaction in vector database...")
    transaction['fraud_score'] = float(risk_score['fraud_risk_score'])
    transaction['risk_level'] = risk_score['risk_level']
    transaction['is_flagged'] = bool(risk_score['fraud_risk_score'] >= 70)
    transaction['investigation_notes'] = llm_result.get('reasoning', None)
    db = get_db()
    db.add_transaction(transaction)
    print("   Stored in LanceDB")

    # Create final alert
    alert = create_fraud_alert(
        transaction, risk_score, pattern, fraud_match, llm_result, recommendations
    )
    
    print(f"\n{'-'*60}")
    print(f"PROCESSING COMPLETE")
    print(f"{'-'*60}\n")
    
    return alert

def process_batch(raw_transactions: list) -> list:
    """Process multiple transactions"""
    
    print(f"\nProcessing batch of {len(raw_transactions)} transactions...\n")
    
    alerts = []
    for i, raw_txn in enumerate(raw_transactions, 1):
        print(f"\n[{i}/{len(raw_transactions)}]")
        try:
            alert = process_transaction(raw_txn)
            alerts.append(alert)
        except Exception as e:
            print(f"Error processing transaction: {e}")
            continue
    
    print(f"\nBatch processing complete: {len(alerts)}/{len(raw_transactions)} successful")
    return alerts

def load_sample_transactions() -> list:
    """Load sample transactions for testing"""
    
    from datetime import timedelta
    
    # Generate sample transactions with varying fraud patterns.
    # IMPORTANT: These are intentionally crafted to reliably create similarity clusters
    # so some transactions get flagged in the UI.
    samples = []
    base_time = datetime.now().replace(minute=0, second=0, microsecond=0)
    
    # Normal transaction
    samples.append({
        "transaction_id": "TXN_001",
        "user_id": "USER_NORMAL_001",
        "amount": 85.50,
        "merchant": "Local Grocery Store",
        "location": "Dallas, TX",
        "timestamp": base_time.isoformat(),
        "device": "iPhone 12",
        "payment_method": "Credit Card ending in 1234"
    })
    
    # Card testing pattern (many small transactions, highly similar)
    # Create enough near-identical samples so later ones will match >10 historical txns
    # and trigger investigation + high scores.
    for i in range(12):
        samples.append({
            "transaction_id": f"TXN_CARDTEST_{i+1:03d}",
            "user_id": f"USER_VICTIM_{i+1:03d}",
            "amount": 19.99,  # keep same bucket + high similarity
            "merchant": "Online Electronics Store",
            "location": "New York, NY",
            "timestamp": (base_time + timedelta(minutes=i)).isoformat(),
            "device": "iPhone 13 Pro",
            "payment_method": f"Credit Card ending in 45{i+1}1"
        })
    
    # Account takeover pattern
    samples.append({
        "transaction_id": "TXN_ATO_001",
        "user_id": "USER_COMPROMISED_001",
        "amount": 299.99,
        "merchant": "Unknown Online Retailer",
        "location": "Moscow, Russia",
        "timestamp": (base_time - timedelta(hours=2)).isoformat(),
        "device": "Unknown Android Device",
        "payment_method": "Credit Card ending in 9876"
    })
    
    # Low-and-slow pattern
    for i in range(3):
        samples.append({
            "transaction_id": f"TXN_SLOW_{i+1:03d}",
            "user_id": f"USER_SLOW_{i+1:03d}",
            "amount": 38.50,
            "merchant": "Online Tech Shop",
            "location": "San Francisco, CA",
            "timestamp": (base_time - timedelta(days=i*3)).isoformat(),
            "device": "iPad Pro",
            "payment_method": f"Credit Card ending in 22{i+1}1"
        })
    
    return samples

def main():
    """Main entry point"""
    
    parser = argparse.ArgumentParser(description='FinGuard Fraud Detection System')
    parser.add_argument('--transaction', type=str, help='JSON string of single transaction')
    parser.add_argument('--file', type=str, help='Path to JSON file with transaction(s)')
    parser.add_argument('--sample', action='store_true', help='Process sample transactions')
    parser.add_argument('--output', type=str, help='Output file for results')
    
    args = parser.parse_args()
    
    # Initialize database
    try:
        print("Initializing FinGuard...")
    except UnicodeEncodeError:
        print("Initializing FinGuard...")
    try:
        db = get_db()
    except Exception as e:
        print(f"Error initializing database: {e}")
        return
    print("System ready\n")
    
    results = []
    
    # Process based on input
    if args.sample:
        print("Loading sample transactions...")
        transactions = load_sample_transactions()
        results = process_batch(transactions)
    
    elif args.transaction:
        print("Processing single transaction from command line...")
        transaction = json.loads(args.transaction)
        result = process_transaction(transaction)
        results = [result]
    
    elif args.file:
        print(f"Loading transactions from {args.file}...")
        with open(args.file, 'r') as f:
            data = json.load(f)
            transactions = data if isinstance(data, list) else [data]
        results = process_batch(transactions)
    
    else:
        print("No input provided. Use --sample, --transaction, or --file")
        print("\nExamples:")
        print("  python main.py --sample")
        print("  python main.py --file data/transactions.json")
        print('  python main.py --transaction \'{"transaction_id": "TXN_001", ...}\'')
        return
    
    # Print summary
    if results:
        print("\n" + "="*60)
        print("FRAUD DETECTION SUMMARY")
        print("="*60)
        
        high_risk = [r for r in results if r['risk_level'] == 'High']
        medium_risk = [r for r in results if r['risk_level'] == 'Medium']
        low_risk = [r for r in results if r['risk_level'] == 'Low']
        
        print(f"\nTotal Processed: {len(results)}")
        print(f"  High Risk: {len(high_risk)}")
        print(f"  Medium Risk: {len(medium_risk)}")
        print(f"  Low Risk: {len(low_risk)}")
        
        avg_score = sum(r['fraud_risk_score'] for r in results) / len(results)
        print(f"\nAverage Fraud Score: {avg_score:.1f}/100")
        
        # Show high risk details
        if high_risk:
            print("\nHIGH RISK TRANSACTIONS:")
            for alert in high_risk:
                print(f"\n  Transaction: {alert['transaction_id']}")
                print(f"  Score: {alert['fraud_risk_score']}/100")
                print(f"  Pattern: {alert['behavioral_analysis']['known_fraud_pattern']}")
                print(f"  Recommendation: {alert['recommendations'][0]}")
    
    # Save results if output file specified
    if args.output and results:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to {args.output}")

if __name__ == "__main__":
    main()
