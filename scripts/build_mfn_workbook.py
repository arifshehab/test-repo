#!/usr/bin/env python3
"""Build the 5-tab .xlsx workbook (EU, Japan, South Korea, Switzerland, Taiwan)
with: HS code | Description | Import value | MFN rate | Forced labor tariff rate.

Forced labor rate logic (net-of-MFN mechanic, per July 23 2026 final FRN):
  - exempt (July 23 final exemption list, Part A + economy's own supplemental
    part) -> 0%
  - else, if MFN rate is a clean ad valorem % -> max(0, cap% - MFN%)
  - else (MFN rate is specific/compound, e.g. "44c/kg + 6%", and no AVE source
    was available) -> flagged, not computed
  - else (HS10 code has no rate data at all, even via 8-digit-ancestor
    fallback -- concentrated in HTS ch.91 watches, a likely 2025-vintage
    statistical-suffix mismatch vs. the current 2026 Rev.12 schedule) -> flagged
"""
import json
import csv
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter

ROOT = "/home/user/test-repo"

CAPS = {
    "European Union": 10.0,
    "Japan": 12.5,
    "South Korea": 12.5,
    "Switzerland": 12.5,
    "Taiwan": 10.0,
}

ECON_FILES = {
    "European Union": "European_Union.json",
    "Japan": "Japan.json",
    "South Korea": "South_Korea.json",
    "Switzerland": "Switzerland.json",
    "Taiwan": "Taiwan.json",
}

PART_LETTER_BY_ECONOMY = {
    "European Union": ["C"],
    "Switzerland": ["D"],
    "Taiwan": ["K"],
    # Japan, South Korea: Part A (universal) only, no supplemental part
}


def norm(code):
    return code.replace(".", "")


def load_code_set(path):
    rows = json.load(open(path))
    return {norm(r["code"]) for r in rows}


def split_by_length(codes):
    c8 = {c for c in codes if len(c) == 8}
    c10 = {c for c in codes if len(c) == 10}
    return c8, c10


def dotted(code10):
    return f"{code10[0:4]}.{code10[4:6]}.{code10[6:8]}.{code10[8:10]}"


