#!/usr/bin/env python3
"""Labeled (h, epsilon) frontier pilot for semantic caching.

Instantiates Definition 1 (operating point) and empirically tests Proposition 1
(monotonicity) on a PUBLIC labeled paraphrase corpus. Each pair (s1, s2, label)
is treated as one cache decision: s1 is the cached prompt, s2 the incoming
query; a HIT occurs when cos(emb(s1), emb(s2)) >= tau, and a hit is a FALSE HIT
when the pair is not a paraphrase (label 0), i.e. reusing s1's response for s2
would be unacceptable. Then:

    h(tau)   = P(sigma >= tau)                 # hit rate
    eps(tau) = P(label == 0 | sigma >= tau)    # false-hit rate

This is an ILLUSTRATIVE single-encoder pilot on public data, NOT a competitive
benchmark of the surveyed systems. Every number is measured, never simulated;
there is no synthetic-score fallback.

Data:    MRPC (Microsoft Research Paraphrase Corpus), TSV with a leading
         "Quality" label column. Public.
Encoder: model2vec (default, static distilled embeddings, CPU, no torch);
         falls back to sentence-transformers all-MiniLM-L6-v2 if requested.

Run:
    python labeled_frontier.py --data msr_paraphrase_train.txt
"""
import argparse
import csv
import math
import os

import numpy as np


def load_mrpc(path):
    rows = []
    with open(path, encoding="utf-8-sig") as fh:
        reader = csv.reader(fh, delimiter="\t", quoting=csv.QUOTE_NONE)
        next(reader, None)  # header: Quality #1ID #2ID #1String #2String
        for r in reader:
            if len(r) < 5:
                continue
            try:
                label = int(r[0].strip())
            except ValueError:
                continue
            rows.append((r[3], r[4], label))
    return rows


def get_encoder(name, backend):
    if backend == "sentence-transformers":
        from sentence_transformers import SentenceTransformer
        m = SentenceTransformer("all-MiniLM-L6-v2")
        return (lambda t: np.asarray(m.encode(t), dtype=np.float64)), \
               "sentence-transformers:all-MiniLM-L6-v2"
    from model2vec import StaticModel
    m = StaticModel.from_pretrained(name)
    return (lambda t: np.asarray(m.encode(t), dtype=np.float64)), \
           "model2vec:" + name


def cos_rows(a, b):
    a = a / (np.linalg.norm(a, axis=1, keepdims=True) + 1e-12)
    b = b / (np.linalg.norm(b, axis=1, keepdims=True) + 1e-12)
    return np.sum(a * b, axis=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="MRPC TSV path")
    ap.add_argument("--model", default="minishlab/potion-base-8M")
    ap.add_argument("--backend", default="model2vec",
                    choices=["model2vec", "sentence-transformers"])
    ap.add_argument("--out", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "labeled_frontier.csv"))
    args = ap.parse_args()

    rows = load_mrpc(args.data)
    s1 = [r[0] for r in rows]
    s2 = [r[1] for r in rows]
    y = np.array([r[2] for r in rows])  # 1 = paraphrase (acceptable reuse)

    enc, enc_name = get_encoder(args.model, args.backend)
    sims = cos_rows(enc(s1), enc(s2))

    n = len(y)
    base = float(y.mean())
    taus = [round(0.50 + 0.05 * k, 2) for k in range(0, 10)]  # 0.50..0.95

    print("encoder=%s  N=%d  paraphrase_base_rate=%.3f" % (enc_name, n, base))
    print("%5s %7s %8s %10s" % ("tau", "hits", "h(tau)", "eps(tau)"))
    table, prev_h, prev_e, mono_h, mono_e = [], None, None, True, True
    for t in taus:
        hit = sims >= t
        nh = int(hit.sum())
        h = nh / n
        eps = float((y[hit] == 0).mean()) if nh > 0 else float("nan")
        table.append((t, nh, h, eps))
        print("%5.2f %7d %8.3f %10.3f" % (t, nh, h, eps))
        if prev_h is not None and h > prev_h + 1e-9:
            mono_h = False
        if (prev_e is not None and not math.isnan(eps)
                and not math.isnan(prev_e) and eps > prev_e + 1e-9):
            mono_e = False
        prev_h, prev_e = h, eps

    print("Proposition 1 check -> h non-increasing: %s | eps non-increasing: %s"
          % (mono_h, mono_e))

    # Matched hit-rate operating points. Fixing h (not tau) makes the false-hit
    # rate comparable ACROSS encoders, since cosine scales differ per encoder.
    print("%9s %7s %10s" % ("h_target", "tau", "eps"))
    matched = []
    for h_star in (0.80, 0.60, 0.40, 0.20):
        tau_star = float(np.quantile(sims, 1.0 - h_star))
        hit = sims >= tau_star
        eps = float((y[hit] == 0).mean()) if int(hit.sum()) > 0 else float("nan")
        matched.append((h_star, tau_star, float(hit.mean()), eps))
        print("%9.2f %7.3f %10.4f" % (h_star, tau_star, eps))
    m_out = args.out.replace(".csv", "") + "_matched.csv"
    with open(m_out, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["h_target", "tau", "hit_rate_h", "false_hit_rate_eps"])
        for hs, t, h, eps in matched:
            w.writerow([hs, "%.4f" % t, "%.4f" % h, "%.4f" % eps])
    print("wrote", m_out)

    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["tau", "n_hits", "hit_rate_h", "false_hit_rate_eps"])
        for t, nh, h, eps in table:
            w.writerow([t, nh, "%.4f" % h, "%.4f" % eps])
    print("wrote", args.out)


if __name__ == "__main__":
    main()
