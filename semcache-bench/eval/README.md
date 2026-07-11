# Labeled operating-point frontier (illustrative pilot)

`labeled_frontier.py` reproduces the measured (h, ε) frontier reported in the
paper (Table: "Measured labeled operating-point frontier on MRPC"). It is an
**illustrative single-encoder pilot on a public paraphrase proxy — not a
competitive benchmark of the surveyed systems.** Every number is measured; the
script has no synthetic-score fallback.

## What it computes

It instantiates the paper's operating-point definition directly. Each labeled
paraphrase pair `(s1, s2, label)` is treated as one cache decision: `s1` is the
stored prompt, `s2` the incoming query. With a sentence encoder `φ` and cosine
similarity,

- **hit** when `cos(φ(s1), φ(s2)) ≥ τ`
- **false hit** when a hit is accepted but the pair is *not* a paraphrase
  (`label == 0`) — i.e. reusing `s1`'s response for `s2` would be unacceptable.

Then `h(τ) = P(σ ≥ τ)` and `ε(τ) = P(label == 0 | σ ≥ τ)`, swept over τ. The
script also checks whether `h` and `ε` are monotone non-increasing in τ, the
empirical content of the monotonicity proposition.

## Data

Microsoft Research Paraphrase Corpus (MRPC), a public TSV whose first column is
the binary `Quality` (paraphrase) label. The corpus is **not redistributed
here**; download it, e.g.:

```
curl -sL -o msr_paraphrase_train.txt \
  https://raw.githubusercontent.com/wasiahmad/paraphrase_identification/master/dataset/msr-paraphrase-corpus/msr_paraphrase_train.txt
```

## Run

```
python -m pip install -r requirements.txt
python labeled_frontier.py --data msr_paraphrase_train.txt
```

Default encoder is `model2vec` (`minishlab/potion-base-8M`, static distilled
embeddings, CPU, no torch). Use `--backend sentence-transformers` (requires an
extra `pip install sentence-transformers`) to run with `all-MiniLM-L6-v2`
instead. Each run writes the τ-sweep to `--out` (default
`labeled_frontier.csv`) and the matched-hit-rate operating points to
`<out>_matched.csv`. The `_matched` file is the **encoder-comparable** view:
because cosine scales differ across encoders, comparing false-hit rate at a
fixed `h` (not a fixed τ) is the meaningful cross-encoder comparison. Running
both encoders and comparing their `_matched` CSVs reproduces the paper's
two-encoder table (the frontiers cross — neither encoder is uniformly best).

## Scope / honesty note

This pilot demonstrates that the operating point `(h, ε)` is a real,
reproducible measurement and that the monotonicity proposition holds for this
encoder and corpus. It does **not** evaluate GPTCache/vCache/Krites/etc., does
not sweep encoders or workloads, and does not exercise verification or
model/corpus updates. A multi-system, multi-workload comparison on production
traces (with verification and updates in the loop) is the benchmark agenda of
the paper's open-problem list, not a claim made here.
