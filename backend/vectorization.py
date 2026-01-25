"""
Transaction Vectorization Module
Converts transactions into semantic embeddings
"""

from sentence_transformers import SentenceTransformer
import numpy as np
import hashlib
import re
from typing import Dict, List

# Global model instance (lazy loaded)
_model = None

def _fallback_hash_embedding(text: str, dim: int = 384) -> List[float]:
    """
    Offline-safe embedding fallback.

    Uses a simple feature-hashing style bag-of-tokens embedding so the system can
    still run (and similarity search still works) without downloading models from
    Hugging Face at runtime.
    """
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    vec = np.zeros(dim, dtype=np.float32)

    for tok in tokens:
        digest = hashlib.sha256(tok.encode("utf-8")).digest()
        idx = int.from_bytes(digest[:2], "little") % dim
        sign = 1.0 if (digest[2] % 2 == 0) else -1.0
        vec[idx] += sign

    norm = float(np.linalg.norm(vec))
    if norm > 0:
        vec /= norm

    return vec.astype(np.float32).tolist()

def get_model():
    """Lazy load embedding model (cached)"""
    global _model
    if _model is None:
        try:
            print("Loading sentence-transformers model...")
            _model = SentenceTransformer('all-MiniLM-L6-v2')
            print("Embedding model loaded")
        except Exception as e:
            # Keep the system functional even if the model cannot be downloaded
            # (offline environments, locked-down networks, proxy issues).
            print(f"Warning: embedding model unavailable, using fallback embeddings. ({e})")
            _model = None
    return _model

def get_amount_bucket(amount: float) -> str:
    """
    Bucket amounts for privacy
    Prevents exact amount leakage in embeddings
    """
    if amount < 10:
        return "micro (under $10)"
    elif amount < 50:
        return "small ($10-$50)"
    elif amount < 200:
        return "medium ($50-$200)"
    elif amount < 1000:
        return "large ($200-$1000)"
    else:
        return "very large (over $1000)"

def create_behavior_text(transaction: Dict) -> str:
    """
    Create privacy-preserving behavioral description
    
    IMPORTANT: No PII included - only behavioral patterns
    This text will be embedded and stored in vector DB
    """
    
    # Bucket amount for privacy
    amount_bucket = get_amount_bucket(transaction['amount'])
    
    # Create natural language description of behavior
    behavior_text = f"""
Transaction behavioral pattern:
Amount range: {amount_bucket}
Merchant category: {transaction['merchant_category']}
Location type: {transaction['location_city']}
Device type: {transaction['device_type']}
Payment method: {transaction['payment_method_type']}
Time of day: {transaction['hour_of_day']} hour
Day of week: {transaction['day_of_week']}
    """.strip()
    
    return behavior_text

def get_embedding(text: str) -> List[float]:
    """
    Generate embedding vector from text
    Returns 384-dimensional vector
    """
    model = get_model()
    if model is None:
        return _fallback_hash_embedding(text, dim=384)

    try:
        vector = model.encode(text, convert_to_numpy=True)
        return vector.tolist()
    except Exception as e:
        print(f"Warning: embedding generation failed, using fallback embeddings. ({e})")
        return _fallback_hash_embedding(text, dim=384)

def vectorize_transaction(transaction: Dict) -> Dict:
    """
    Add behavioral text and vector embedding to transaction
    
    Args:
        transaction: Dict with transaction data
    
    Returns:
        Dict with added 'behavior_text' and 'vector' fields
    """
    
    # Create behavioral description
    behavior_text = create_behavior_text(transaction)
    
    # Generate embedding
    vector = get_embedding(behavior_text)
    
    # Add to transaction
    transaction['behavior_text'] = behavior_text
    transaction['vector'] = vector
    
    return transaction

def batch_vectorize(transactions: List[Dict]) -> List[Dict]:
    """
    Vectorize multiple transactions efficiently
    """
    model = get_model()
    
    # Create all behavior texts
    behavior_texts = [create_behavior_text(txn) for txn in transactions]
    
    # Batch encode (faster than individual)
    vectors = model.encode(behavior_texts, convert_to_numpy=True, show_progress_bar=True)
    
    # Add to transactions
    for i, txn in enumerate(transactions):
        txn['behavior_text'] = behavior_texts[i]
        txn['vector'] = vectors[i].tolist()
    
    return transactions

def calculate_similarity(vector1: List[float], vector2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors
    Returns value between 0 and 1 (1 = identical)
    """
    v1 = np.array(vector1)
    v2 = np.array(vector2)
    
    # Cosine similarity
    similarity = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
    
    return float(similarity)
