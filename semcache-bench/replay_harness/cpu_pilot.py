#!/usr/bin/env python3
"""CPU pilot: a toy semantic cache that runs in well under five minutes.

This is a SCALE-DOWN CONTRACT DEMONSTRATOR, NOT a production benchmark. It
exists to prove that the trace schema and validator describe a real,
runnable pipeline: a tiny semantic cache processes a stream of prompts,
makes hit/miss/admit decisions under a cosine-similarity threshold, and
emits a trace (pilot_trace.jsonl) that PASSES validate_trace.py.

Embeddings:
  * First choice  -> sentence-transformers 'all-MiniLM-L6-v2'.
  * Fallback      -> a deterministic, dependency-free stdlib hashing
                     pseudo-embedding, used automatically if torch /
                     sentence-transformers are not importable. The harness
                     therefore ALWAYS runs zero-dependency.

Run:
    python3 cpu_pilot.py
"""

import hashlib
import json
import math
import os
import time

# Threshold tuned for the dependency-free bag-of-tokens fallback embedding, so
# near-duplicate paraphrases (which share most tokens) register as hits while
# genuinely novel prompts miss and are admitted. With the optional
# sentence-transformer backend a higher tau (~0.83) is more appropriate; this
# value keeps the zero-dependency demo behaving as documented in the README.
THRESHOLD = 0.60
EMBED_DIM = 64
OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "pilot_trace.jsonl")
MODEL_VERSION = "toy-svc-pilot-1"

# --- Embedding backend (guarded import) -----------------------------------

def _load_backend():
    """Return (encode_fn, model_name). Falls back to stdlib hashing."""
    try:
        from sentence_transformers import SentenceTransformer  # noqa: F401
        model = SentenceTransformer("all-MiniLM-L6-v2")

        def encode(text):
            vec = model.encode(text, normalize_embeddings=False)
            return [float(x) for x in vec]

        return encode, "all-MiniLM-L6-v2"
    except Exception:  # ImportError, model-download failure, no torch, etc.
        return _stdlib_encode, "stdlib-hash-fallback"


def _stdlib_encode(text):
    """Deterministic pseudo-embedding from token hashing (bag-of-words).

    Each token is hashed into EMBED_DIM buckets with a signed weight, so that
    prompts sharing tokens (paraphrases) land close in cosine space while
    unrelated prompts do not. Purely for the contract demo; no semantics.
    """
    vec = [0.0] * EMBED_DIM
    tokens = "".join(c.lower() if c.isalnum() else " " for c in text).split()
    for tok in tokens:
        h = hashlib.sha256(tok.encode("utf-8")).digest()
        idx = h[0] % EMBED_DIM
        sign = 1.0 if (h[1] & 1) else -1.0
        vec[idx] += sign
    return vec


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


# --- Workload: ~20 cached prompts with near-duplicate paraphrase pairs -----

SEED_PROMPTS = [
    "How do I reset my password?",
    "What is the capital of France?",
    "Convert 10 miles to kilometers.",
    "Explain photosynthesis in simple terms.",
    "What time zone is New York in?",
    "How do I center a div in CSS?",
    "Summarize the plot of Romeo and Juliet.",
    "What is the boiling point of water?",
    "How do I install Python on Windows?",
    "Give me a chocolate chip cookie recipe.",
    "What is the speed of light?",
    "How do I tie a tie?",
    "What is the difference between TCP and UDP?",
    "Translate 'good morning' to Spanish.",
    "How many continents are there?",
    "What is a black hole?",
    "How do I make cold brew coffee?",
    "What does HTTP status 404 mean?",
    "How do I sort a list in Python?",
    "What is the tallest mountain on Earth?",
]

