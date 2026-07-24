#!/usr/bin/env python3
"""Merge the June 2, 2026 (proposed action, Annex A) and July 23, 2026
(final action, Annex II Part A) universal exempt-HTSUS lists into one CSV:
HS code, Description, which list it's on (old / new / both).

Both source annexes apply "Goods of Any Investigated Economy" (no country
carve-out), so this is a like-for-like comparison. July 23 also added
country/bloc-specific supplemental exemptions (Annex II Parts B-O) that are
NOT included here since they don't apply economy-wide — see
parts/manifest.json and the value-calculation script for how those are
folded into the per-economy import totals instead.
"""
import csv
import json


def load_dedup(path):
    rows = json.load(open(path))
    by_code = {}
    for r in rows:
        code, desc, scope = r['code'], r['description'], r['scope']
        if code not in by_code:
            by_code[code] = {'description': desc, 'scope': scope}
        else:
            # keep the richer (non-empty) description/scope; page-break
            # artifacts produce a harmless empty-description duplicate row
            if not by_code[code]['description'] and desc:
                by_code[code]['description'] = desc
            if not by_code[code]['scope'] and scope:
                by_code[code]['scope'] = scope
    return by_code


OLD = load_dedup('/home/user/test-repo/data/source/june_annexA_raw.json')
NEW = load_dedup('/home/user/test-repo/data/source/july_partA_raw.json')

all_codes = sorted(set(OLD) | set(NEW))
print(f'old (June 2 Annex A): {len(OLD)} codes')
print(f'new (July 23 Annex II Part A): {len(NEW)} codes')
print(f'union: {len(all_codes)} codes')
print(f'both: {len(set(OLD) & set(NEW))}')
print(f'old only: {len(set(OLD) - set(NEW))}')
print(f'new only: {len(set(NEW) - set(OLD))}')

out_path = '/home/user/test-repo/output/section301_exempt_hs_codes.csv'
with open(out_path, 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['HS_Code', 'Description', 'Exemption_List', 'Scope_Limitation'])
    for code in all_codes:
        in_old, in_new = code in OLD, code in NEW
        which = 'both' if in_old and in_new else ('old' if in_old else 'new')
        desc = (NEW.get(code) or OLD.get(code))['description']
        scope = (NEW.get(code) or OLD.get(code))['scope']
        w.writerow([code, desc, which, scope])

print(f'\nWrote {len(all_codes)} rows to {out_path}')
