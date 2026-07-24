#!/usr/bin/env python3
"""Parse Annex II Parts B-O (country/bloc-specific supplemental exemptions)
from the July 23, 2026 final-action FRN, and save each as its own JSON file
plus a combined manifest.
"""
import json
import sys
sys.path.insert(0, '/home/user/test-repo/scripts')
from parse_annex import parse_annex

PDF = '/home/user/test-repo/data/source/july23_final.pdf'
OUT_DIR = '/home/user/test-repo/data/source/parts'

PARTS = [
    ('B', 'United Kingdom', 242, 245),
    ('C', 'European Union', 245, 247),
    ('D', 'Switzerland', 247, 253),
    ('E', 'Malaysia', 253, 259),
    ('F', 'Cambodia', 259, 266),
    ('G', 'Guatemala', 266, 272),
    ('H', 'El Salvador', 272, 277),
    ('I', 'Argentina', 277, 282),
    ('J', 'Bangladesh', 282, 287),
    ('K', 'Taiwan', 287, 293),
    ('L', 'Indonesia', 293, 300),
    ('M', 'Ecuador', 300, 308),
    ('N', 'Jordan', 308, 315),
    ('O', 'Jordan|El Salvador|Guatemala (CAFTA-DR textile/apparel)', 315, 431),
]

import os
os.makedirs(OUT_DIR, exist_ok=True)

manifest = []
for letter, economy, start, end in PARTS:
    rows = parse_annex(PDF, start, end)
    codes = [r['code'] for r in rows]
    n_dupe = len(codes) - len(set(codes))
    print(f'Part {letter} ({economy}): pages {start}-{end - 1}, {len(rows)} rows, '
          f'{len(set(codes))} unique, {n_dupe} dup-artifacts', file=sys.stderr)
    fname = f'{OUT_DIR}/part_{letter}.json'
    with open(fname, 'w') as f:
        json.dump(rows, f, indent=1)
    manifest.append({'part': letter, 'economy': economy, 'start_page': start,
                      'end_page': end, 'file': fname, 'row_count': len(rows)})

with open(f'{OUT_DIR}/manifest.json', 'w') as f:
    json.dump(manifest, f, indent=1)
print('Done.', file=sys.stderr)
