#!/usr/bin/env python3
"""For each of the 60 investigated economies, compute:
  - total CY2025 general-imports (customs) value
  - value of that covered by the "old" (June 2, 2026 proposed) exemption list
  - value of that covered by the "new" (July 23, 2026 final) exemption list

Matching is hierarchical: an 8-digit exempt HTSUS code covers every 10-digit
Census commodity code sharing that 8-digit prefix; a 10-digit exempt code
covers only that exact 10-digit line (Census data is already at HS10, its
finest grain, so a 10-digit exemption cannot cover anything more specific).

"New" per economy = July Annex II Part A (universal) PLUS that economy's
own country/bloc-specific supplemental Part (B-O), where one exists -- e.g.
the United Kingdom's new exempt set is Part A union Part B. "Old" has no
such per-economy layer: June's Annex A was universal-only, no country
carve-outs existed yet, so every economy's "old" set is just Annex A.
"""
import json
import csv

ROOT = '/home/user/test-repo'


def norm(code):
    return code.replace('.', '')


def load_code_set(path):
    rows = json.load(open(path))
    codes = set()
    for r in rows:
        c = norm(r['code'])
        codes.add(c)
    return codes


def split_by_length(codes):
    """Return (set of 8-digit codes, set of 10-digit codes)."""
    c8 = {c for c in codes if len(c) == 8}
    c10 = {c for c in codes if len(c) == 10}
    other = [c for c in codes if len(c) not in (8, 10)]
    if other:
        print(f'WARNING: unexpected code lengths: {other[:10]}')
    return c8, c10


def exempt_value(hs10_values, c8, c10):
    total_exempt = 0
    for code, val in hs10_values.items():
        if code[:8] in c8 or code in c10:
            total_exempt += val
    return total_exempt


# ---- Load exemption code sets ----
OLD_ALL = load_code_set(f'{ROOT}/data/source/june_annexA_raw.json')
NEW_PART_A = load_code_set(f'{ROOT}/data/source/july_partA_raw.json')
OLD_8, OLD_10 = split_by_length(OLD_ALL)
NEWA_8, NEWA_10 = split_by_length(NEW_PART_A)

PART_LETTER_BY_ECONOMY = {
    'United Kingdom': ['B'],
    'European Union': ['C'],
    'Switzerland': ['D'],
    'Malaysia': ['E'],
    'Cambodia': ['F'],
    'Guatemala': ['G', 'O'],
    'El Salvador': ['H', 'O'],
    'Argentina': ['I'],
    'Bangladesh': ['J'],
    'Taiwan': ['K'],
    'Indonesia': ['L'],
    'Ecuador': ['M'],
    'Jordan': ['N', 'O'],
}

part_code_sets = {}
for letter in 'BCDEFGHIJKLMNO':
    part_code_sets[letter] = load_code_set(f'{ROOT}/data/source/parts/part_{letter}.json')

# ---- Load rate table + country codes ----
rates = json.load(open(f'{ROOT}/data/source/economy_rates_clean.json'))
econ_codes = json.load(open(f'{ROOT}/data/source/economy_country_codes.json'))


def safe_name(economy):
    return economy.replace(' ', '_').replace(',', '').replace('ü', 'u')


results = []
for economy in sorted(rates.keys()):
    hs10_values = json.load(open(f'{ROOT}/data/census/{safe_name(economy)}.json'))
    hs10_values = {k: int(v) for k, v in hs10_values.items()}

    total = sum(hs10_values.values())
    exempt_old = exempt_value(hs10_values, OLD_8, OLD_10)

    # "new" = Part A plus this economy's own supplemental part(s), if any
    extra_letters = PART_LETTER_BY_ECONOMY.get(economy, [])
    if extra_letters:
        new_8, new_10 = set(NEWA_8), set(NEWA_10)
        for letter in extra_letters:
            e8, e10 = split_by_length(part_code_sets[letter])
            new_8 |= e8
            new_10 |= e10
        exempt_new = exempt_value(hs10_values, new_8, new_10)
        notes = f'Part A + Part {"+".join(extra_letters)}'
    else:
        exempt_new = exempt_value(hs10_values, NEWA_8, NEWA_10)
        notes = 'Part A only'

    results.append({
        'Economy': economy,
        'Tariff_Rate': rates[economy]['rate_label'],
        'Total_Import_Value_USD': total,
        'Exempt_Import_Value_Old_USD': exempt_old,
        'Exempt_Import_Value_New_USD': exempt_new,
        'New_List_Composition': notes,
        'Census_Country_Codes': ','.join(econ_codes[economy]),
    })

out_path = f'{ROOT}/output/section301_import_values_by_economy.csv'
with open(out_path, 'w', newline='') as f:
    fieldnames = ['Economy', 'Tariff_Rate', 'Total_Import_Value_USD',
                  'Exempt_Import_Value_Old_USD', 'Exempt_Import_Value_New_USD',
                  'New_List_Composition', 'Census_Country_Codes']
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    for r in results:
        w.writerow(r)

print(f'Wrote {len(results)} economy rows to {out_path}')
total_all = sum(r['Total_Import_Value_USD'] for r in results)
print(f'Grand total CY2025 imports across all 60 economies: ${total_all:,}')
