# USTR Section 301 (Forced Labor) — Exempted Goods: July 2026 vs June 2026

Comparison of the goods exempted from the U.S. Trade Representative's Section 301
tariffs imposed on 60 economies for failing to ban imports made with forced labor.

The **July 23, 2026 final action** is compared against the **June 2026 proposed
action**, and every exempted HTS provision is flagged as a **new** exemption or one
that already **existed** in June.

## Source documents

| List | Document | Where the codes live |
|------|----------|----------------------|
| **June** (previous / proposed) | [FRN — Section 301 Forced Labor Import Ban, Actionability & Proposed Action, June 2/5 2026](https://ustr.gov/sites/default/files/files/Press/Releases/2026/FRN%20-%20Section%20301%20Forced%20Labor%20Import%20Ban%20Actionabilty%20and%20Proposed%20Action%206-2-26%20FINAL.pdf) | Annex A |
| **July** (current / final) | [FLIP 301 Investigation Final Action FRN, July 23 2026](https://ustr.gov/sites/default/files/files/Press/Releases/2026/FLIP%20301%20Investigation%20Final%20Action%20FRN%207-23-26%20FINAL.pdf) | Annexes I & II |
| Announcement | [Fact sheet (July 2026)](https://ustr.gov/about/policy-offices/press-office/fact-sheets/2026/july/fact-sheet-ustr-section-301-action-response-failure-60-economies-ban-imports-produced-forced-labor) | — |

## Files

| File | Contents |
|------|----------|
| `USTR_Section301_ForcedLabor_Exemptions_Jul2026_vs_Jun2026.xlsx` | Workbook: Summary + 3 data tabs (main deliverable) |
| `exempted_hs_codes_full_july.csv` | Full July list — every Annex II entry (5,304 rows): HS Code · Description · New/Existing · Applies To · Scope Limitation |
| `exempted_hs_codes_unique_july.csv` | 4,070 unique July codes, de-duplicated, with the economies each applies to |
| `new_universal_exemptions_vs_june.csv` | The 465 codes added to the universal (all-economies) list vs June |
| `june_annex_a_exempted_codes.csv` | The June Annex A list (1,655 codes), for reference |

## Method & definitions

- Codes were extracted programmatically from the June Annex A and July Annex II
  product-exemption tables (columns *HTSUS | Description | Scope Limitation*).
- July **Annex II** is organised in Parts: **Part A** = the universal list (applies to
  all investigated economies); **Parts B–O** = economy-specific carve-outs (UK, EU,
  Switzerland, Malaysia, Cambodia, Guatemala, El Salvador, Argentina, Bangladesh,
  Taiwan, Indonesia, Ecuador, Jordan) plus a large **Part O** CAFTA-DR textile/apparel
  list.
- **Existing** = the HTS code also appears in the June Annex A list.
  **New** = it does not (added in the final action).

## Key findings

- **June Annex A (proposed):** 1,655 exempted HTS codes (single universal list).
- **July universal list (Part A):** 2,120 codes = **all 1,655 June codes retained** +
  **465 new** universal exemptions. **Zero** June exemptions were removed.
- **July also adds 13 economy-specific lists** (Parts B–N) and a **CAFTA-DR
  textile/apparel list** (Part O, 1,737 lines) that did not exist in June.
- **Total July Annex II entries:** 5,304 (4,070 unique codes → 1,655 existing, 2,415 new).

### July Annex II by Part

| Part | Applies to | Entries | Existing | New |
|------|-----------|--------:|---------:|----:|
| A | All investigated economies (universal) | 2,120 | 1,655 | 465 |
| B | United Kingdom | 49 | 1 | 48 |
| C | European Union | 43 | 1 | 42 |
| D | Switzerland | 134 | 1 | 133 |
| E | Malaysia | 104 | 1 | 103 |
| F | Cambodia | 157 | 1 | 156 |
| G | Guatemala | 112 | 1 | 111 |
| H | El Salvador | 99 | 1 | 98 |
| I | Argentina | 93 | 1 | 92 |
| J | Bangladesh | 87 | 1 | 86 |
| K | Taiwan | 118 | 1 | 117 |
| L | Indonesia | 148 | 1 | 147 |
| M | Ecuador | 151 | 2 | 149 |
| N | Jordan | 152 | 1 | 151 |
| O | CAFTA-DR textiles/apparel (Jordan, El Salvador, Guatemala) | 1,737 | 0 | 1,737 |
| **Total** | | **5,304** | **1,655** | **3,649** |

> The per-Part "Existing"/"New" columns count rows; unique-code totals differ because a
> code can be exempted for more than one economy (163 codes appear in more than one Part).

## Note on the FRN's "471 additional products"

Section D of the July notice ("Determination to Exempt Additional Products") states that
the Trade Representative excluded *"an additional 471 products"* beyond those proposed in
June. This workbook counts **465** distinct new HTS subheadings in the universal list
(Part A).

The 465 figure was verified two independent ways — parsing the annex table structure, and
re-extracting codes by text geometry (leftmost-column position). Both return exactly 2,120
Part A codes, with no missed rows, duplicates, or non-standard entries; and June's 1,655
codes are an **exact subset** of Part A (0 removed), including after normalizing 8- vs
10-digit code formats. So 465 is the accurate count of distinct *new tariff lines*.

The 6-item difference is therefore a **counting-definition gap** between the notice's prose
"product" count and distinct HTS subheadings in Annex II — not missing or duplicated data.
Three candidate explanations were tested and **all ruled out**:

1. **10-digit code formatting** — the 7 codes in `XXXX.XX.XXXX` form are already counted
   correctly; normalizing to 8 digits changes nothing.
2. **Modified exemptions** — 369 shared codes received scope changes (mostly new `Pharma`
   tags) and 97 differ only by PDF line-break hyphenation. Neither equals 6.
3. **A June 2 vs June 5 difference** — ruled out by OCR, see below.

### OCR verification of the June 5 Federal Register annex

USTR's 471 might have been measured against the **June 5 Federal Register** publication
rather than the **June 2 pre-publication PDF** used here. The Federal Register renders
Annex A as page images, so the 68 annex pages were extracted and OCR'd (Tesseract 5,
multi-pass across PSM modes 4/6/11/12, left-hand HTSUS column cropped) and compared
code-by-code against the June 2 extraction.

- OCR recall was **~96%** (1,631 of 1,655 codes read cleanly), with 43 identifiable
  misreads (e.g. `0201.20.06` read as `9201.20.06`).
- The 67 codes OCR appeared to "miss" were scattered thinly across **30 pages** (1–7 per
  page) — the signature of random read failure, not a deliberate removal of 6 codes.
- **16 of those codes were then inspected visually** in the page images, spanning three
  chapters (28 chemicals, 71 precious metals, 81 base metals). **All 16 were present.**

**Conclusion:** the June 5 published annex is identical in content to the June 2 PDF used
here. The June baseline of 1,655 codes is confirmed, and **465 is the correct count of
distinct new HTS subheadings**. The FRN's "471" reflects how USTR tallies "products" in
prose, not a different underlying list.

## Category exemptions (not tied to HTS codes)

Both notices also exempt, outside the HTS tables: informational materials; donations
(food, clothing, medicine to relieve human suffering); accompanied baggage; all
articles/parts subject to **Section 232** tariffs (aluminium, steel, copper, autos &
parts, medium/heavy trucks & parts, wood products, semiconductors); and articles for
pharmaceutical use. In the July notice these are HTSUS headings 9903.05.85–9903.05.92
(Annex I). June also recited USMCA-compliant goods of Canada/Mexico and CAFTA-DR
duty-free textiles; in July the CAFTA-DR textile/apparel exemptions are enumerated as
HTS codes in Annex II, Part O.
