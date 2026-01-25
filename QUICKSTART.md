# FinGuard Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Prerequisites
```bash
# Check Python version (need 3.9+)
python3 --version

# Install Ollama
# Visit: https://ollama.ai
# Or on Mac: brew install ollama
# Or on Linux: curl -fsSL https://ollama.com/install.sh | sh
```

### Step 2: One-Command Setup
```bash
# Make setup script executable and run
chmod +x setup.sh
./setup.sh
```

This will:
- Create virtual environment
- Install all dependencies
- Download Ollama model
- Initialize database

### Step 3: Activate Environment
```bash
source venv/bin/activate
```

### Step 4: Process Sample Transactions
```bash
python main.py --sample
```

You should see output like:
```
========================================================
Processing Transaction: TXN_001
========================================================
📥 Step 1: Ingesting transaction...
   ✅ Normalized and anonymized
🔢 Step 2: Vectorizing behavioral pattern...
   ✅ Generated 384-dim embedding
💾 Step 3: Storing in vector database...
   ✅ Stored in LanceDB
🔍 Step 4: Detecting fraud patterns...
   📊 Similar transactions: 0
   👥 Accounts involved: 0
⏭️  Step 5: Skipping AI investigation (low risk)
📈 Step 6: Calculating fraud risk score...
   🎯 Final Score: 15/100 (Low Risk)
```

### Step 5: Launch Dashboard
```bash
streamlit run dashboard/app.py
```

Your browser will open to `http://localhost:8501`

## 🎯 What to Try

### Test Individual Transaction
```bash
python main.py --transaction '{
  "transaction_id": "TEST_001",
  "user_id": "USER_123",
  "amount": 47.50,
  "merchant": "Online Electronics Store",
  "location": "New York, NY",
  "timestamp": "2026-01-24T14:23:45Z",
  "device": "iPhone 13 Pro",
  "payment_method": "Credit Card ending in 4521"
}'
```

### Process from File
```bash
python main.py --file data/sample_transactions.json
```

### Save Results
```bash
python main.py --sample --output results.json
```

## 📊 Dashboard Features

1. **Overview Tab**: KPIs, risk distribution, fraud timeline
2. **Transactions Tab**: Filter and export transaction data
3. **Analytics Tab**: Merchant analysis, heatmaps
4. **System Tab**: Configuration and health checks

## 🔧 Troubleshooting

### Ollama Not Running
```bash
# Start Ollama service
ollama serve

# In another terminal, verify it's working
ollama list
```

### LanceDB Connection Error
```bash
# Clear and reinitialize
rm -rf data/lancedb/*
python backend/setup_db.py
```

### Memory Issues
If you have limited RAM:
```bash
# Use smaller model
ollama pull llama3.2:latest

# Edit main.py and investigation.py
# Change: model='llama3.3:latest'
# To:     model='llama3.2:latest'
```

## 📚 Next Steps

1. **Customize Fraud Patterns**: Edit `backend/database.py` → `_seed_fraud_patterns()`
2. **Adjust Risk Scoring**: Edit `backend/risk_scoring.py`
3. **Add More Features**: Extend `backend/ingestion.py` with custom fields
4. **Build API**: Use the included FastAPI skeleton

## 🆘 Need Help?

Check the full README.md for:
- Detailed architecture explanation
- API documentation
- Configuration options
- Advanced usage examples

---

**You're all set! Happy fraud detecting! 🛡️**
