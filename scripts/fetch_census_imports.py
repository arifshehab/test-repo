#!/usr/bin/env python3
"""Pull CY2025 general-imports value (customs/GEN value, GEN_VAL_YR at MONTH=12
= full-year cumulative) at HS10 detail from the Census International Trade API,
for each of the 60 Section 301 forced-labor-investigation economies.

For the European Union, sums across its 27 member-state CTY_CODEs into one
combined HS10 -> value map, since Census does not have an EU aggregate code.

Writes one JSON file per economy to data/census/<safe_name>.json:
    {"<HS10 code>": <GEN_VAL_YR dollars>, ...}
plus a manifest with fetch status, so a rerun can skip already-done economies.
"""
import json
import os
import sys
import time
import urllib.request
import urllib.error

API_KEY = "9d8262f3277dcdff1ce01e98598b26c0d115cf5f"
BASE = "https://api.census.gov/data/timeseries/intltrade/imports/hs"
YEAR = "2025"
MONTH = "12"  # GEN_VAL_YR at MONTH=12 = full calendar-year cumulative total

ROOT = "/home/user/test-repo"
CODES_FILE = f"{ROOT}/data/source/economy_country_codes.json"
OUT_DIR = f"{ROOT}/data/census"
MANIFEST_FILE = f"{OUT_DIR}/manifest.json"

os.makedirs(OUT_DIR, exist_ok=True)


def safe_name(economy):
    return economy.replace(' ', '_').replace(',', '').replace('ü', 'u')


def fetch_one_country(cty_code, max_retries=5):
    url = (f"{BASE}?get=I_COMMODITY,GEN_VAL_YR&YEAR={YEAR}&MONTH={MONTH}"
           f"&COMM_LVL=HS10&CTY_CODE={cty_code}&key={API_KEY}")
    delay = 2
    for attempt in range(1, max_retries + 1):
        try:
            with urllib.request.urlopen(url, timeout=90) as resp:
                status = resp.status
                body = resp.read()
            if status == 204:
                return {}
            if status != 200:
                raise RuntimeError(f"HTTP {status}")
            data = json.loads(body)
            header = data[0]
            idx_code = header.index('I_COMMODITY')
            idx_val = header.index('GEN_VAL_YR')
            out = {}
            for row in data[1:]:
                code = row[idx_code]
                val = int(row[idx_val]) if row[idx_val] not in (None, '') else 0
                out[code] = out.get(code, 0) + val
            return out
        except urllib.error.HTTPError as e:
            if e.code == 204:
                return {}
            print(f'    HTTPError {e.code} on CTY_CODE={cty_code}, attempt {attempt}', file=sys.stderr)
        except Exception as e:
            print(f'    Error on CTY_CODE={cty_code}, attempt {attempt}: {e}', file=sys.stderr)
        if attempt < max_retries:
            time.sleep(delay)
            delay *= 2
    raise RuntimeError(f"Failed to fetch CTY_CODE={cty_code} after {max_retries} attempts")


def main():
    codes_map = json.load(open(CODES_FILE))
    manifest = {}
    if os.path.exists(MANIFEST_FILE):
        manifest = json.load(open(MANIFEST_FILE))

    economies = list(codes_map.keys())
    only = sys.argv[1:] if len(sys.argv) > 1 else None

    for economy in economies:
        if only and economy not in only:
            continue
        fname = f"{OUT_DIR}/{safe_name(economy)}.json"
        if manifest.get(economy) == 'done' and os.path.exists(fname):
            print(f'[skip] {economy} already done', file=sys.stderr)
            continue

        t0 = time.time()
        cty_codes = codes_map[economy]
        combined = {}
        try:
            for cty in cty_codes:
                part = fetch_one_country(cty)
                for code, val in part.items():
                    combined[code] = combined.get(code, 0) + val
                time.sleep(0.4)
            with open(fname, 'w') as f:
                json.dump(combined, f)
            manifest[economy] = 'done'
            elapsed = time.time() - t0
            total_val = sum(combined.values())
            print(f'[ok] {economy}: {len(combined)} HS10 lines, '
                  f'total ${total_val:,} ({elapsed:.1f}s, {len(cty_codes)} country code(s))',
                  file=sys.stderr)
        except Exception as e:
            manifest[economy] = f'FAILED: {e}'
            print(f'[FAIL] {economy}: {e}', file=sys.stderr)

        with open(MANIFEST_FILE, 'w') as f:
            json.dump(manifest, f, indent=1)

    n_done = sum(1 for v in manifest.values() if v == 'done')
    print(f'\n{n_done}/{len(economies)} economies done.', file=sys.stderr)


if __name__ == '__main__':
    main()
