#!/usr/bin/env python3
"""Contract validator for semantic-caching trace files (JSONL).

Standard-library ONLY (no jsonschema, pydantic, or PyYAML). The field
contract below is hardcoded as an inline dict and MUST stay in lock-step
with schema/trace_schema.yaml.

Usage:
    python3 validate_trace.py <path-to-trace.jsonl>

Validates, for every record:
  * all required fields are present and non-null,
  * every present field has the correct type,
  * enum-valued fields hold an allowed value,
  * optional fields may be absent or null (nullable handling).

Prints PASS/FAIL per record plus a summary. Exits 0 only if every record
passes; exits 1 on any validation failure or input error.
"""

import json
import sys

# --- Field contract -------------------------------------------------------
# type: a Python type or tuple of types acceptable for the field's value.
#       bool is checked specially so that True/False are NOT accepted where a
#       numeric (int/float) field is expected, and vice versa.
# required: True  -> must be present and non-null.
#           False -> may be omitted or null.
# enum: optional list of allowed values (checked when value is non-null).

# JSON numbers may decode to int (e.g. 0) where a float is expected; we accept
# int for float fields but reject bool (since bool is a subclass of int).
NUMERIC = (int, float)

FIELD_SPEC = {
    # required
    "request_id":           {"type": str,     "required": True},
    "timestamp":            {"type": NUMERIC,  "required": True},
    "prompt_hash":          {"type": str,     "required": True},
    "embedding_model":      {"type": str,     "required": True},
    "similarity_threshold": {"type": NUMERIC,  "required": True},
    "cache_decision":       {"type": str,     "required": True,
                             "enum": ["hit", "miss", "admit"]},
    "latency_ms":           {"type": NUMERIC,  "required": True},
    "model_version":        {"type": str,     "required": True},
    # optional / nullable
    "matched_entry_id":     {"type": str,     "required": False},
    "similarity_score":     {"type": NUMERIC,  "required": False},
    "served_response_id":   {"type": str,     "required": False},
    "verified":             {"type": bool,    "required": False},
    "verification_method":  {"type": str,     "required": False,
                             "enum": ["none", "threshold", "llm_judge",
                                      "conformal"]},
    "is_false_hit":         {"type": bool,    "required": False},
    "cost_usd":             {"type": NUMERIC,  "required": False},
    "corpus_version":       {"type": str,     "required": False},
}


def _type_ok(value, expected):
    """Type check that keeps bool and numeric types from cross-contaminating."""
    if expected is bool:
        return isinstance(value, bool)
    if expected is NUMERIC:
        # accept int/float but NOT bool
        return isinstance(value, NUMERIC) and not isinstance(value, bool)
    if expected is str:
        return isinstance(value, str)
    return isinstance(value, expected)


def validate_record(rec):
    """Return a list of error strings (empty list == valid)."""
    errors = []

    if not isinstance(rec, dict):
        return ["record is not a JSON object"]

    # Unknown fields are tolerated (forward compatibility) but flagged softly.
    for key in rec:
        if key not in FIELD_SPEC:
            errors.append("unknown field '%s'" % key)

    for name, spec in FIELD_SPEC.items():
        present = name in rec
        value = rec.get(name)

        if spec["required"]:
            if not present:
                errors.append("missing required field '%s'" % name)
                continue
            if value is None:
                errors.append("required field '%s' is null" % name)
                continue
        else:
            # optional: absent or null is fine
            if not present or value is None:
                continue

        if not _type_ok(value, spec["type"]):
            errors.append(
                "field '%s' has wrong type: got %s" % (name, type(value).__name__)
            )
            continue

        if "enum" in spec and value not in spec["enum"]:
            errors.append(
                "field '%s' value %r not in %s" % (name, value, spec["enum"])
            )

    return errors


def main(argv):
    if len(argv) != 2:
        sys.stderr.write("usage: python3 validate_trace.py <trace.jsonl>\n")
        return 1

    path = argv[1]
    try:
        fh = open(path, "r", encoding="utf-8")
    except OSError as exc:
        sys.stderr.write("cannot open %s: %s\n" % (path, exc))
        return 1

    total = 0
    passed = 0
    failed = 0

    with fh:
        for lineno, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            total += 1
            try:
                rec = json.loads(line)
            except ValueError as exc:
                failed += 1
                print("FAIL  record %d: invalid JSON: %s" % (lineno, exc))
                continue

            errors = validate_record(rec)
            rid = rec.get("request_id", "?") if isinstance(rec, dict) else "?"
            if errors:
                failed += 1
                print("FAIL  record %d (request_id=%s):" % (lineno, rid))
                for err in errors:
                    print("        - %s" % err)
            else:
                passed += 1
                print("PASS  record %d (request_id=%s)" % (lineno, rid))

    print("-" * 56)
    print("summary: %d record(s), %d passed, %d failed" % (total, passed, failed))

    if total == 0:
        sys.stderr.write("no records found in %s\n" % path)
        return 1
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
