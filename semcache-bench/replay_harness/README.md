# Replay Harness — CPU Pilot

A **scale-down contract demonstrator**, not a production benchmark. `cpu_pilot.py`
runs a toy ~20-prompt in-memory semantic cache on CPU in well under five
minutes and emits a trace that passes the schema contract validator.

## What it does

1. Builds an in-memory cache from ~20 seed prompts.
2. Replays a short query stream containing near-duplicate paraphrases (expected
   cache **hits**), exact repeats (**hits**), and novel queries (**miss → admit**).
3. Scores each query against the cache with cosine similarity over embeddings,
   applies the admission threshold, and records one schema-conformant event per
   query.
4. Writes `pilot_trace.jsonl` and prints the hit rate.

## Embedding backend (zero-dependency fallback)

The pilot first tries to load sentence-transformers `all-MiniLM-L6-v2`. If
`torch` / `sentence-transformers` are not installed (or the model cannot be
fetched), it **transparently falls back** to a deterministic stdlib hashing
pseudo-embedding. Either way the pilot runs to completion — **no third-party
packages are required.** The `embedding_model` field in the emitted trace
records which backend was used (`all-MiniLM-L6-v2` or `hashfallback-v1`).

## Run

```bash
# zero-dependency mode (fallback embeddings):
python3 cpu_pilot.py

# optional real-embedding mode:
pip install -r requirements.txt
python3 cpu_pilot.py
```

## Expected output shape

```
embedding backend : hashfallback-v1
queries processed : 8
cache hits        : <n>
hit rate          : <pct>%
avg latency_ms    : <ms>
wall time         : <s>s
trace written     : .../replay_harness/pilot_trace.jsonl
NOTE: This is a scale-down CONTRACT DEMONSTRATOR ...
```

## Verify the emitted trace conforms

```bash
cd ..
python3 validate_trace.py replay_harness/pilot_trace.jsonl   # exits 0, all PASS
```
