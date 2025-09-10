# EstimateDoc – Final Mapping and Analysis Report

## Overview
- Total templates (ClientRequirements): 547
- Mapped to newSQL documents: 446
- Unmatched to newSQL: 101
- Data sources: ClientRequirements.xlsx; ExportSandI manifests (root + per-code); newSQL JSON (documents, fields, documentfields, field_analysis); BecInfo; mapping guidance in MAPPING_APPROACH_DOCUMENTATION.md.

## Mapping Approach
- Extract codes from ExportSandI.Manifest.xml; for each code open Precedents/<code>/manifest.xml.
- From folder manifest, read PrecTitle, PrecID, PrecPath, PrecScript; prefer folder manifest over root.
- Link Excel Current Title to PrecTitle.
- Derive SQL match keys in order:
  1) PrecPath basename (Windows) → numeric filename in newSQL documents (e.g., Company\2694.dot → 2694.dot).
  2) ExportSandI Code as numeric filename (e.g., 7387 → 7387.dot).
  3) PrecTitle and its normalized variants; suffix-stripped variants (e.g., sup021b → sup021).
  4) PrecID (as a last resort).

## Category Definitions
- Categories per BecInfo: Search, Reflection, If, Built In Script, Extended, Scripted, Unbound, Precedent Script.
- Unique = FieldID appears in exactly 1 document; Common = FieldID appears in >1 document (within newSQL).

## Category Totals (actual)
- Built In Script: Unique=17, Common=166
- Extended: Unique=24, Common=71
- If: Unique=4354, Common=525
- Precedent Script: Unique=328, Common=1916
- Reflection: Unique=1068, Common=578
- Scripted: Unique=4, Common=80
- Search: Unique=157, Common=519
- Unbound: Unique=431, Common=236

## Estimates for Unmatched
- Estimates are computed by applying matched-only averages per category and total to each unmatched row (see Estimates sheet).
- Treat as planning placeholders; replace with actuals when additional documents or a crosswalk is available.

## Files Delivered
- CodexFinal/EstimateDoc_Final.xlsx: Pivot-friendly workbook
  - Templates: all per-row metrics
  - Estimates: averages applied for unmatched
  - AggregatedByTitle: rolled-up view by Current Title
  - LongCategoryCounts: normalized per-category counts for pivoting
  - Unmatched_SQL: rows without SQL mapping
  - Summary: coverage and averages
- CodexFinal/Final_Report.md: This report (approach, findings, next steps)