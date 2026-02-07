# FinGuard Learner Guide

A beginner-friendly walkthrough of the fraud detection flow, the AI tools and libraries used at each step, and why they matter.

---

## What FinGuard Does (In One Sentence)

FinGuard takes a raw transaction (amount, merchant, device, etc.), converts it into a "behavior fingerprint," compares it with past transactions and known fraud patterns, optionally asks an AI to investigate, and outputs a fraud risk score plus recommendations.

---

## The Big Picture: End-to-End Flow

```
Raw Transaction
      |
      v
[1] INGEST & NORMALIZE   (anonymize, categorize)
      |
      v
[2] VECTORIZE            (text -> numbers)
      |
      v
[3] PATTERN DETECTION    (similarity search)
      |
      v
[4] AI INVESTIGATION     (only if risky)
      |
      v
[5] RISK SCORING        (rules + AI)
      |
      v
[6] STORE & ALERT       (save, recommend)
```

The **UI (Streamlit dashboard)** reads from the stored results and lets you run sample transactions, view flags, and explore analytics. It does not do the AI processing itself; that happens when you run `main.py` or use **Run Sample Transactions** in the System tab.

---

## Step-by-Step: What Happens, What’s Used, and Why

### Step 1: Ingest and Normalize

**What happens:**  
Raw fields (user id, merchant, location, device, payment method, timestamp) are validated, then anonymized and categorized. User IDs are hashed, merchants become categories (e.g. "electronics"), amounts become buckets (e.g. "small $10–50"), and we derive hour/day.

**AI tool/library:**  
None. Uses Python’s **`hashlib`** and simple rule-based logic.

**Why it’s used:**  
- **Privacy:** No raw PII (names, exact IDs) is stored or sent to any model.  
- **Consistency:** Categories and buckets make behavioral patterns comparable across transactions.

**Learning takeaway:**  
AI works better on clean, structured, privacy-safe data. This step is "data prep" before any ML.

---

### Step 2: Vectorize (Embeddings)

**What happens:**  
A short **behavior text** is built from the normalized fields (e.g. "Amount range: small ($10–50), Merchant category: electronics, Device type: mobile, …"). That text is turned into a list of 384 numbers (a **vector**).

**AI tool/library:**  
- **sentence-transformers** (model: `all-MiniLM-L6-v2`).  
- Fallback: a simple **hash-based embedding** if the model can’t be loaded (e.g. offline).

**Why it’s used:**  
- **Semantic similarity:** Sentences with similar meaning get similar vectors. Two "small electronics purchase on mobile" behaviors end up close in number space even if wording differs.  
- **Comparable across time:** We can later ask "which past transactions looked like this one?" by comparing vectors.

**Learning takeaway:**  
**Embeddings** turn text (or other data) into vectors so we can measure "how similar" two things are. Models like MiniLM are small, fast, and run locally.

---

### Step 3: Pattern Detection

**What happens:**  
The new transaction’s vector is used to:  
1. **Search similar past transactions** (last 30 days, top 20).  
2. **Match against known fraud patterns** (e.g. "Card Testing," "Account Takeover") stored as vectors.  
We then compute: how many similar transactions, how many unique users, time span, amount spread, etc., and whether we hit any known fraud pattern.

**AI tool/library:**  
- **LanceDB** (vector database).  
- **PyArrow** for schema and data layout.

**Why it’s used:**  
- **Vector search:** LanceDB quickly finds "nearest" vectors. That’s how we get "similar" transactions and "similar to this fraud pattern" without comparing every pair by hand.  
- **Embedded:** No separate DB server; it runs inside the app and stores under `data/lancedb`.

**Learning takeaway:**  
A **vector database** is built to store and search vectors efficiently. "Similar" usually means nearest in vector space (e.g. cosine similarity or L2 distance).

---

### Step 4: AI Investigation (Conditional)

**What happens:**  
Only if the pattern step says "needs investigation" (e.g. many similar txns, many users, or a fraud-pattern match). We build a **prompt** with transaction details, pattern stats, and risk flags, then send it to an LLM. The LLM returns structured JSON: `is_fraud`, `confidence`, `fraud_type`, `reasoning`, `recommendations`.

**AI tool/library:**  
- **Ollama** (local LLM runtime).  
- **Mistral** (`mistral:latest`) as the model in this project.

**Why it’s used:**  
- **Interpretation:** The LLM plays "expert analyst": it reads the evidence and explains why something looks like fraud or not.  
- **Local and free:** Ollama runs models on your machine; no cloud API keys.  
- **Structured output:** We ask for JSON so we can parse and use the result in code.

**Learning takeaway:**  
**LLMs** can follow instructions and reason over context. Here they’re used as a "decision support" layer, not as the only source of truth. We still combine them with rules.

---

### Step 5: Risk Scoring

