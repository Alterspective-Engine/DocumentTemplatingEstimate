# Excel → Dataset Matching Guidance (Precedents & Templates)

**Purpose**  
Provide a clear, deterministic method to link rows from the supplied Excel workbook (your “documents of interest”) to the broader dataset (Manifest XML, JSON exports, and the ExportSandI package), so the set can be analysed and estimated end‑to‑end.

---

## 1) Data sources & roles

- **Excel (documents of interest)**: free‑text columns that may contain an ID (numeric code), a “Sup…” name, and/or a filename.
- **Top‑level Manifest XML** (`ExportSandI.Manifest.xml`): authoritative list of **Precedent** items with **Code** (numeric) and **Name** (often `Sup0xx…`).  
- **JSON exports**:  
  - `dbo_Documents.json` — contains **Filename** (e.g., `17553.dot`) and **DocumentID`**.  
  - `dbo_DocumentFields.json` — links DocumentID ↔ FieldID.  
  - `dbo_Fields.json` — contains **FieldCode** text used for complexity/LOE.  
- **ExportSandI.zip**: a structured per‑precedent export with **per‑precedent `manifest.xml` files**; useful for confirming precedent existence and folder paths (it **does not** include the Word `.dot` binaries).

**Goal:** Build a one‑row‑per‑Excel‑item mapping to DocumentID (when possible), enriched with manifest/precedent context, and a second‑best mapping to a per‑precedent folder when a DocumentID cannot be resolved.

---

## 2) Canonical join keys (what to extract from Excel)

From every Excel row, derive these **normalized** keys:
- **`excel_code`**: the first 3+ digit number in the row (e.g., `17553`).  
  - Regex: `\b(\d{3,})\b`
- **`excel_name`**: the first token that looks like a Sup name (e.g., `Sup021c` → `sup021c`).  
  - Regex: `\b(sup[0-9a-z]+)\b` (case‑insensitive)
- **`excel_filename`**: the first token ending in `.dot|.doc|.docx|.xsl|.xslt` (lower‑case).  
  - Regex: `([A-Za-z0-9_\-]+)\.(dot|docx?|xsl|xslt)$`

> If Excel “Name” columns contain embedded values (e.g., `Value: 17553` or `Precedent [17553]`), also extract:  
> - **`val_digits`** via bracket/inline patterns `\[(\d{3,})\]` or the generic digits regex above, and  
> - **`val_sup`** via the Sup regex.

Create a **`candidate_filename`** in this order of preference:
1) `excel_filename` (verbatim, lower‑cased)  
2) `excel_code + ".dot"`  
3) `excel_name + ".dot"`  
4) If using “value” mining: `val_digits + ".dot"` then `val_sup + ".dot"`

---

## 3) Normalization rules (apply to all sides before matching)

- Trim whitespace; lower‑case all name‑like, filename‑like, and Sup tokens.
- Keep numeric **Code** as digits only (no padding, no spaces).
- For filenames, compare by **basename** only (ignore directory, keep extension).  
- Treat `Sup021c` and `sup021c` as equal; output normalized `sup021c`.
- Ignore duplicate internal spaces and punctuation when parsing free text.

---

## 4) Deterministic matching pipeline (with precedence)

Use this order and **stop at the first successful hit**. Persist the method you used as `match_method` and a `match_confidence` label.

1) **Exact filename → Documents (High)**  
   - Join `candidate_filename` ↔ `dbo_Documents.Basename` (lower‑case).  
   - If hit, attach `DocumentID` and proceed to field enrichment (Section 6).

2) **Code → Manifest → Filename → Documents (High)**  
   - Join `excel_code` ↔ `Manifest.Code`.  
   - Derive `code.dot` and join ↔ `Documents.Basename`.

3) **Sup‑name → Manifest → Filename → Documents (High/Medium)**  
   - Join `excel_name` (normalized) ↔ `Manifest.Name` (normalized).  
   - Derive `supname.dot` and join ↔ `Documents.Basename`.

4) **Name “value” mining (Medium)**  
   - Use `val_digits` or `val_sup` extracted from Excel name text.  
   - As above, derive `.dot` and join ↔ `Documents.Basename`.

5) **Per‑precedent folder (ZIP) only (Low)**  
   - If no `DocumentID` found, map via `excel_code` or `excel_name` to a **per‑precedent folder** in `ExportSandI/Precedents/<code>/manifest.xml`.  
   - Store `zip_rel_path` (e.g., `ExportSandI/Precedents/17553/manifest.xml`) as **evidence of existence**, but mark as **no‑document** (you still lack the `.dot` file in the ZIP).

> **Conflict resolution:**  
> - If multiple documents match the same filename, prefer `.dot` over `.doc/.docx/.xsl/.xslt`.  
> - If both Code and Sup resolve but point to different targets, **prefer Code** and flag a `note_conflict="code_vs_sup"` for review.

---

## 5) Confidence model

- **High**: exact filename to `Documents`, or Code→Manifest→`code.dot`→`Documents`.  
- **Medium**: Sup‑name→Manifest→`sup.dot`→`Documents`, or name “value” mining that lands in `Documents`.  
- **Low**: only per‑precedent folder evidence in the ZIP (no `DocumentID`).

Persist `match_method` ∈ {`filename`, `code_manifest`, `sup_manifest`, `name_value`, `zip_only`} and `match_confidence` ∈ {`High`,`Medium`,`Low`}.

---

## 6) Enrichment for LOE readiness (when `DocumentID` exists)

If a `DocumentID` is available:
- Join `dbo_DocumentFields` on `DocumentID` to get the list of `FieldID`s.  
- Join `dbo_Fields` on `FieldID` to obtain `FieldCode` strings.
- Compute complexity signals per template:  
  - **Core fields**: `MERGEFIELD`  
  - **Unbound fields**: `DOCVARIABLE`  
  - **IF statements**: presence of `IF`  
  - **Nested IF**: ≥2 `IF` tokens in a single `FieldCode`  
  - **Scripted/calculated**: heuristics matching `FORMULA`, `SET `, `REF `, `MERGESEQ`, `MACROBUTTON` (count IF separately)
- Classify **Simple / Complex / Very Complex** using your chosen thresholds (e.g., total field count ≤25 and no IF/scripted = Simple; >55 or nested IFs = Very Complex; else Complex).
- Apply your effort model (minutes per tag/rule/calculated/questionnaire/sections + base times).

> If there’s **no** `DocumentID`, use the **extrapolation** approach: apply the matched set’s complexity mix to the unmatched count to estimate total effort.

---

## 7) Output schema (recommended)

Produce a single audit table with at least these columns:

| Column | Description |
|---|---|
| `row_uid` | A stable per‑row key (sheet name + row number or a GUID) |
| `__sheet` | Sheet/tab name from Excel |
| `excel_raw_name` | First non‑null “name” cell used |
| `excel_code` | Extracted digits (e.g., `17553`) |
| `excel_name` | Extracted Sup name (normalized, e.g., `sup021c`) |
| `excel_filename` | Extracted explicit filename from Excel (lower‑cased) |
| `val_digits` / `val_sup` | Values mined from name text (optional) |
| `candidate_filename` | Chosen candidate basename used for match |
| `manifest_code` / `manifest_name` | If resolved via manifest |
| `DocumentID` | From `dbo_Documents` (if matched) |
| `DocumentBasename` | From `dbo_Documents.Basename` |
| `FieldRefCount` | Count of linked fields (if available) |
| `zip_rel_path` | Path of matched per‑precedent folder (if any) |
| `match_method` | `filename` / `code_manifest` / `sup_manifest` / `name_value` / `zip_only` |
| `match_confidence` | High / Medium / Low |
| `unmatched_reason` | Categorised reason when no `DocumentID` (see §9) |

This same table is suitable to feed dashboards and to drive LOE.

---

## 8) Algorithm sketch (pseudocode)

```pseudo
for row in Excel:
  extract excel_code, excel_name, excel_filename
  extract val_digits, val_sup (optional “value” mining)

  candidate_filename := coalesce(
    lower(excel_filename),
    excel_code + ".dot",
    lower(excel_name) + ".dot",
    val_digits + ".dot",
    lower(val_sup) + ".dot"
  )

  # try exact filename → Documents
  if Documents.contains(candidate_filename):
     link DocumentID; method="filename"; confidence="High"; continue

  # try Code → Manifest → candidate filename → Documents
  if Manifest.hasCode(excel_code) and Documents.contains(excel_code + ".dot"):
     link DocumentID; method="code_manifest"; confidence="High"; continue

  # try Sup → Manifest → candidate filename → Documents
  if Manifest.hasName(excel_name) and Documents.contains(lower(excel_name) + ".dot"):
     link DocumentID; method="sup_manifest"; confidence="Medium"; continue

  # try "value" mined tokens
  if Documents.contains(val_digits + ".dot" OR val_sup + ".dot"):
     link DocumentID; method="name_value"; confidence="Medium"; continue

  # last resort: per‑precedent folder evidence
  if ZIP.Precedents.contains(excel_code) or ZIP.Precedents.contains(excel_name):
     link zip_rel_path; method="zip_only"; confidence="Low"
  else:
     method="unmatched"; confidence="Low"