# Query stream: paraphrases (should hit), exact repeats (should hit), and
# genuinely new prompts (should miss -> admit).
QUERY_STREAM = [
    "How can I reset my password?",            # paraphrase of seed 0
    "What's the capital city of France?",       # paraphrase of seed 1
    "Explain photosynthesis simply.",           # paraphrase of seed 3
    "How do I center a div in CSS?",            # exact repeat of seed 5
    "What is the boiling point of water?",      # exact repeat of seed 7
    "How do I install Python on Windows?",      # exact repeat of seed 8
    "What is the price of Bitcoin today?",      # new -> miss/admit
    "Recommend a good science fiction novel.",  # new -> miss/admit
    "How do I sort a list in Python?",          # exact repeat of seed 18
    "What is the highest mountain in the world?",  # paraphrase of seed 19
]


def build_cache(encode):
    cache = []
    for i, prompt in enumerate(SEED_PROMPTS):
        cache.append({
            "entry_id": "ent-%04d" % i,
            "prompt": prompt,
            "embedding": encode(prompt),
            "response_id": "resp-%04d" % i,
        })
    return cache


def prompt_hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def main():
    start = time.time()
    encode, model_name = _load_backend()
    cache = build_cache(encode)

    records = []
    hits = 0
    next_entry = len(SEED_PROMPTS)

    for i, query in enumerate(QUERY_STREAM):
        q_emb = encode(query)
        best_score = -1.0
        best = None
        for entry in cache:
            score = cosine(q_emb, entry["embedding"])
            if score > best_score:
                best_score = score
                best = entry

        ts = time.time()
        base = {
            "request_id": "pilot-%04d" % i,
            "timestamp": round(ts, 3),
            "prompt_hash": prompt_hash(query),
            "embedding_model": model_name,
            "similarity_threshold": THRESHOLD,
            "model_version": MODEL_VERSION,
        }

        if best is not None and best_score >= THRESHOLD:
            hits += 1
            base.update({
                "cache_decision": "hit",
                "latency_ms": round(8.0 + 4.0 * (i % 3), 1),
                "matched_entry_id": best["entry_id"],
                "similarity_score": round(best_score, 4),
                "served_response_id": best["response_id"],
                "verified": False,
                "verification_method": "threshold",
                "is_false_hit": False,
                "cost_usd": 0.0,
                "corpus_version": "pilot-kb-v1",
            })
        else:
            # miss -> generate (simulated) and admit into the cache
            new_id = "ent-%04d" % next_entry
            resp_id = "resp-%04d" % next_entry
            cache.append({
                "entry_id": new_id,
                "prompt": query,
                "embedding": q_emb,
                "response_id": resp_id,
            })
            next_entry += 1
            base.update({
                "cache_decision": "admit",
                "latency_ms": round(650.0 + 30.0 * (i % 4), 1),
                "matched_entry_id": None,
                "similarity_score": (round(best_score, 4)
                                     if best_score >= 0 else None),
                "served_response_id": resp_id,
                "verified": False,
                "verification_method": "none",
                "is_false_hit": None,
                "cost_usd": round(0.0025 + 0.0005 * (i % 3), 4),
                "corpus_version": "pilot-kb-v1",
            })

        records.append(base)

    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec) + "\n")

    # Aggregation uses (r.get(f) or 0) so that null optional fields are safe.
    total_cost = sum((r.get("cost_usd") or 0) for r in records)
    total_latency = sum((r.get("latency_ms") or 0) for r in records)
    n = len(records)
    hit_rate = hits / n if n else 0.0
    elapsed = time.time() - start

    print("embedding backend : %s" % model_name)
    print("requests          : %d" % n)
    print("hits              : %d" % hits)
    print("hit rate          : %.1f%%" % (100.0 * hit_rate))
    print("total cost (usd)  : %.4f" % total_cost)
    print("avg latency (ms)  : %.1f" % (total_latency / n if n else 0.0))
    print("trace written to  : %s" % OUT_PATH)
    print("elapsed (s)       : %.2f" % elapsed)
    print("")
    print("NOTE: scale-down contract demonstrator, not a production benchmark.")


if __name__ == "__main__":
    main()