def main():
    rate_map = json.load(open(f"{ROOT}/data/source/mfn_rate_map.json"))
    by8 = {}
    for c, info in rate_map.items():
        by8.setdefault(c[:8], set()).add((info["rate_type"], info["rate_pct"]))

    new_part_a = load_code_set(f"{ROOT}/data/source/july_partA_raw.json")
    newa_8, newa_10 = split_by_length(new_part_a)

    part_code_sets = {}
    for letter in "BCDEFGHIJKLMNO":
        part_code_sets[letter] = load_code_set(f"{ROOT}/data/source/parts/part_{letter}.json")

    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill("solid", fgColor="1F4E78")
    flag_fill = PatternFill("solid", fgColor="FFF2CC")

    summary_rows = []

    for economy, fn in ECON_FILES.items():
        cap = CAPS[economy]
        letters = PART_LETTER_BY_ECONOMY.get(economy, [])
        exempt_8, exempt_10 = set(newa_8), set(newa_10)
        for letter in letters:
            e8, e10 = split_by_length(part_code_sets[letter])
            exempt_8 |= e8
            exempt_10 |= e10

        hs10_values = json.load(open(f"{ROOT}/data/census/{fn}"))
        codes = sorted(c for c, v in hs10_values.items() if v and v > 0)

        ws = wb.create_sheet(title=economy[:31])
        headers = ["HS Code", "Description", "Import Value (USD, CY2025 General Imports)",
                   "MFN Rate (Col.1 General)", "Forced Labor Tariff Rate", "Notes"]
        ws.append(headers)
        for col in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws.freeze_panes = "A2"

        n_exempt = n_percent = n_compound_flag = n_missing_flag = 0
        total_val = 0
        exempt_val = 0
        computed_val = 0
        flagged_val = 0

        for code in codes:
            val = hs10_values[code]
            total_val += val
            is_exempt = code[:8] in exempt_8 or code in exempt_10

            info = rate_map.get(code)
            source_note = ""
            if info is None:
                fallback = by8.get(code[:8])
                if fallback and len(fallback) == 1:
                    rate_type, rate_pct = next(iter(fallback))
                    desc = None
                    source_note = "MFN rate inferred from 8-digit ancestor (exact HS10 line not in current HTS Rev.12; possible 2025-vintage statistical-suffix change)"
                else:
                    rate_type, rate_pct = "unresolved", None
                    desc = None
            else:
                rate_type, rate_pct = info["rate_type"], info["rate_pct"]
                desc = info["desc"]

            mfn_display = None
            fl_rate = None
            notes = source_note

            if is_exempt:
                mfn_display = None if rate_pct is None else rate_pct
                if rate_type not in ("free", "percent"):
                    mfn_display = None
                fl_rate = 0.0
                n_exempt += 1
                exempt_val += val
            elif rate_type in ("free", "percent"):
                mfn_display = rate_pct
                fl_rate = max(0.0, cap - rate_pct)
                n_percent += 1
                computed_val += val
            elif rate_type == "specific_or_compound":
                mfn_display = "non-ad-valorem (see raw rate)"
                fl_rate = "N/A - AVE unavailable"
                notes = (notes + "; " if notes else "") + f"Raw MFN rate: {info['raw'] if info else ''} - not a clean % and no AVE source found; forced-labor rate not computed"
                n_compound_flag += 1
                flagged_val += val
            else:
                mfn_display = "unavailable"
                fl_rate = "N/A - MFN rate unavailable"
                notes = (notes + "; " if notes else "") + "HS10 code (and its 8-digit parent) not found in current USITC HTS Revision 12 schedule"
                n_missing_flag += 1
                flagged_val += val

            row = [dotted(code), desc, val, mfn_display, fl_rate, notes]
            ws.append(row)
            if isinstance(fl_rate, str):
                r = ws.max_row
                for col in range(1, len(headers) + 1):
                    ws.cell(row=r, column=col).fill = flag_fill

        # column formatting
        ws.column_dimensions["A"].width = 16
        ws.column_dimensions["B"].width = 55
        ws.column_dimensions["C"].width = 24
        ws.column_dimensions["D"].width = 20
        ws.column_dimensions["E"].width = 22
        ws.column_dimensions["F"].width = 60
        for r in range(2, ws.max_row + 1):
            c = ws.cell(row=r, column=3)
            c.number_format = "#,##0"
            d = ws.cell(row=r, column=4)
            if isinstance(d.value, (int, float)):
                d.number_format = "0.00\"%\""
            e = ws.cell(row=r, column=5)
            if isinstance(e.value, (int, float)):
                e.number_format = "0.00\"%\""

        summary_rows.append({
            "Economy": economy,
            "Cap": cap,
            "HS10 lines": len(codes),
            "Total import value": total_val,
            "Exempt lines": n_exempt,
            "Exempt value": exempt_val,
            "Computed (%) lines": n_percent,
            "Computed value": computed_val,
            "Flagged: non-ad-valorem": n_compound_flag,
            "Flagged: rate unavailable": n_missing_flag,
            "Flagged value (total)": flagged_val,
        })
        print(f"{economy}: {len(codes)} lines | exempt={n_exempt} | computed={n_percent} | "
              f"flagged_compound={n_compound_flag} | flagged_missing={n_missing_flag} | "
              f"flagged_value=${flagged_val:,.0f} ({100*flagged_val/total_val:.2f}%)")

    out_path = f"{ROOT}/output/section301_mfn_forced_labor_rates_by_economy.xlsx"
    wb.save(out_path)
    print(f"\nWrote workbook: {out_path}")

    with open(f"{ROOT}/output/section301_mfn_workbook_summary.csv", "w", newline="") as f:
        fieldnames = list(summary_rows[0].keys())
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in summary_rows:
            w.writerow(r)


if __name__ == "__main__":
    main()
