# FinGuard Project Summary

## What This Project Does

FinGuard is a **zero-cost behavioral fraud detection system** that uses AI to identify sophisticated fraud patterns that traditional rule-based systems miss. It analyzes transaction behavior patterns across time and accounts to detect:

- **Card Testing**: Multiple small transactions to validate stolen cards
- **Account Takeover**: Unauthorized access with behavioral changes
- **Low-and-Slow Attacks**: Small amounts over time to avoid detection
- **Velocity Attacks**: Rapid coordinated fraud across accounts

## Architecture Overview

```
Transaction Input
     ↓
1. Ingestion Pipeline (Anonymize PII)
     ↓
2. Behavioral Vectorization (384-dim embeddings)
     ↓
3. Vector Storage (LanceDB)
     ↓
4. Pattern Detection (Similarity search)
     ↓
5. AI Investigation (Ollama LLM)
     ↓
6. Risk Scoring (Hybrid: 40% rules + 60% AI)
     ↓
7. Alert Generation (Actionable recommendations)
```

## Technology Stack

| Component | Technology | Cost |
|-----------|-----------|------|
| Vector Database | LanceDB | FREE (embedded) |
| Embeddings | sentence-transformers | FREE (local) |
| LLM | Ollama (Llama 3.3) | FREE (local) |
| Dashboard | Streamlit | FREE |
| Backend | Python, FastAPI | FREE |
| Data Processing | pandas, numpy | FREE |

**Total Cost: $0**

## Project Structure

```
finguard/
├── backend/                    # Core fraud detection logic
│   ├── database.py            # LanceDB management
│   ├── vectorization.py       # Embedding generation
│   ├── ingestion.py           # Transaction processing
│   ├── pattern_detection.py   # Pattern analysis
│   ├── investigation.py       # LLM agent
│   ├── risk_scoring.py        # Score calculation
│   └── setup_db.py            # Database initialization
│
├── dashboard/                  # Streamlit UI
│   └── app.py                 # Main dashboard
│
├── data/                       # Data storage
│   ├── lancedb/               # Vector database
│   └── sample_transactions.json
│
├── config/                     # Configuration
│   └── config.yaml
│
├── tests/                      # Unit tests
│   └── test_backend.py
│
├── main.py                     # CLI orchestrator
├── requirements.txt            # Dependencies
├── setup.sh                    # Auto-setup script
├── README.md                   # Full documentation
├── QUICKSTART.md              # Quick start guide
└── LICENSE                     # MIT License
```

## Privacy Features

1. **User ID Hashing**: SHA-256 one-way hash (irreversible)
2. **Merchant Categorization**: Broad categories, not exact names
3. **Amount Bucketing**: Ranges instead of exact amounts
4. **Location Generalization**: City only, no full addresses
5. **Device Type Categorization**: Type only, not fingerprints

**Result**: Vector embeddings contain NO personally identifiable information

## How It Works - Example

**Input Transaction:**
```json
{
  "transaction_id": "TXN_98234",
  "user_id": "USER_5021",
  "amount": 47.50,
  "merchant": "Online Electronics Store",
  "location": "New York, NY",
  "timestamp": "2026-01-19T14:23:45Z",
  "device": "iPhone 13 Pro",
  "payment_method": "Credit Card ending in 4521"
}
```

**Processing Steps:**

1. **Anonymization**:
   - User ID → `8f3c2e1a9b4d5f7e` (hashed)
   - Merchant → `electronics` (categorized)
   - Amount → `small ($10-$50)` (bucketed)

2. **Vectorization**:
   - Creates behavioral text description
   - Generates 384-dim embedding vector
   - Stores in LanceDB

3. **Pattern Detection**:
   - Searches for similar transaction vectors
   - Finds 12 similar transactions across 8 days
   - Matches "Card Testing" fraud pattern (89% confidence)

4. **AI Investigation**:
   - LLM analyzes the pattern
   - Detects coordinated low-value purchases
   - Identifies IP cluster anomaly

5. **Risk Scoring**:
   - Rule-based signals: 65/100
   - LLM confidence: 87/100
   - Final score: 79/100 (High Risk)

**Output:**
```json
{
  "fraud_risk_score": 82,
  "risk_level": "High",
  "reasoning": "Behavioral anomaly detected...",
  "recommendations": [
    "Flag USER_5021 for manual review",
    "Temporarily limit transaction amounts",
    "Request additional authentication"
  ]
}
```

## Performance Metrics

- **Embedding Generation**: ~50ms per transaction
- **Vector Search**: ~10ms (top-20 results)
- **LLM Investigation**: ~2-5 seconds
- **Total Processing**: ~3-6 seconds per transaction

## Key Innovations

1. **Behavioral Memory**: Unlike traditional point-in-time analysis, stores and queries behavioral patterns across time
2. **Semantic Similarity**: Finds fraud even when details differ (different merchants, amounts, times)
3. **Privacy-First**: Full anonymization while maintaining detection capability
4. **Explainable AI**: Clear reasoning for every fraud decision
5. **Zero-Cost**: Enterprise-grade detection without enterprise costs

## Getting Started

**1. Quick Setup:**
```bash
chmod +x setup.sh && ./setup.sh
```

**2. Process Samples:**
```bash
python main.py --sample
```

**3. Launch Dashboard:**
```bash
streamlit run dashboard/app.py
```

## Use Cases

- **Banks**: Real-time transaction monitoring
- **E-commerce**: Payment fraud detection
- **Fintech**: Account security
- **Research**: Fraud pattern analysis
- **Education**: AI/ML demonstrations

## Future Enhancements

- [ ] Multi-model ensemble (combine multiple LLMs)
- [ ] Graph analysis (account relationship networks)
- [ ] Real-time streaming pipeline
- [ ] Advanced visualization (network graphs)
- [ ] API rate limiting and authentication
- [ ] Automated model retraining
- [ ] Integration with payment processors

## Contributing

This is an open-source educational project. Contributions welcome:
- Add new fraud patterns
- Improve detection algorithms
- Enhance dashboard features
- Add integration examples

## Resources

- [LanceDB Documentation](https://lancedb.github.io/lancedb/)
- [Ollama Models](https://ollama.ai/library)
- [Sentence Transformers](https://www.sbert.net/)
- [Streamlit Docs](https://docs.streamlit.io/)

## License

MIT License - Free to use, modify, and distribute

---

**Built for the FinGuard Challenge**
Demonstrating that world-class AI fraud detection doesn't require expensive enterprise software.