```

---

## 9) Unmatched reason taxonomy (for reporting)

When no `DocumentID` was found, bucket by **first true** condition:
1. `No identifier in Excel` (no code/name/filename/value)  
2. `Excel filename not in Documents` (extension mismatch or not exported)  
3. `Excel code not in Manifest` (different library slice or typo)  
4. `Excel name not in Manifest` (variant name or different library)  
5. `Manifest matched but Documents missing` (manifest OK; no `.dot` in current export)  
6. `ZIP‑only evidence` (found the precedent folder, but no DocumentID available)

These categories feed your coverage KPIs and next‑actions.

---

## 10) QA & governance

- **Coverage metrics**: Excel row count, matched `DocumentID` count, ZIP‑only count, unmatched count.  
- **Spot‑checks**: open 5–10 matched templates; verify filename ↔ code/name ↔ field count alignment.  
- **Conflicts**: capture and resolve code vs sup discrepancies; lock to **Code** when in doubt.  
- **Reproducibility**: keep the exact regexes and normalization rules under version control; log `match_method` and all input identifiers per row.

---

## 11) Known constraints

- The provided `ExportSandI.zip` is **metadata‑only** (no Word `.dot` binaries). Use it to confirm precedent existence and paths, not for field analysis.  
- Field‑level LOE requires either `dbo_DocumentFields` + `dbo_Fields` (preferred) or access to the actual `.dot/.docx` templates for parsing.
- Expect Sup names to vary by case/spaces; always normalize.

---

## 12) Minimal column checklist for your report

- IDs: `row_uid`, `__sheet`  
- Extracted keys: `excel_code`, `excel_name`, `excel_filename`, `val_digits`, `val_sup`, `candidate_filename`  
- Resolution: `manifest_code`, `manifest_name`, `DocumentID`, `DocumentBasename`, `zip_rel_path`  
- Status: `match_method`, `match_confidence`, `unmatched_reason`  
- (If available) LOE‑ready: `FieldRefCount`, complexity flags/counters, estimated minutes

---

**Tip:** When you receive additional exports (e.g., missing `.dot` files or a second `DocumentFields/Fields` slice), re‑run the same pipeline: only the final step outcomes change; your audit schema remains stable.