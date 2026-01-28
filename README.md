# FinGuard - Behavioral Fraud Detection System

A zero-cost, privacy-first AI fraud detection system using LanceDB vector database and Ollama LLM for behavioral pattern recognition.

## Key Features

- **Behavioral Vectorization**: Converts transactions into semantic embeddings (no PII).
- **Pattern Detection**: Identifies complex fraud patterns (Card Testing, Account Takeover) across time.
- **AI Investigation**: Local LLM (Ollama) acts as a forensic investigator to analyze risks.
- **Real-time Dashboard**: Interactive monitoring interface.
- **Privacy-First**: Hashed IDs and generalized data; no raw PII is stored or processed.

## Tech Stack

- **Vector DB**: LanceDB (Serverless, embedded)
- **AI/LLM**: Ollama (Mistral/Llama), sentence-transformers
- **Interface**: Streamlit
- **Backend**: Python

## Quick Start

### Prerequisites
1. **Python 3.9+**
2. **Ollama** installed and running (`ollama serve`)
3. Pull the model: `ollama pull mistral` (or your configured model)

### Run the App

**Windows:**
Double-click `start_app.bat`

**Mac/Linux:**
```bash
chmod +x start_app.sh
./start_app.sh
```

These scripts automatically set up the environment, install dependencies, initialize the database, and launch the dashboard.

**Tip:** In the UI, go to the **System** tab and click **Run Sample Transactions** to populate the dashboard with test data.

## Manual Usage

If you prefer running components manually:

```bash
# Process sample transactions
python main.py --sample

# Run Dashboard
streamlit run dashboard/app.py
```

### Windows note (virtualenv)
If you installed dependencies into the `venv`, run:

```powershell
.\venv\Scripts\python main.py --sample
```

## Project Structure

- `backend/`: Core logic (Vectorization, Detection, Investigation)
- `dashboard/`: Streamlit UI application
- `data/`: LanceDB storage and samples
- `config/`: System configuration (`config.yaml`)

## Configuration

Edit `config/config.yaml` to customize models, thresholds, and risk weights.

```yaml
llm:
  model: "mistral:latest"  # or llama3.3
detection:
  similarity_threshold: 0.75
```

---
**Built for the FinGuard Challenge** | 100% Free & Open Source Tools
