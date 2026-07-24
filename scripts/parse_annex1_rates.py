#!/usr/bin/env python3
"""Parse Annex I of the July 23, 2026 final-action FRN: the table of new
HTSUS headings 9903.05.20-9903.05.84 that impose the base Section 301
additional ad valorem duty rate (10% or 12.5%) on each of the 60
investigated economies.

Table shape per heading (as rendered by PDF text extraction):
    <heading code>            (own line, optionally prefixed with a quote mark)
    Except for products described in headings ..., articles the product
    of <Economy>, as provided for in U.S. note 52 to this subchapter . . .
    The duty provided in the applicable subheading + <RATE>%   (x2-3, one per rate column)
"""
import fitz
import re
import sys
import json

HEAD_RE = re.compile(r'^9903\.\d{2}\.\d{2}$')
QUOTE_CHARS = '"“”‘’\''


def parse(pdf_path, start_page, end_page):
    doc = fitz.open(pdf_path)
    lines = []
    for i in range(start_page, end_page):
        for l in doc[i].get_text().split('\n'):
            s = l.strip().lstrip(QUOTE_CHARS).strip()
            if s:
                lines.append(s)

    blocks = []
    cur_code, cur_lines = None, []
    for s in lines:
        if HEAD_RE.match(s):
            if cur_code:
                blocks.append((cur_code, ' '.join(cur_lines)))
            cur_code, cur_lines = s, []
        else:
            cur_lines.append(s)
    if cur_code:
        blocks.append((cur_code, ' '.join(cur_lines)))

    results = []
    for code, text in blocks:
        m = re.search(r'articles? the product of (.+?),\s*as provided for', text)
        if not m:
            continue
        economy = m.group(1).strip()
        rates = sorted(set(re.findall(r'\+\s*(\d+(?:\.\d+)?)\s*%', text)))
        net_mfn = 'net of MFN' in text or 'net MFN' in text
        results.append({
            'heading': code,
            'economy': economy,
            'rates_found': rates,
            'raw_excerpt': text[:400],
        })
    return results


if __name__ == '__main__':
    pdf_path, start_page, end_page, out_json = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    rows = parse(pdf_path, start_page, end_page)
    print(f'Parsed {len(rows)} economy-rate entries', file=sys.stderr)
    with open(out_json, 'w') as f:
        json.dump(rows, f, indent=1)
