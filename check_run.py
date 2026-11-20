#!/usr/bin/env python3
"""check_run.py: check one scraper run before your agent trusts it.

    python3 check_run.py run.json --expect expect.json
    python3 check_run.py run1.json run2.json --expect expect.json     # keep the fuller run
    python3 check_run.py run.json --expect expect.json --heal-prompt

run.json is what `bdata scraper run <id> <url> --pretty -o run.json` writes: a JSON list of rows.
expect.json says what a complete run looks like:

    {"min_rows": 33,
     "sequence": "rank",
     "fields": {"rank": "int", "product_name": "str", "upvote_count": "int", "topics": "list"}}

It prints one line per problem, each with what to do next, and exits 1 when any check fails,
so the same command gates a cron job, a CI step or the instruction you pin for your agent.
--heal-prompt prints a sentence you can pass to `bdata scraper heal` for the problems it found.

Standard-library Python 3.10+. Read-only. No API key.
"""
import argparse
import json
import re
import sys

TYPES = {"int": int, "float": (int, float), "str": str, "list": list, "dict": dict, "bool": bool}
INT_TEXT = re.compile(r"^-?\d[\d,]*$")
LIST_TEXT = re.compile(r"^\s*\[.*\]\s*$", re.S)


def load_rows(path):
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if isinstance(data, dict):
        data = data.get("data", data.get("results", []))
    if not isinstance(data, list):
        raise SystemExit(f"{path}: expected a JSON list of rows, got {type(data).__name__}")
    return [r for r in data if isinstance(r, dict)]


def check(rows, expect):
    """Return a list of (check, ok, message, heal_clause)."""
    out = []
    n, want = len(rows), expect.get("min_rows")
    if want is not None:
        if n >= want:
            out.append(("rows", True, f"{n} rows, at least the {want} expected", None))
        else:
            out.append(("rows", False,
                        f"{n} of {want} rows. Run it once more; if the count repeats, heal it with a "
                        "sentence that says how the page loads the rest (scroll, pagination, a 'load more' button).",
                        f"returns only {n} of the {want} rows; keep loading the page until the row count stops growing"))
    seq = expect.get("sequence")
    if seq and rows:
        vals = []
        for r in rows:
            v = r.get(seq)
            if isinstance(v, str) and INT_TEXT.match(v):
                v = int(v.replace(",", ""))
            if isinstance(v, int):
                vals.append(v)
        if vals:
            have, top = set(vals), max(max(vals), want or 0)
            gaps = [i for i in range(1, top + 1) if i not in have]
            dupes = sorted({v for v in vals if vals.count(v) > 1})
            if gaps:
                out.append((f"{seq}-gaps", False, f"{seq} missing: {span(gaps)}", None))
            if dupes:
                out.append((f"{seq}-dupes", False, f"{seq} repeated: {span(dupes)}", None))
            if not gaps and not dupes:
                out.append((f"{seq}-gaps", True, f"{seq} runs 1 to {top} with no gaps or repeats", None))
    for field, kind in (expect.get("fields") or {}).items():
        out.extend(check_field(rows, field, kind))
    return out


def check_field(rows, field, kind):
    want = TYPES.get(kind)
    if want is None:
        raise SystemExit(f"unknown type {kind!r} for {field}: use one of {', '.join(TYPES)}")
    missing = sum(1 for r in rows if field not in r)
    empty = sum(1 for r in rows if field in r and r[field] in (None, "", [], {}))
    wrong = [r[field] for r in rows if r.get(field) not in (None, "", [], {}) and not isinstance(r[field], want)]
    res = []
    if missing:
        res.append((field, False, f"{field} absent from {missing} of {len(rows)} rows",
                    f"leaves {field} off some rows; return it on every row"))
    if empty:
        res.append((field, False, f"{field} empty in {empty} of {len(rows)} rows",
                    f"returns {field} empty on some rows; fill it on every row"))
    if wrong:
        sample = wrong[0]
        hint = ""
        if kind in ("int", "float") and isinstance(sample, str) and INT_TEXT.match(sample):
            hint = " (a number stored as text sorts wrong: \"97\" lands above \"363\")"
        if kind == "list" and isinstance(sample, str) and LIST_TEXT.match(sample):
            hint = " (a string that only looks like a list)"
        res.append((field, False,
                    f"{field} is {type(sample).__name__} in {len(wrong)} of {len(rows)} rows, expected {kind}: "
                    f"{json.dumps(sample)[:40]}{hint}",
                    f"returns {field} as {type(sample).__name__}; return it as {'an integer' if kind == 'int' else 'a JSON array' if kind == 'list' else kind}"))
    if not (missing or empty or wrong):
        res.append((field, True, f"{field}: {kind} on every row", None))
    return res


def span(nums):
    """[18, 19, 20, 25] -> '18 to 20, 25'"""
    parts, start = [], None
    for i, v in enumerate(nums):
        if start is None:
            start = v
        if i + 1 == len(nums) or nums[i + 1] != v + 1:
            parts.append(str(start) if start == v else f"{start} to {v}")
            start = None
    return ", ".join(parts)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("runs", nargs="+", help="the JSON one or more scraper runs wrote; with several, the one with the most rows is checked")
    ap.add_argument("--expect", required=True, help="JSON file: min_rows, sequence, fields")
    ap.add_argument("--heal-prompt", action="store_true", help="print a heal sentence for the failures")
    a = ap.parse_args(argv)
    loaded = [(path, load_rows(path)) for path in a.runs]
    path, rows = max(loaded, key=lambda pr: len(pr[1]))
    if len(loaded) > 1:
        print(f"KEPT  {path}: {len(rows)} rows (" + ", ".join(f"{q}: {len(r)}" for q, r in loaded if q != path) + ")\n")
    with open(a.expect, encoding="utf-8") as fh:
        expect = json.load(fh)
    results = check(rows, expect)
    failed = [r for r in results if not r[1]]
    for name, ok, msg, _ in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name:<14} {msg}")
    print(f"\n{'COMPLETE' if not failed else 'INCOMPLETE'}: {len(results) - len(failed)} of {len(results)} checks pass")
    if a.heal_prompt and failed:
        clauses = [c for _, _, _, c in failed if c]
        print("\nheal prompt:\n  " + "The scraper " + "; ".join(clauses) + ".")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
