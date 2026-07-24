#!/usr/bin/env python3
"""Build the clean 60-economy tariff-rate table from the raw Annex I parse,
fixing the one page-break name-garbling artifact (South Africa) and encoding
the 5 "net-of-MFN / top-up-to-threshold" economies properly (EU, Japan,
South Korea, Switzerland, Taiwan) rather than as a flat additive percent.
"""
import json

raw = json.load(open('/home/user/test-repo/data/source/annex1_rates_raw.json'))

# Flat "+X% on top of MFN/column-1" economies map straight across.
FLAT = {}
for r in raw:
    econ = r['economy']
    if 'ad valorem (or ad valorem equivalent)' in econ:
        continue  # handled specially below
    if econ == ('The duty provided in the applicable The duty provided in the '
                'applicable The duty provided in the 82 South Africa'):
        econ = 'South Africa'
    econ = econ.strip()
    if econ.startswith('the '):
        econ = econ[4:]
    rate = r['rates_found'][0] if r['rates_found'] else None
    FLAT[econ] = {
        'economy': econ,
        'heading': r['heading'],
        'rate_type': 'flat_additive',
        'rate_pct': float(rate) if rate else None,
        'rate_label': f'+{rate}% (additional duty on top of existing MFN/Col.1 rate)' if rate else 'UNPARSED',
    }

# Net-of-MFN economies: threshold is in the "greater than or equal to" heading's
# economy string; confirmed from Annex I text: below threshold -> net rate =
# threshold (flat, not additive); at/above threshold -> +0% (no change).
NET_MFN = {
    'European Union': 10.0,
    'Japan': 12.5,
    'South Korea': 12.5,
    'Switzerland': 12.5,
    'Taiwan': 10.0,
}
for econ, threshold in NET_MFN.items():
    FLAT[econ] = {
        'economy': econ,
        'heading': None,
        'rate_type': 'net_of_mfn',
        'rate_pct': threshold,
        'rate_label': (f'Net {threshold}% (top-up to {threshold}% combined MFN+Sec.301; '
                        f'+0% additional if existing MFN/Col.1 rate already >= {threshold}%)'),
    }

print(f'Total economies parsed: {len(FLAT)}')
for k in sorted(FLAT):
    print(' ', k, '->', FLAT[k]['rate_label'])

with open('/home/user/test-repo/data/source/economy_rates_clean.json', 'w') as f:
    json.dump(FLAT, f, indent=1)