**What happens:**  
A **hybrid score** is computed:  
- **40% rule-based:** Points for multiple accounts, many similar txns, time spread, amount clustering, merchant hopping, device switching, fraud-pattern match.  
- **60% AI-based:** The LLM’s `confidence` (or a default when we skip investigation).  
Final score 0–100; we map to Low / Medium / High risk and use it to flag (e.g. score ≥ 70 → flagged).

**AI tool/library:**  
- No new library. Uses **logic in `risk_scoring.py`** plus the **LLM result** from Step 4.

**Why it’s used:**  
- **Balance:** Rules are transparent and stable; the LLM adds flexibility for nuanced cases.  
- **Explainability:** We always have a rule component and LLM reasoning to fall back on.

**Learning takeaway:**  
**Hybrid systems** (rules + ML/LLM) are common in production: rules for clarity and safety, AI for harder judgments.

---

### Step 6: Store and Alert

**What happens:**  
The transaction is stored **with** its fraud score, risk level, and `is_flagged` in LanceDB. We also create an **alert** object (for API or CLI) with reasoning, behavioral summary, and recommendations.

**AI tool/library:**  
- **LanceDB** again (and **PyArrow**): we append the new row to the transactions table.

**Why it’s used:**  
- **Dashboard and history:** The UI reads from LanceDB to show Overview, Transactions, Analytics.  
- **Consistency:** Same vector DB holds both "memory" (past txns) and "results" (scores, flags).

**Learning takeaway:**  
Storing model outputs (scores, flags, reasoning) is what makes the system **auditable** and the UI **useful**.

---

## The UI: What Uses What

| Part of UI | Tool/Library | Why |
|------------|----------------|-----|
| **App framework** | **Streamlit** | Quick dashboards with Python; buttons, tabs, tables, charts. |
| **Charts** | **Plotly** | Interactive plots (e.g. risk distribution, fraud timeline, heatmaps). |
| **Data** | **LanceDB** | All metrics, transaction list, and flags come from tables we write in the pipeline. |
| **Run Sample Transactions** | **main.py** | Runs the full pipeline (ingest → vectorize → detect → LLM → score → store) for built-in sample txns. |

**Note:** We use **Plotly** for charts, not Altair. Altair is not used in this project.

---

## How to Run and Test via the UI

1. **Start the app**  
   - Windows: `start_app.bat`  
   - Mac/Linux: `./start_app.sh`

2. **Open the dashboard**  
   Browser at `http://localhost:8501` (or the port Streamlit prints).

3. **Ensure Ollama + Mistral**  
   `ollama serve` and `ollama pull mistral` (or your configured model).

4. **Generate data**  
   Go to the **System** tab and click **Run Sample Transactions**. This runs the pipeline on sample data and fills LanceDB.

5. **Inspect results**  
   - **Overview:** KPIs, risk distribution, timeline, high-risk list.  
   - **Transactions:** Filter by risk, export CSV.  
   - **Analytics:** Merchant/device breakdown, fraud heatmaps.

6. **Interpret flags**  
   Flagged rows are those with risk score ≥ 70 (or your configured threshold). Details come from pattern detection and, when used, LLM reasoning.

---

## Glossary (Quick Reference)

- **Embedding:** A vector (list of numbers) representing meaning; similar things have similar vectors.  
- **Vector DB:** Database optimized to store and search vectors (e.g. nearest-neighbor).  
- **LLM:** Large language model; generates text (here, structured JSON) from a prompt.  
- **Ollama:** Local runtime to run LLMs (e.g. Mistral, Llama) on your machine.  
- **sentence-transformers:** Library and models to produce embeddings from text.  
- **LanceDB:** Embeddable vector DB used here for transactions and fraud patterns.  
- **Hybrid scoring:** Combining rule-based logic and ML/LLM outputs into one decision.

---

## Summary Table: Steps vs Tools

| Step | Module | AI/Tool | Purpose |
|------|--------|---------|---------|
| 1. Ingest | `ingestion.py` | hashlib, rules | Anonymize, categorize; no AI |
| 2. Vectorize | `vectorization.py` | sentence-transformers (or hash fallback) | Text → 384-d vector |
| 3. Pattern detection | `pattern_detection.py` | LanceDB | Similar txns + fraud-pattern match |
| 4. AI investigation | `investigation.py` | Ollama + Mistral | LLM analyst when risky |
| 5. Risk scoring | `risk_scoring.py` | Rules + LLM result | Hybrid 40% rules, 60% AI |
| 6. Store & alert | `database.py`, `main.py` | LanceDB | Persist scores, flags, alerts |
| UI | `dashboard/app.py` | Streamlit, Plotly, LanceDB | Display and Run Sample Transactions |

---

*This guide is for learning only. It is not committed to the repo.*
