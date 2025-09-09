# EstimateDoc – Codex Analysis Report

## Introduction
- Purpose: Link ClientRequirements templates to ExportSandI and SQL exports; quantify fields by category and uniqueness (no weighting or complexity).
- Data sources: ClientRequirements.xlsx; ExportSandI manifests; newSQL JSON dumps; Scripts.

## Methodology & Reasoning Steps (summarized)
- Parsed ExportSandI.Manifest.xml for items Type="Precedents"; collected numeric codes and names.
- For each code, checked Precedents/{code}/manifest.xml; where present, extracted PrecTitle, PrecID, PrecScript, and extension.
- Loaded Documents/Fields/DocumentFields from newSQL JSON files; mapped DocumentID→filename and derived base codes (lowercased filenames without extension).
- Classified Fields into categories by FieldCode patterns (e.g., IF, DOCVARIABLE, MERGEFIELD, HYPERLINK, INCLUDETEXT, etc.).
- Aggregated, per document, unique FieldIDs by category; computed reuse by counting how many documents each FieldID appears in.
- Matched ClientRequirements rows by Current Title against PrecTitle/SQL base codes (case-insensitive).
- For duplicates (same Current Title, different Description), kept separate rows and noted related variants.
- Created an Excel export with per-category Unique/Common counts and totals only (no weighting, no complexity scoring).

## Data Linking Analysis
- Client rows: 547; matched to ExportSandI: 545; matched to SQL: 446.
- Data files: documents=documents.json, fields=fields.json, relationships=documentfields.json
- Precedent→Script linkage used PrecScript in Precedent manifests (e.g., PrecScript="_16188" maps to Scripts/_16188).
- SQL Document match uses base filename (e.g., sup073 from "sup073.dot"). No external IDs were cross-walked.

### Category Columns Derived
- Built In Script: counts for Unique Built In Script and Common Built In Script.
- Extended: counts for Unique Extended and Common Extended.
- If: counts for Unique If and Common If.
- Precedent Script: counts for Unique Precedent Script and Common Precedent Script.
- Reflection: counts for Unique Reflection and Common Reflection.
- Scripted: counts for Unique Scripted and Common Scripted.
- Search: counts for Unique Search and Common Search.
- Unbound: counts for Unique Unbound and Common Unbound.

## Category Totals (from data source)
- Built In Script: Unique=17, Common=166
- Extended: Unique=24, Common=71
- If: Unique=4354, Common=525
- Precedent Script: Unique=328, Common=1916
- Reflection: Unique=1068, Common=578
- Scripted: Unique=4, Common=80
- Search: Unique=157, Common=519
- Unbound: Unique=431, Common=236

## Matched Subset Averages (for estimation)
- Built In Script: Avg Unique=0.04, Avg Common=0.37
- Extended: Avg Unique=0.05, Avg Common=0.16
- If: Avg Unique=9.76, Avg Common=1.18
- Precedent Script: Avg Unique=0.74, Avg Common=4.3
- Reflection: Avg Unique=2.39, Avg Common=1.3
- Scripted: Avg Unique=0.01, Avg Common=0.18
- Search: Avg Unique=0.35, Avg Common=1.16
- Unbound: Avg Unique=0.97, Avg Common=0.53
- Avg Total Field IDs (unique): 23.48
- Avg Total Field Instances: 47.09
- Avg Total Unique Fields: 14.31
- Avg Total Reusable Fields: 9.17

## Estimation for Unmatched Rows
- Estimates sheet applies matched averages to unmatched templates (per category and totals).
- Caution: Current matched coverage is low; treat these as rough placeholders until more documents are available or a crosswalk is provided.

## Scripts Utility Review
- Located PRECEDENT scripts under ExportSandI/Scripts/_<code>; manifests include scrType=PRECEDENT and embedded C#-like logic.
- Where Precedent manifest includes PrecScript, we recorded presence; reuse can be assessed by identical PrecScript across templates.

## Unknown XML Review
- ExportSandI.Replacement.xml appears to define field replacement metadata (FIELDREPLACER) for Precedent-level default values, lookup sources, and constraints (e.g., PrecType, PrecDirID).
- Likely used by the export/import tooling to map UI fields to database values and defaults during packaging.

## Optimal Linking Method – Evaluation
- Primary keys: use PrecID/Code from ExportSandI manifests; match to ClientRequirements by PrecTitle; match to SQL by base filename. This avoids cross-dataset ID conflation.
- Robustness: Prefer Precedent manifest PrecTitle over root Name; fall back to root Name if manifest missing.
- Reuse detection: Field-level uniqueness is computed strictly within SQL data by FieldID→Documents cardinality; no external assumptions made.
- Improvement: If available, extract an explicit mapping table between PrecID and SQL Document filename to remove reliance on string base names.

## Postgres + UI Strategy
- Schema: tables for client_requirements, precedents (from ExportSandI), sql_documents, fields, document_fields, scripts; views for per-template aggregates (counts only).
- Import: load from live DB (read-only) into staging; derive aggregates by counts only.
- UI: grid per template showing categories, unique/common counts and totals; no weighting or scoring involved.

## Edge Cases & Gaps
- Missing Precedent manifests in some code folders: PrecTitle and PrecScript may be unavailable; we use root manifest Name as a fallback.
- Some ClientRequirements titles may not exist in SQL exports; those rows are retained with zeros and flagged as unmatched.
- Scripts linkage only available when PrecScript is populated in Precedent manifest.

## Deliverables
- Excel export with analysis: CodexReview/ClientRequirements_Analyzed.xlsx
- Contains: per-category Unique/Common columns; total field metrics; related variants; no scoring or parameters.

## Conclusions & Recommendations
- Linkage based on PrecTitle⇄filename base is viable given current data; prefer PrecID where possible for stability.
- Maintain scripts mapping via PrecScript and count reusable scripts by identical scrCode across precedents.
- Adopt the proposed Postgres schema and simple UI to surface unique vs reusable field counts (no weighting).
- Address missing manifests by re-exporting complete Precedent metadata or enriching with an external mapping file.
- Keep FIELDREPLACER (Replacement.xml) available to guide defaults in any import tooling; document its fields in developer docs.