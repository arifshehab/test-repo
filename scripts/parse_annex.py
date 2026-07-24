#!/usr/bin/env python3
"""Parse the Annex A exempt-HTSUS table out of a USTR Section 301 FRN PDF.

Each row in the source table renders as:
    <code>            (own line, fullmatch only)
    <description...>   (one or more lines)
    <scope tag>         (optional: exactly "Ex" or "Aircraft")
Codes that are merely *mentioned* inside another row's description text
(e.g. "...other than those of subheading 8411.91.10") appear on a line
with surrounding words, so they do NOT fullmatch the bare-code pattern and
are correctly left as description continuation text.
"""
import fitz
import re
import sys
import json

CODE_FULL = re.compile(r'^\d{4}\.\d{2}\.\d{2,4}$')
# 'Ex' and 'Aircraft' are defined in both FRNs; 'Pharma' is introduced only
# in the July 23 final action's Annex II note (not present in June's Annex A).
SCOPE_TAGS = {'Ex', 'Aircraft', 'Pharma'}
PART_HEADER_RE = re.compile(r'^Part [A-Z]\.')
HEADER_SEQ = ['HTSUS', 'Description', 'Scope', 'Limitations']


def parse_annex(pdf_path, start_page, end_page=None):
    doc = fitz.open(pdf_path)
    end_page = end_page if end_page is not None else len(doc)
    lines = []
    for i in range(start_page, end_page):
        for l in doc[i].get_text().split('\n'):
            s = l.strip()
            # Only drop blank lines, bare page numbers, and "Part X." part
            # headers here. Do NOT filter the column-header words (HTSUS /
            # Description / Scope / Limitations) individually: each of them
            # also occurs legitimately as the last wrapped word/line of a
            # real product description (e.g. "...of the\nHTSUS"), so a
            # blanket per-line filter silently truncates real descriptions.
            # The header is instead stripped below as a contiguous 4-line
            # sequence, which real description text won't coincidentally
            # reproduce.
            if s == '' or s.isdigit() or PART_HEADER_RE.match(s) or s == 'Table of Contents':
                continue
            lines.append(s)

    # Strip the repeated "HTSUS / Description / Scope / Limitations" table
    # header wherever it appears as an exact contiguous run.
    cleaned = []
    i = 0
    n = len(HEADER_SEQ)
    while i < len(lines):
        if lines[i:i + n] == HEADER_SEQ:
            i += n
        else:
            cleaned.append(lines[i])
            i += 1
    lines = cleaned

    rows = []
    cur = None
    for s in lines:
        if CODE_FULL.match(s):
            if cur is not None:
                rows.append(cur)
            cur = {'code': s, 'desc_lines': [], 'scope': ''}
        elif s in SCOPE_TAGS and cur is not None:
            cur['scope'] = s
        elif cur is not None:
            cur['desc_lines'].append(s)
    if cur is not None:
        rows.append(cur)

    out = []
    for r in rows:
        desc = ' '.join(r['desc_lines'])
        desc = re.sub(r'\s+', ' ', desc).strip()
        scope = r['scope']
        # The "Scope Limitations" table cell occasionally lands on the same
        # extracted text line as the tail of the Description cell instead of
        # its own line (a PDF-extraction quirk, not a document feature), e.g.
        # one raw line reading "...aeronautical or space navigation Aircraft".
        # When that happens the tag never appears alone, so it's missed as a
        # scope tag and instead pollutes the end of the description. No real
        # HTSUS description legitimately ends on the bare word "Aircraft" or
        # "Ex", so if the scope column is otherwise empty, reclaim it.
        if not scope:
            m = re.search(r'\s(Ex|Aircraft|Pharma)$', desc)
            if m:
                scope = m.group(1)
                desc = desc[:m.start()].strip()
        out.append({'code': r['code'], 'description': desc, 'scope': scope})

    return _repair_inline_code_refs(out)


# A genuine row's description is a noun phrase describing goods and never
# trails off on a bare conjunction/preposition/reference word. When a
# description *does* end that way, it's a sign the sentence kept going into
# a cross-reference to another HTSUS subheading (e.g. "...of subheading
# 9031.41 or") that happened to land alone on its own text line and got
# mis-parsed as a new row (see module docstring: normally such references
# are safe because they share a line with a word like "subheading", but
# line-wrap position is a coin flip and sometimes leaves the bare code
# isolated). That mis-parsed "row" has an empty description (nothing came
# before the next real code or scope tag), so it's never a useful entry on
# its own -- fold it back into the row it truncated.
_DANGLING_END_RE = re.compile(
    r'\b(or|and|to|of|in|the|a|an|for|with|on|by|from|subheading|subheadings)$',
    re.IGNORECASE)


def _repair_inline_code_refs(rows):
    repaired = []
    i = 0
    while i < len(rows):
        cur = dict(rows[i])
        # Absorb any run of immediately-following empty-description rows
        # that look like inline subheading references, not real entries.
        while (i + 1 < len(rows) and rows[i + 1]['description'] == ''
               and _DANGLING_END_RE.search(cur['description'])):
            nxt = rows[i + 1]
            cur['description'] = (cur['description'] + ' ' + nxt['code']).strip()
            if not cur['scope'] and nxt['scope']:
                cur['scope'] = nxt['scope']
            i += 1
        repaired.append(cur)
        i += 1
    return repaired


if __name__ == '__main__':
    pdf_path = sys.argv[1]
    start_page = int(sys.argv[2])
    out_json = sys.argv[3]
    end_page = int(sys.argv[4]) if len(sys.argv) > 4 else None
    rows = parse_annex(pdf_path, start_page, end_page)
    codes = [r['code'] for r in rows]
    print(f'{pdf_path}: parsed {len(rows)} rows, {len(set(codes))} unique codes', file=sys.stderr)
    dupes = {c for c in codes if codes.count(c) > 1}
    if dupes:
        print(f'WARNING duplicate codes: {dupes}', file=sys.stderr)
    with open(out_json, 'w') as f:
        json.dump(rows, f, indent=1)
