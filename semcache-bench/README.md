# semcache-bench — contract-validation harness

Reference contract-validation harness for the semantic-cache benchmark trace
schema proposed in the survey *"Semantic Caching and Response Reuse for LLM
Services"* (§Evaluation). This subdirectory is the runnable harness scaffold; the
parent `companion/` holds the survey-level artifacts (evidence matrix, search
log, license, citation).

## What this IS

- A documented **trace schema** (`schema/trace_schema.yaml`) defining the
  fields a conforming semantic-cache evaluation must log, with a conformant
  example (`schema/example_trace.jsonl`).
- A **stdlib-only validator** (`validate_trace.py`) that checks a JSONL trace
  against the schema contract (required fields, types, enums, nullability).
- A **scale-down CPU pilot** (`replay_harness/cpu_pilot.py`) that runs a toy
  semantic cache end to end and emits a conforming trace.

## What this IS NOT

- Not a production benchmark or performance leaderboard. The pilot uses a toy
  ~20-prompt corpus and, by default, a deterministic stdlib hashing
  pseudo-embedding; its numbers are illustrative only. The contribution is the
  *contract* and the proof that it is concrete and checkable.

## File layout

```
semcache-bench/
  README.md                     # this file
  validate_trace.py             # stdlib-only contract validator
  schema/
    trace_schema.yaml           # proposed benchmark trace schema (plain YAML)
    example_trace.jsonl         # conformant example records (>=2 validation methods)
  replay_harness/
    cpu_pilot.py                # toy CPU semantic cache; emits pilot_trace.jsonl
    requirements.txt            # optional torch + sentence-transformers pins
    README.md                   # scale-down framing + run instructions
```

## Three-command laptop quick-start

```bash
# from companion/semcache-bench/
python3 validate_trace.py schema/example_trace.jsonl
python3 replay_harness/cpu_pilot.py
python3 validate_trace.py replay_harness/pilot_trace.jsonl
```

All three exit 0 with no third-party packages installed (the pilot falls back to
a deterministic stdlib pseudo-embedding when `sentence-transformers` is absent).

## License

Code is MIT; the schema and example trace are CC-BY-4.0. See `../LICENSE` and
`../CITATION.cff`.
