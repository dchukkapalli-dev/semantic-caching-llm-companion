# Data Availability

The machine-readable companion artifacts are released in the paper's `companion/`
directory: the full evidence matrix as a CSV (`evidence_matrix.csv`), the trace
schema for the reference benchmark (Evaluation section), the contract validator that
checks logged accept/reject decisions and realized false-hit rate against a claimed
bound, a CPU-only pilot that runs the end-to-end embed/match/verify/score pipeline
on a small public trace, and a labeled operating-point evaluation
(`eval/labeled_frontier.py`) that reproduces the measured frontier of Table 3 from
the public MRPC corpus. The CSV is a *superset* of Table 2 (21 rows: the ≈15
dedicated semantic-cache systems in the table plus the directly-adjacent
prefix/KV-cache and foundation systems of the Background section), with the
symbol-to-text encoding documented in `companion/README.md`. Together these let the
taxonomy coding be audited and any bounded-error claim be reproduced without
specialized hardware. The companion is permanently archived on Zenodo under the
concept DOI [10.5281/zenodo.20551823](https://doi.org/10.5281/zenodo.20551823)
(which always resolves to the latest version; this paper corresponds to v1.0.0,
[10.5281/zenodo.20551824](https://doi.org/10.5281/zenodo.20551824)), with the code
released under the MIT license, the data and schema under CC-BY-4.0, and a source
mirror at <https://github.com/dchukkapalli-dev/semantic-caching-llm-companion>.
