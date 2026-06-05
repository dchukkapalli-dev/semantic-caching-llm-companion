# Companion Artifact — Semantic Caching and Response Reuse for Large Language Model Services: A Survey

Machine-readable companion for the survey *"Semantic Caching and Response Reuse
for Large Language Model Services: A Survey."* It backs the manuscript's Data Availability statement,
evaluation section, and Contribution 5 with **runnable** artifacts.

**Deposit.** Permanently archived on Zenodo under the concept DOI
[10.5281/zenodo.20551823](https://doi.org/10.5281/zenodo.20551823) (always resolves to
the latest version; v1.0.0 specifically:
[10.5281/zenodo.20551824](https://doi.org/10.5281/zenodo.20551824)). Source mirror at
<https://github.com/dchukkapalli-dev/semantic-caching-llm-companion>.

## What this IS

- A **contract-validation harness** for the survey's proposed semantic-cache
  benchmark **trace schema**, in `semcache-bench/`: a documented schema
  (`semcache-bench/schema/trace_schema.yaml`), a conformant example trace, and a
  stdlib-only validator (`semcache-bench/validate_trace.py`).
- The **systematic-search log** (`search_log.csv`) and the **evidence matrix**
  (`evidence_matrix.csv`) underpinning the survey's taxonomy and PRISMA funnel.
- A **scale-down CPU pilot** (`semcache-bench/replay_harness/cpu_pilot.py`) that
  exercises the schema end to end on a toy corpus and emits a conformant trace.

## What this IS NOT

- It is **not** a production semantic-cache benchmark, nor a performance
  leaderboard. The CPU pilot uses a toy ~20-prompt corpus and (by default) a
  hashing pseudo-embedding; its numbers are illustrative only.
- It is **not** a reference cache implementation. It validates that a trace
  honors the proposed schema contract — the contribution is the *contract*, and
  the proof that the contract is concrete and checkable.

## File tree

```
companion/
  README.md                 # this file
  LICENSE                   # MIT (covers code)
  CITATION.cff              # CFF 1.2.0 metadata
  search_log.csv            # systematic-search log (6 databases)
  evidence_matrix.csv       # one row per surveyed work (21 works)
  semcache-bench/           # the runnable contract-validation harness
    README.md               # harness overview + quick-start
    validate_trace.py       # stdlib-only contract validator
    schema/
      trace_schema.yaml     # proposed benchmark trace schema (plain YAML)
      example_trace.jsonl   # >=3 conformant records, >=2 validation methods
    replay_harness/
      cpu_pilot.py          # toy CPU semantic cache; emits pilot_trace.jsonl
      requirements.txt      # optional torch + sentence-transformers pins
      README.md             # scale-down framing + run instructions
```

## Data / schema notes

**`evidence_matrix.csv` is a superset of the manuscript's Table 1.** It carries
**21 data rows**: the ~15 *dedicated* semantic-cache systems shown in the typeset
table, **plus** the directly-adjacent prefix/KV-cache and foundation systems
(`cachegen24`, `promptcache_sys24`, `sglang24`, `cachedattention24`,
`mooncake24`, `paged_attention23`) that the survey uses only to delineate the
reuse stack. The 21-vs-15 row count is therefore by design.

**Symbol mapping (CSV ↔ rendered table).** The CSV encodes the table's
`correctness_guarantee`, `distributed`, and `security_aware` columns as the text
values `yes` / `partial` / `no`, mapping to the table's `●` / `○` / `---`
symbols respectively; an em dash (`—`) marks a not-applicable cell (the
attack-paper row `keycollision26`), distinct from `no`. This lets the CSV be
checked mechanically against the typeset table.

**`search_log.csv` and the PRISMA funnel.** `search_log.csv` is the per-database
breakdown behind the "Identification" count of the manuscript's PRISMA funnel
(§Methodology, ~240 identified → 76 included): summing the per-database `n_hits`
(before cross-database dedup) yields the identification total, and
`n_after_screen` feeds the screening stage. All counts are post-deduplication
estimates (flagged in each row's `notes`), reported for auditability rather than
as exact recall figures, consistent with the survey's scope-survey positioning.

## Three-command laptop quick-start

```bash
cd semcache-bench

# 1. Validate the shipped example trace against the schema contract
python3 validate_trace.py schema/example_trace.jsonl

# 2. Run the zero-dependency CPU pilot (emits replay_harness/pilot_trace.jsonl)
python3 replay_harness/cpu_pilot.py

# 3. Validate the pilot's freshly emitted trace
python3 validate_trace.py replay_harness/pilot_trace.jsonl
```

All three exit 0 with no third-party packages installed (the pilot falls back to
a deterministic stdlib pseudo-embedding when `sentence-transformers` is absent).

## License

- **Code** (`semcache-bench/validate_trace.py`, `semcache-bench/replay_harness/`)
  is licensed **MIT** — see `LICENSE`.
- **Data / CSVs** (`search_log.csv`, `evidence_matrix.csv`) and the schema /
  example trace are released under **CC-BY-4.0**
  (<https://creativecommons.org/licenses/by/4.0/>). Reuse with attribution to
  the authors listed in `CITATION.cff`.
