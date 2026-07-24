#!/usr/bin/env python3
"""Fetch USITC HTS 'general' (MFN/Column 1) rate data for every chapter that
appears in the 5 net-of-MFN economies' CY2025 import data, via the
hts.usitc.gov getRates endpoint (one call returns the whole 2-digit chapter).

Writes one raw JSON file per chapter to data/source/hts_chapters/<CH>.json.
"""
import json
import os
import sys
import time
import urllib.request
import urllib.error

ROOT = "/home/user/test-repo"
CENSUS_DIR = f"{ROOT}/data/census"
OUT_DIR = f"{ROOT}/data/source/hts_chapters"
os.makedirs(OUT_DIR, exist_ok=True)

ECON_FILES = {
    'European Union': 'European_Union.json',
    'Japan': 'Japan.json',
    'South Korea': 'South_Korea.json',
    'Switzerland': 'Switzerland.json',
    'Taiwan': 'Taiwan.json',
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://hts.usitc.gov/",
}


def get_needed_chapters():
    union = set()
    for fn in ECON_FILES.values():
        d = json.load(open(f"{CENSUS_DIR}/{fn}"))
        union |= set(c for c, v in d.items() if v and v > 0)
    return sorted(set(c[:2] for c in union))


def fetch_chapter(ch, max_retries=5):
    ep = "getRates99" if ch == "99" else "getRates"
    url = f"https://hts.usitc.gov/reststop/{ep}?htsno={ch}&keyword="
    delay = 3
    for attempt in range(1, max_retries + 1):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=60) as resp:
                status = resp.status
                body = resp.read()
            if status != 200:
                raise RuntimeError(f"HTTP {status}")
            data = json.loads(body)
            return data
        except Exception as e:
            print(f"    [ch {ch}] attempt {attempt} error: {e}", file=sys.stderr)
        if attempt < max_retries:
            time.sleep(delay)
            delay *= 2
    raise RuntimeError(f"Failed chapter {ch} after {max_retries} attempts")


def main():
    chapters = get_needed_chapters()
    print(f"{len(chapters)} chapters needed: {chapters}", file=sys.stderr)

    manifest_file = f"{OUT_DIR}/manifest.json"
    manifest = json.load(open(manifest_file)) if os.path.exists(manifest_file) else {}

    for ch in chapters:
        fname = f"{OUT_DIR}/{ch}.json"
        if manifest.get(ch) == "done" and os.path.exists(fname):
            print(f"[skip] chapter {ch} already done", file=sys.stderr)
            continue
        t0 = time.time()
        try:
            data = fetch_chapter(ch)
            with open(fname, "w") as f:
                json.dump(data, f)
            manifest[ch] = "done"
            print(f"[ok] chapter {ch}: {len(data)} rows ({time.time()-t0:.1f}s)", file=sys.stderr)
        except Exception as e:
            manifest[ch] = f"FAILED: {e}"
            print(f"[FAIL] chapter {ch}: {e}", file=sys.stderr)
        with open(manifest_file, "w") as f:
            json.dump(manifest, f, indent=1)
        time.sleep(0.5)

    n_done = sum(1 for v in manifest.values() if v == "done")
    print(f"\n{n_done}/{len(chapters)} chapters done.", file=sys.stderr)


if __name__ == "__main__":
    main()
