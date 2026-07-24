#!/usr/bin/env python3
"""Parse fetched HTS chapter JSON into a flat HS10 -> MFN (Column 1 General)
rate map, resolving the standard HTS hierarchical rate inheritance (the
printed rate lives on the legal 8-digit line; 10-digit statistical suffixes
below it are blank and inherit that rate).

Classifies each resolved rate as:
  - "free"                -> 0.0%
  - "percent"             -> ad valorem %, e.g. "4.5%"
  - "specific_or_compound"-> not a clean %, e.g. "1c/kg" or "1.5c/kg + 5%"
  - "unresolved"           -> no rate found anywhere up the ancestor chain

Writes data/source/mfn_rate_map.json: {hs10: {desc, raw, rate_type, rate_pct}}
"""
import json
import re
import glob

CH_DIR = "/home/user/test-repo/data/source/hts_chapters"
OUT_FILE = "/home/user/test-repo/data/source/mfn_rate_map.json"


def strip_html(s):
    if not s:
        return s
    s = re.sub(r"<[^>]+>", "", s)
    return s.strip()


def strip_footnote_marker(s):
    # trailing footnote refs like " 1/", " 2/" left after tag stripping
    if not s:
        return s
    return re.sub(r"\s+\d+/\s*$", "", s).strip()


def classify(raw):
    """raw: HTML-stripped, footnote-stripped general-rate text (or None)."""
    if raw is None or raw == "":
        return "unresolved", None
    s = raw.strip()
    if s.lower() == "free":
        return "free", 0.0
    m = re.fullmatch(r"(\d+(?:\.\d+)?)\s*%", s)
    if m:
        return "percent", float(m.group(1))
    return "specific_or_compound", None


def main():
    rate_map = {}
    stats = {"free": 0, "percent": 0, "specific_or_compound": 0, "unresolved": 0}
    unresolved_examples = []
    compound_examples = []

    for fn in sorted(glob.glob(f"{CH_DIR}/*.json")):
        if fn.endswith("manifest.json"):
            continue
        rows = json.load(open(fn))
        # stack[indent] = resolved raw rate string (cleaned) at that indent level
        stack = {}
        for row in rows:
            indent = row.get("indent")
            try:
                indent = int(indent)
            except (TypeError, ValueError):
                continue
            own_raw = strip_footnote_marker(strip_html(row.get("general")))
            if own_raw:
                stack[indent] = own_raw
                # clear deeper levels; a new rate at this indent supersedes old children context
                for k in list(stack.keys()):
                    if k > indent:
                        del stack[k]
            htsno = row.get("htsno")
            if not htsno:
                continue
            code = htsno.replace(".", "")
            if len(code) != 10:
                continue
            resolved = own_raw
            if not resolved:
                # walk up ancestor indents
                for anc in range(indent - 1, -1, -1):
                    if anc in stack:
                        resolved = stack[anc]
                        break
            rate_type, rate_pct = classify(resolved)
            stats[rate_type] += 1
            if rate_type == "unresolved" and len(unresolved_examples) < 10:
                unresolved_examples.append((code, row.get("description")))
            if rate_type == "specific_or_compound" and len(compound_examples) < 10:
                compound_examples.append((code, resolved))
            rate_map[code] = {
                "desc": row.get("description"),
                "raw": resolved,
                "rate_type": rate_type,
                "rate_pct": rate_pct,
            }

    json.dump(rate_map, open(OUT_FILE, "w"))
    print("stats:", stats)
    print("unresolved examples:", unresolved_examples)
    print("compound examples:", compound_examples)
    print("total HS10 codes mapped:", len(rate_map))


if __name__ == "__main__":
    main()
