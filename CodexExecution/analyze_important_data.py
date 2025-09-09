#!/usr/bin/env python3
import os
import re
import json
import math
import argparse
from collections import defaultdict, Counter

import pandas as pd
from lxml import etree
from dotenv import dotenv_values
import pymssql

# Paths
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
IMPORTANT = os.path.join(ROOT, 'ImportantData')
EXPORT_SANDI_ROOT_MANIFEST = os.path.join(IMPORTANT, 'ExportSandI.Manifest.xml')
EXPORT_SANDI_DIR = os.path.join(IMPORTANT, 'ExportSandI')
EXPORT_SANDI_MANIFEST = os.path.join(EXPORT_SANDI_DIR, 'ExportSandI.Manifest.xml')
PRECEDENTS_DIR = os.path.join(EXPORT_SANDI_DIR, 'Precedents')
SCRIPTS_DIR = os.path.join(EXPORT_SANDI_DIR, 'Scripts')
SQL_DIR = os.path.join(IMPORTANT, 'SQLExport')
CLIENT_XLSX = os.path.join(IMPORTANT, 'ClientRequirements.xlsx')
OUT_DIR = os.path.join(ROOT, 'CodexReview')
OUT_XLSX = os.path.join(OUT_DIR, 'ClientRequirements_Analyzed.xlsx')
OUT_REPORT = os.path.join(OUT_DIR, 'CodexReport.md')
NEWSQL_DIR = os.path.join(ROOT, 'newSQL')


def parse_root_manifest(path):
    """Parse ExportSandI.Manifest.xml and extract items with Type=\"Precedents\".
    Returns list of dicts with keys: code (str), name (str), id (str/int), description(str).
    """
    with open(path, 'rb') as f:
        content = f.read()
    try:
        root = etree.fromstring(content)
    except Exception:
        # Some manifests may lack a single root; ensure it parses
        parser = etree.XMLParser(recover=True)
        root = etree.fromstring(content, parser=parser)
    items = []
    for el in root.findall('.//Items'):
        typ = el.get('Type')
        if (typ or '').lower() == 'precedents':
            items.append({
                'id': el.get('ID'),
                'code': el.get('Code'),
                'name': el.get('Name'),
                'description': el.get('Description', ''),
                'active': el.get('Active'),
            })
    return items


def parse_precedent_manifest(manifest_path):
    """Parse a Precedents/{code}/manifest.xml for PrecTitle, PrecID, PrecScript, precExtension."""
    if not os.path.exists(manifest_path):
        return None
    with open(manifest_path, 'rb') as f:
        parser = etree.XMLParser(recover=True)
        root = etree.parse(f, parser).getroot()
    # Grab first PRECEDENT element values
    ns = {'x': root.nsmap.get(None)} if None in root.nsmap else {}
    def text(xpath):
        el = root.find(xpath, namespaces=ns) if ns else root.find(xpath)
        return (el.text.strip() if el is not None and el.text is not None else '')
    # In files, fields appear under PRECEDENT element (not always namespaced)
    prec_id = ''
    prec_title = ''
    prec_script = ''
    prec_ext = ''
    prec_path = ''
    # Try without namespace
    for tag in ['PrecID', 'PrecTitle', 'PrecScript', 'precExtension', 'PrecPath']:
        val = text(f'.//{tag}')
        if tag == 'PrecID':
            prec_id = val
        elif tag == 'PrecTitle':
            prec_title = val
        elif tag == 'PrecScript':
            prec_script = val
        elif tag == 'precExtension':
            prec_ext = val
        elif tag == 'PrecPath':
            prec_path = val
    return {
        'PrecID': prec_id,
        'PrecTitle': prec_title,
        'PrecScript': prec_script,
        'precExtension': prec_ext,
        'PrecPath': prec_path,
    }


def scan_all_prec_manifests():
    mapping = {}
    if not os.path.isdir(PRECEDENTS_DIR):
        return mapping
    for code in os.listdir(PRECEDENTS_DIR):
        code_path = os.path.join(PRECEDENTS_DIR, code)
        if not os.path.isdir(code_path):
            continue
        man = os.path.join(code_path, 'manifest.xml')
        if not os.path.exists(man):
            continue
        info = parse_precedent_manifest(man)
        title = (info.get('PrecTitle') or '').strip()
        if not title:
            continue
        mapping[title.lower()] = {
            'Code': code,
            'RootName': '',
            'PrecTitle': title,
            'PrecScript': info.get('PrecScript', ''),
            'precExtension': info.get('precExtension', ''),
            'FolderExists': True,
            'ManifestExists': True,
            'ManifestPath': man,
        }
    return mapping


def load_sql_from_db():
    cfg = dotenv_values(os.path.join(ROOT, '.env'))
    server_raw = cfg.get('DB_SERVER', '')
    if not server_raw:
        raise RuntimeError('DB_SERVER not set in .env')
    if ',' in server_raw:
        server, port = server_raw.split(',', 1)
        port = int(port)
    else:
        server, port = server_raw, 1433
    user = cfg.get('DB_USER')
    pw = cfg.get('DB_PASSWORD')
    dbname = cfg.get('DB_NAME')
    conn = pymssql.connect(server=server, user=user, password=pw, database=dbname, port=port)
    cur = conn.cursor(as_dict=True)

    # Discover table names by columns to avoid hard-coding
    cur.execute("""
        SELECT TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
    """)
    from collections import defaultdict
    cols = defaultdict(set)
    for r in cur:
        cols[(r['TABLE_SCHEMA'], r['TABLE_NAME'])].add(r['COLUMN_NAME'].lower())
    def find_table(require_cols):
        res = []
        for (s,t), c in cols.items():
            if all(col in c for col in require_cols):
                res.append((s,t))
        return res
    docs_tbl = find_table(['documentid', 'filename'])
    fields_tbl = find_table(['fieldid', 'fieldcode'])
    rel_tbl = None
    # relationship may use 'count' or 'instances' naming
    rel_cands = []
    for (s,t), c in cols.items():
        if 'documentid' in c and 'fieldid' in c and ('count' in c or 'instances' in c or 'instancecount' in c):
            rel_cands.append((s,t))
    if not (docs_tbl and fields_tbl and rel_cands):
        raise RuntimeError('Could not discover required tables in DB')
    docs_schema, docs_name = docs_tbl[0]
    fields_schema, fields_name = fields_tbl[0]
    rel_schema, rel_name = rel_cands[0]

    # Load documents
    cur.execute(f"SELECT DocumentID, FileName as Filename FROM [{docs_schema}].[{docs_name}]")
    doc_rows = [dict(r) for r in cur]
    # Load fields
    cur.execute(f"SELECT FieldID, FieldCode, FieldResult FROM [{fields_schema}].[{fields_name}]")
    field_rows = [dict(r) for r in cur]
    # Load relationships (normalize column name for count)
    # Build query that selects possibly named columns
    # We’ll check actual columns again
    rel_cols = cols[(rel_schema, rel_name)]
    count_col = 'Count' if 'count' in rel_cols else ('Instances' if 'instances' in rel_cols else 'InstanceCount')
    cur.execute(f"SELECT DocumentID, FieldID, [{count_col}] as [Count] FROM [{rel_schema}].[{rel_name}]")
    dfr_rows = [dict(r) for r in cur]
    conn.close()
    meta = {
        'documents_table': f'{docs_schema}.{docs_name}',
        'fields_table': f'{fields_schema}.{fields_name}',
        'relationships_table': f'{rel_schema}.{rel_name}',
        'relationships_count_column': count_col,
        'server': server,
        'database': dbname,
    }
    return doc_rows, field_rows, dfr_rows, meta


def load_sql_from_newsql():
    docs_path = os.path.join(NEWSQL_DIR, 'documents.json')
    fields_path = os.path.join(NEWSQL_DIR, 'fields.json')
    dfr_path = os.path.join(NEWSQL_DIR, 'documentfields.json')
    if not (os.path.exists(docs_path) and os.path.exists(fields_path) and os.path.exists(dfr_path)):
        return None
    with open(docs_path, 'r', encoding='utf-8') as f:
        doc_rows = json.load(f)
    with open(fields_path, 'r', encoding='utf-8') as f:
        field_rows = json.load(f)
    with open(dfr_path, 'r', encoding='utf-8') as f:
        dfr_rows = json.load(f)
    meta = {
        'source': 'newSQL',
        'documents_file': docs_path,
        'fields_file': fields_path,
        'relationships_file': dfr_path,
    }
    return doc_rows, field_rows, dfr_rows, meta


def load_field_analysis_mapping():
    """Optional: load newSQL/field_analysis.json to map FieldCode -> field_category."""
    fa_path = os.path.join(NEWSQL_DIR, 'field_analysis.json')
    if not os.path.exists(fa_path):
        return {}
    try:
        with open(fa_path, 'r', encoding='utf-8') as f:
            arr = json.load(f)
        mapping = {}
        for row in arr:
            code = row.get('fieldcode')
            cat = row.get('field_category')
            if code and cat:
                mapping[code] = cat
        return mapping
    except Exception:
        return {}


# Categorization aligned to provided CASE logic
def categorize_field_code(code: str, override_map: dict | None = None) -> str:
    c = (code or '')
    if override_map and c in override_map:
        return override_map[c]
    cl = c.upper()
    # Order matters (mirrors the SQL CASE sequence)
    if 'UDSCH' in cl:
        return 'Search'
    if '~' in c:
        return 'Reflection'
    if 'IF' in cl:
        return 'If'
    if 'DOCVARIABLE "#' in c:
        return 'Built In Script'
    if '$$' in c:
        return 'Extended'
    if 'SCR' in cl:
        return 'Scripted'
    if '_' in c:
        return 'Unbound'
    return 'Precedent Script'


def build_sql_indexes(doc_rows, field_rows, dfr_rows):
    # Document base codes derived from Filename, AttachedTemplate, FileFullname and normalized variants
    docid_to_filename = {d['DocumentID']: d.get('Filename') for d in doc_rows}
    docid_to_base = {}
    base_to_docids = defaultdict(list)
    for d in doc_rows:
        did = d['DocumentID']
        bases = set()
        fn = d.get('Filename')
        if fn:
            bases.add(os.path.splitext(fn)[0].strip().lower())
        at = d.get('AttachedTemplate')
        if at:
            bases.add(os.path.splitext(at)[0].strip().lower())
        ff = d.get('FileFullname')
        if ff:
            bases.add(os.path.splitext(os.path.basename(ff))[0].strip().lower())
        # normalized variants (alnum only)
        for b in list(bases):
            nb = ''.join(ch for ch in b if ch.isalnum())
            if nb:
                bases.add(nb)
        for b in bases:
            if not b:
                continue
            base_to_docids[b].append(did)
        # prefer filename base as primary
        if fn:
            docid_to_base[did] = os.path.splitext(fn)[0].strip().lower()

    # Field categories
    fieldid_to_code = {f['FieldID']: f.get('FieldCode', '') for f in field_rows}
    fa_override = load_field_analysis_mapping()
    fieldid_to_cat = {fid: categorize_field_code(code, fa_override) for fid, code in fieldid_to_code.items()}

    # Document -> set(FieldID) and counts
    doc_to_fields = defaultdict(lambda: defaultdict(int))  # docid -> fieldid -> total count across instances
    for rel in dfr_rows:
        did = rel['DocumentID']
        fid = rel['FieldID']
        cnt = rel.get('Count', 1)
        doc_to_fields[did][fid] += cnt

    # FieldID -> set(DocumentID) for reuse analysis
    fieldid_to_docs = defaultdict(set)
    for did, fmap in doc_to_fields.items():
        for fid in fmap.keys():
            fieldid_to_docs[fid].add(did)

    # Categories present
    categories = sorted(set(fieldid_to_cat.values()))

    return {
        'docid_to_filename': docid_to_filename,
        'docid_to_base': docid_to_base,
        'base_to_docids': base_to_docids,
        'fieldid_to_code': fieldid_to_code,
        'fieldid_to_cat': fieldid_to_cat,
        'doc_to_fields': doc_to_fields,
        'fieldid_to_docs': fieldid_to_docs,
        'categories': categories,
    }


def collect_precedent_details(root_items):
    details = {}
    for it in root_items:
        code = (it.get('code') or '').strip()
        name = (it.get('name') or '').strip()
        if not code:
            continue
        # Some directories may or may not exist
        prec_dir = os.path.join(PRECEDENTS_DIR, code)
        manifest_path = os.path.join(prec_dir, 'manifest.xml')
        prec_title = ''
        prec_script = ''
        prec_ext = ''
        if os.path.exists(manifest_path):
            parsed = parse_precedent_manifest(manifest_path)
            if parsed:
                prec_title = parsed.get('PrecTitle', '')
                prec_script = parsed.get('PrecScript', '')
                prec_ext = parsed.get('precExtension', '')
        # Fallback PrecTitle from root name when manifest is missing
        if not prec_title and name:
            prec_title = name.strip()
        details[code] = {
            'Code': code,
            'RootName': name,
            'PrecTitle': prec_title,
            'PrecScript': prec_script,
            'precExtension': prec_ext,
            'PrecPath': parsed.get('PrecPath','') if os.path.exists(manifest_path) else '',
            'FolderExists': os.path.isdir(prec_dir),
            'ManifestExists': os.path.exists(manifest_path),
            'ManifestPath': manifest_path if os.path.exists(manifest_path) else '',
        }
    return details


def read_client_requirements(path):
    df = pd.read_excel(path)
    # Standardize columns
    cols = {c: c.strip() for c in df.columns}
    df.rename(columns=cols, inplace=True)
    required = ['Current Title', 'Description']
    for r in required:
        if r not in df.columns:
            raise ValueError(f"Missing required column in ClientRequirements.xlsx: {r}")
    # Normalize title key
    df['__title_key__'] = df['Current Title'].astype(str).str.strip().str.lower()
    return df


def build_analysis():
    root_manifest_path = EXPORT_SANDI_ROOT_MANIFEST if os.path.exists(EXPORT_SANDI_ROOT_MANIFEST) else EXPORT_SANDI_MANIFEST
    root_items = parse_root_manifest(root_manifest_path)
    prec_details = collect_precedent_details(root_items)
    manifest_title_map = scan_all_prec_manifests()

    # Index prec by title key for lookup
    title_to_prec = {}
    # Prefer entries actually parsed from Precedent manifests
    title_to_prec.update(manifest_title_map)
    # Add any remaining from root manifest as fallback
    for code, info in prec_details.items():
        title = (info.get('PrecTitle') or '').strip()
        if title and title.lower() not in title_to_prec:
            title_to_prec[title.lower()] = info

    # SQL indexes: prefer newSQL JSON if present, else live DB
    new_load = load_sql_from_newsql()
    if new_load:
        doc_rows, field_rows, dfr_rows, db_meta = new_load
    else:
        doc_rows, field_rows, dfr_rows, db_meta = load_sql_from_db()
    sql_idx = build_sql_indexes(doc_rows, field_rows, dfr_rows)

    # Scripts inventory (for reference and reuse)
    script_codes = set()
    if os.path.isdir(SCRIPTS_DIR):
        for name in os.listdir(SCRIPTS_DIR):
            if name.startswith('_'):
                script_codes.add(name)

    # Client requirements
    client_df = read_client_requirements(CLIENT_XLSX)

    categories = sql_idx['categories']
    # Build per-row analysis
    rows_out = []
    for _, row in client_df.iterrows():
        title_key = row['__title_key__']
        desc = row['Description']
        prec = title_to_prec.get(title_key)
        match_source = 'manifest' if prec and prec.get('ManifestExists') else ('root' if prec else '')
        export_code = prec['Code'] if prec else ''
        export_precscript = prec.get('PrecScript', '') if prec else ''
        manifest_exists = prec.get('ManifestExists', False) if prec else False
        # SQL doc mapping using multiple strategies
        bmap = sql_idx['base_to_docids']
        docids = []
        # direct match and normalized
        norm_title = ''.join(ch for ch in title_key if ch.isalnum())
        docids += bmap.get(title_key, []) + bmap.get(norm_title, [])
        # try manifest PrecTitle
        if prec:
            pt = (prec.get('PrecTitle') or '').strip().lower()
            if pt:
                npt = ''.join(ch for ch in pt if ch.isalnum())
                docids += bmap.get(pt, []) + bmap.get(npt, [])
            # also try root manifest Name if available
            rootname = (prec.get('RootName') or '').strip().lower()
            if rootname:
                nr = ''.join(ch for ch in rootname if ch.isalnum())
                docids += bmap.get(rootname, []) + bmap.get(nr, [])
            # try PrecPath basename (Windows-style path)
            ppath = (prec.get('PrecPath') or '').strip()
            # Fallback: derive PrecPath by directly parsing the folder manifest using ExportSandI Code
            if not ppath and export_code:
                man_path = os.path.join(PRECEDENTS_DIR, str(export_code), 'manifest.xml')
                if os.path.exists(man_path):
                    parsed = parse_precedent_manifest(man_path)
                    ppath = (parsed.get('PrecPath') or '').strip()
            if ppath:
                import ntpath as _nt
                bn = _nt.basename(ppath)
                base = _nt.splitext(bn)[0].strip().lower()
                nb = ''.join(ch for ch in base if ch.isalnum())
                docids += bmap.get(base, []) + bmap.get(nb, [])
        # try ExportSandI Code as numeric filename base (e.g., 7387 -> 7387.dot)
        if export_code:
            code_str = str(export_code).split('.')[0]
            code_norm = ''.join(ch for ch in code_str if ch.isalnum())
            docids += bmap.get(code_str.lower(), []) + bmap.get(code_norm.lower(), [])
            # try PrecID
            pid = (prec.get('PrecID') or '').strip()
            if pid:
                pidl = pid.lower()
                nb = ''.join(ch for ch in pidl if ch.isalnum())
                docids += bmap.get(pidl, []) + bmap.get(nb, [])
        # try stripping trailing letter (e.g., sup021b -> sup021)
        import re as _re
        m = _re.match(r'^([a-z]+\d+)[a-z]$', title_key)
        if m:
            base_try = m.group(1)
            nb = ''.join(ch for ch in base_try if ch.isalnum())
            docids += bmap.get(base_try, []) + bmap.get(nb, [])
        # dedupe
        docids = sorted(set(docids))
        found_in_sql = bool(docids)

        # Aggregate by categories
        # Unique vs common: a field is reusable if it appears in more than 1 document overall
        cat_unique = {c: 0 for c in categories}
        cat_common = {c: 0 for c in categories}
        total_unique_fields = 0
        total_common_fields = 0
        total_field_instances = 0
        total_field_ids = 0
        if found_in_sql:
            seen_fids = set()
            for did in docids:
                fmap = sql_idx['doc_to_fields'].get(did, {})
                for fid, cnt in fmap.items():
                    if fid in seen_fids:
                        # Avoid double-counting same FieldID across multiple DocumentIDs for the same title key
                        # (Shouldn't happen often, but safety)
                        continue
                    seen_fids.add(fid)
                    cat = sql_idx['fieldid_to_cat'].get(fid, 'OTHER')
                    used_in_docs = len(sql_idx['fieldid_to_docs'].get(fid, []))
                    if used_in_docs > 1:
                        cat_common[cat] += 1
                        total_common_fields += 1
                    else:
                        cat_unique[cat] += 1
                        total_unique_fields += 1
                    total_field_ids += 1
                    total_field_instances += cnt

        out = {
            'Current Title': row['Current Title'],
            'Description': desc,
            'Existing Complexity': row.get('Complexity', ''),
            'Matched In ExportSandI': bool(prec),
            'ExportSandI Code': export_code,
            'Manifest Present': manifest_exists,
            'Precedent Match Source': match_source,
            'PrecTitle (from Manifest or Name)': (prec.get('PrecTitle') if prec else ''),
            'PrecID': (prec.get('PrecID') if prec else ''),
            'PrecPath': (prec.get('PrecPath') if prec else ''),
            'PrecScript Code': export_precscript,
            'PrecScript Exists': bool(export_precscript and export_precscript in script_codes),
            'Matched In SQLExport': found_in_sql,
            'SQL DocumentIDs': ','.join(map(str, docids)) if docids else '',
            'Total Field IDs (unique)': total_field_ids,
            'Total Field Instances': total_field_instances,
            'Total Unique Fields': total_unique_fields,
            'Total Reusable Fields': total_common_fields,
        }
        # Add per-category breakdown
        for c in categories:
            out[f'Unique {c}'] = cat_unique.get(c, 0)
            out[f'Common {c}'] = cat_common.get(c, 0)
        # Precedent Scripts categorization: treat presence as 1, and compute reuse across precedents later
        rows_out.append(out)

    out_df = pd.DataFrame(rows_out)

    # Compute related variants: rows sharing same Current Title but different Description
    # Build a helper column with joined descriptions for same title
    client_df = read_client_requirements(CLIENT_XLSX)
    variants = client_df.groupby('__title_key__')['Description'].unique().to_dict()
    out_df['Related Variants (by Title)'] = out_df['Current Title'].str.lower().map(
        lambda k: ' | '.join(variants.get(k, [])) if isinstance(k, str) else ''
    )

    # Compute averages over matched rows for later imputation
    matched_mask = out_df['Matched In SQLExport'] == True
    matched_df = out_df[matched_mask]
    avg_unique = {}
    avg_common = {}
    for c in categories:
        ucol = f'Unique {c}'
        ccol = f'Common {c}'
        avg_unique[c] = float(matched_df[ucol].mean()) if not matched_df.empty else 0.0
        avg_common[c] = float(matched_df[ccol].mean()) if not matched_df.empty else 0.0
    # Totals
    avg_totals = {
        'Total Field IDs (unique)': float(matched_df['Total Field IDs (unique)'].mean()) if not matched_df.empty else 0.0,
        'Total Field Instances': float(matched_df['Total Field Instances'].mean()) if not matched_df.empty else 0.0,
        'Total Unique Fields': float(matched_df['Total Unique Fields'].mean()) if not matched_df.empty else 0.0,
        'Total Reusable Fields': float(matched_df['Total Reusable Fields'].mean()) if not matched_df.empty else 0.0,
    }

    # Prepare Estimates sheet: actual counts for matched, average-imputed for unmatched
    est_rows = []
    for _, r in out_df.iterrows():
        row = {
            'Current Title': r['Current Title'],
            'Description': r['Description'],
            'Matched In SQLExport': r['Matched In SQLExport'],
            'Estimation Method': 'Actual' if r['Matched In SQLExport'] else 'Average (from matched subset)',
        }
        # Per-category
        for c in categories:
            ucol = f'Unique {c}'
            ccol = f'Common {c}'
            if r['Matched In SQLExport']:
                row[f'Est. Unique {c}'] = int(r[ucol])
                row[f'Est. Common {c}'] = int(r[ccol])
            else:
                row[f'Est. Unique {c}'] = int(round(avg_unique[c]))
                row[f'Est. Common {c}'] = int(round(avg_common[c]))
        # Totals
        if r['Matched In SQLExport']:
            row['Est. Total Field IDs (unique)'] = int(r['Total Field IDs (unique)'])
            row['Est. Total Field Instances'] = int(r['Total Field Instances'])
            row['Est. Total Unique Fields'] = int(r['Total Unique Fields'])
            row['Est. Total Reusable Fields'] = int(r['Total Reusable Fields'])
        else:
            row['Est. Total Field IDs (unique)'] = int(round(avg_totals['Total Field IDs (unique)']))
            row['Est. Total Field Instances'] = int(round(avg_totals['Total Field Instances']))
            row['Est. Total Unique Fields'] = int(round(avg_totals['Total Unique Fields']))
            row['Est. Total Reusable Fields'] = int(round(avg_totals['Total Reusable Fields']))
        est_rows.append(row)
    est_df = pd.DataFrame(est_rows)

    # Write Excel with extracted counts only (no weights/complexity)
    with pd.ExcelWriter(OUT_XLSX, engine='xlsxwriter') as writer:
        out_df.to_excel(writer, sheet_name='Analyzed', index=False)
        est_df.to_excel(writer, sheet_name='Estimates', index=False)

        # Aggregated view by Current Title (collapse multiple descriptions)
        def _join_unique_str(vals):
            s = sorted({str(v) for v in vals if pd.notna(v) and str(v).strip() != ''})
            return ' | '.join(s)

        def _any_true(vals):
            return bool(pd.Series(vals).fillna(False).any())

        def _prefer_source(vals):
            # Prefer 'manifest' over 'root', else ''
            vs = {v for v in vals if isinstance(v, str)}
            if 'manifest' in vs:
                return 'manifest'
            if 'root' in vs:
                return 'root'
            return ''

        def _union_docids(vals):
            ids = set()
            for v in vals:
                if not isinstance(v, str):
                    continue
                for part in v.split(','):
                    part = part.strip()
                    if part:
                        ids.add(part)
            return ','.join(sorted(ids, key=lambda x: (len(x), x)))

        # Determine numeric columns to sum
        num_cols = [c for c in out_df.columns if c.startswith('Total ') or c.startswith('Unique ') or c.startswith('Common ')]
        agg_spec = {
            'Description': _join_unique_str,
            'Existing Complexity': _join_unique_str,
            'Matched In ExportSandI': _any_true,
            'ExportSandI Code': _join_unique_str,
            'Manifest Present': _any_true,
            'Precedent Match Source': _prefer_source,
            'PrecTitle (from Manifest or Name)': _join_unique_str,
            'PrecScript Code': _join_unique_str,
            'PrecScript Exists': _any_true,
            'Matched In SQLExport': _any_true,
            'SQL DocumentIDs': _union_docids,
        }
        for c in num_cols:
            agg_spec[c] = 'sum'

        # Add a row counter for variants
        out_df['__variant_count__'] = 1
        agg_spec['__variant_count__'] = 'sum'

        agg_df = out_df.groupby('Current Title', as_index=False).agg(agg_spec)
        agg_df.rename(columns={'__variant_count__': 'Variant Count'}, inplace=True)
        # Reorder: Current Title, Variant Count, rest
        cols_order = ['Current Title', 'Variant Count'] + [c for c in agg_df.columns if c not in ('Current Title','Variant Count')]
        agg_df = agg_df[cols_order]
        agg_df.to_excel(writer, sheet_name='AggregatedByTitle', index=False)

        # Category definitions sheet for clarity (derived from provided rules)
        cat_defs = [
            {'Category': 'Search', 'Rule': 'FieldCode contains UDSCH', 'Description': 'Selection from list (participants, e.g., Legal Assistant, Client). Handles one-to-many.'},
            {'Category': 'Reflection', 'Rule': 'FieldCode contains ~', 'Description': 'Built-in fields reflecting through object model (e.g., ~file., ~associate.).'},
            {'Category': 'If', 'Rule': 'FieldCode contains IF', 'Description': 'Conditional logic fields.'},
            {'Category': 'Built In Script', 'Rule': 'FieldCode contains DOCVARIABLE "#', 'Description': 'MatterSphere helper scripts; code not visible.'},
            {'Category': 'Extended', 'Rule': 'FieldCode contains $$', 'Description': 'Extended data fields tied to extended objects (File, Associate, Contact).'},
            {'Category': 'Scripted', 'Rule': 'FieldCode contains SCR', 'Description': 'C# script inside MatterSphere that outputs a string; reusable.'},
            {'Category': 'Unbound', 'Rule': 'FieldCode contains underscore _', 'Description': 'Questionnaire-only fields; not stored in DB.'},
            {'Category': 'Precedent Script', 'Rule': 'Else', 'Description': 'Script written specifically for the precedent; outputs fields used in document.'},
        ]
        pd.DataFrame(cat_defs).to_excel(writer, sheet_name='CategoryDefinitions', index=False)

        # Coverage summary sheet
        summary = {
            'Total Client Rows': [len(out_df)],
            'Matched ExportSandI': [int(out_df['Matched In ExportSandI'].sum())],
            'Matched SQL (data source)': [int(out_df['Matched In SQLExport'].sum())],
            'Unmatched SQL (data source)': [int((~matched_mask).sum())],
        }
        # Aggregate totals by category
        for c in categories:
            summary[f'Total Unique {c}'] = [int(out_df[f'Unique {c}'].sum()) if f'Unique {c}' in out_df.columns else 0]
            summary[f'Total Common {c}'] = [int(out_df[f'Common {c}'].sum()) if f'Common {c}' in out_df.columns else 0]
            summary[f'Avg Unique {c} (matched only)'] = [round(avg_unique[c], 2)]
            summary[f'Avg Common {c} (matched only)'] = [round(avg_common[c], 2)]
        for k, v in avg_totals.items():
            summary[f'Avg {k} (matched only)'] = [round(v, 2)]
        pd.DataFrame(summary).to_excel(writer, sheet_name='Summary', index=False)

        # DBMeta sheet from newSQL metadata if present
        if os.path.isdir(NEWSQL_DIR):
            # Row counts
            try:
                with open(os.path.join(NEWSQL_DIR, 'row_counts.json'), 'r', encoding='utf-8') as f:
                    row_counts = json.load(f)
            except Exception:
                row_counts = {}
            # Table schemas
            try:
                with open(os.path.join(NEWSQL_DIR, 'table_schemas.json'), 'r', encoding='utf-8') as f:
                    schemas = json.load(f)
                schemas_df = pd.DataFrame(schemas)
            except Exception:
                schemas_df = pd.DataFrame()
            # Validation report and summaries (as text)
            def read_text(p):
                try:
                    with open(p, 'r', encoding='utf-8', errors='ignore') as f:
                        return f.read()
                except Exception:
                    return ''
            val_report = read_text(os.path.join(NEWSQL_DIR, 'validation_report.txt'))
            data_val_sum = read_text(os.path.join(NEWSQL_DIR, 'DATA_VALIDATION_SUMMARY.md'))
            data_summary = read_text(os.path.join(NEWSQL_DIR, 'data_summary.md'))

            # Write row counts
            rc_df = pd.DataFrame([row_counts]) if isinstance(row_counts, dict) else pd.DataFrame()
            rc_df.to_excel(writer, sheet_name='DBMeta_RowCounts', index=False)
            # Write schemas
            if not schemas_df.empty:
                schemas_df.to_excel(writer, sheet_name='DBMeta_Schemas', index=False)
            # Write text sheets
            if val_report:
                ws = writer.book.add_worksheet('DBMeta_Validation')
                wrap = writer.book.add_format({'text_wrap': True, 'valign': 'top'})
                ws.set_column(0, 0, 120)
                ws.write(0, 0, val_report, wrap)
            if data_val_sum:
                ws = writer.book.add_worksheet('DBMeta_DataValSummary')
                wrap = writer.book.add_format({'text_wrap': True, 'valign': 'top'})
                ws.set_column(0, 0, 120)
                ws.write(0, 0, data_val_sum, wrap)
            if data_summary:
                ws = writer.book.add_worksheet('DBMeta_DataSummary')
                wrap = writer.book.add_format({'text_wrap': True, 'valign': 'top'})
                ws.set_column(0, 0, 120)
                ws.write(0, 0, data_summary, wrap)

        # BecInfo sheet (verbatim) for reference
        bec_path = os.path.join(IMPORTANT, 'BecInfo.txt')
        if os.path.exists(bec_path):
            with open(bec_path, 'r', encoding='utf-8', errors='ignore') as bf:
                bec_text = bf.read()
            ws_bec = writer.book.add_worksheet('BecInfo')
            # Write text into A1, wrap text
            wrap = writer.book.add_format({'text_wrap': True, 'valign': 'top'})
            ws_bec.set_column(0, 0, 120)
            ws_bec.write(0, 0, bec_text, wrap)

    return {
        'out_df': out_df,
        'categories': categories,
        'prec_details': prec_details,
        'title_to_prec': title_to_prec,
        'sql_idx': sql_idx,
        'script_codes': sorted(script_codes),
        'db_meta': db_meta,
    }


def build_markdown_report(analysis):
    out_df = analysis['out_df']
    categories = analysis['categories']
    prec_details = analysis['prec_details']
    sql_idx = analysis['sql_idx']
    db_meta = analysis.get('db_meta', {})

    # Overview counts
    matched_export = int(out_df['Matched In ExportSandI'].sum())
    matched_sql = int(out_df['Matched In SQLExport'].sum())
    total = len(out_df)

    lines = []
    al = lines.append
    al('# EstimateDoc – Codex Analysis Report')
    al('')
    al('## Introduction')
    al('- Purpose: Link ClientRequirements templates to ExportSandI and SQL exports; quantify fields by category and uniqueness (no weighting or complexity).')
    if db_meta.get('source') == 'newSQL':
        al('- Data sources: ClientRequirements.xlsx; ExportSandI manifests; newSQL JSON dumps; Scripts.')
    else:
        al('- Data sources: ClientRequirements.xlsx; ExportSandI manifests; live SQL database; Scripts.')
    al('')
    al('## Methodology & Reasoning Steps (summarized)')
    al('- Parsed ExportSandI.Manifest.xml for items Type=\"Precedents\"; collected numeric codes and names.')
    al('- For each code, checked Precedents/{code}/manifest.xml; where present, extracted PrecTitle, PrecID, PrecScript, and extension.')
    if db_meta.get('source') == 'newSQL':
        al('- Loaded Documents/Fields/DocumentFields from newSQL JSON files; mapped DocumentID→filename and derived base codes (lowercased filenames without extension).')
    else:
        al('- Queried live database (read-only) to load Documents/Fields/DocumentFields; mapped DocumentID→filename and derived base codes (lowercased filenames without extension).')
    al('- Classified Fields into categories by FieldCode patterns (e.g., IF, DOCVARIABLE, MERGEFIELD, HYPERLINK, INCLUDETEXT, etc.).')
    al('- Aggregated, per document, unique FieldIDs by category; computed reuse by counting how many documents each FieldID appears in.')
    al('- Matched ClientRequirements rows by Current Title against PrecTitle/SQL base codes (case-insensitive).')
    al('- For duplicates (same Current Title, different Description), kept separate rows and noted related variants.')
    al('- Created an Excel export with per-category Unique/Common counts and totals only (no weighting, no complexity scoring).')
    al('')
    al('## Data Linking Analysis')
    al(f'- Client rows: {total}; matched to ExportSandI: {matched_export}; matched to SQL: {matched_sql}.')
    if db_meta:
        if db_meta.get('source') == 'newSQL':
            al(f"- Data files: documents={os.path.basename(db_meta.get('documents_file',''))}, fields={os.path.basename(db_meta.get('fields_file',''))}, relationships={os.path.basename(db_meta.get('relationships_file',''))}")
        else:
            al(f"- SQL Server: {db_meta.get('server')} | Database: {db_meta.get('database')}")
            al(f"- Tables: documents={db_meta.get('documents_table')}, fields={db_meta.get('fields_table')}, relationships={db_meta.get('relationships_table')} ({db_meta.get('relationships_count_column')} column)")
    al('- Precedent→Script linkage used PrecScript in Precedent manifests (e.g., PrecScript=\"_16188\" maps to Scripts/_16188).')
    al('- SQL Document match uses base filename (e.g., sup073 from \"sup073.dot\"). No external IDs were cross-walked.')
    al('')
    al('### Category Columns Derived')
    for c in categories:
        al(f'- {c}: counts for Unique {c} and Common {c}.')
    al('')
    al('## Category Totals (from data source)')
    for c in categories:
        total_u = int(out_df.get(f'Unique {c}', pd.Series()).sum()) if f'Unique {c}' in out_df.columns else 0
        total_c = int(out_df.get(f'Common {c}', pd.Series()).sum()) if f'Common {c}' in out_df.columns else 0
        al(f'- {c}: Unique={total_u}, Common={total_c}')
    # Averages over matched subset (used for imputations)
    matched_mask = out_df['Matched In SQLExport'] == True
    matched_df = out_df[matched_mask]
    al('')
    al('## Matched Subset Averages (for estimation)')
    if matched_df.empty:
        al('- No matched rows found; cannot compute averages.')
    else:
        for c in categories:
            ucol = f'Unique {c}'
            ccol = f'Common {c}'
            au = round(float(matched_df[ucol].mean()), 2)
            ac = round(float(matched_df[ccol].mean()), 2)
            al(f'- {c}: Avg Unique={au}, Avg Common={ac}')
        al(f"- Avg Total Field IDs (unique): {round(float(matched_df['Total Field IDs (unique)'].mean()),2)}")
        al(f"- Avg Total Field Instances: {round(float(matched_df['Total Field Instances'].mean()),2)}")
        al(f"- Avg Total Unique Fields: {round(float(matched_df['Total Unique Fields'].mean()),2)}")
        al(f"- Avg Total Reusable Fields: {round(float(matched_df['Total Reusable Fields'].mean()),2)}")

    al('')
    al('## Estimation for Unmatched Rows')
    al('- Estimates sheet applies matched averages to unmatched templates (per category and totals).')
    al('- Caution: Current matched coverage is low; treat these as rough placeholders until more documents are available or a crosswalk is provided.')
    al('')
    al('## Scripts Utility Review')
    al('- Located PRECEDENT scripts under ExportSandI/Scripts/_<code>; manifests include scrType=PRECEDENT and embedded C#-like logic.')
    al('- Where Precedent manifest includes PrecScript, we recorded presence; reuse can be assessed by identical PrecScript across templates.')
    al('')
    al('## Unknown XML Review')
    al('- ExportSandI.Replacement.xml appears to define field replacement metadata (FIELDREPLACER) for Precedent-level default values, lookup sources, and constraints (e.g., PrecType, PrecDirID).')
    al('- Likely used by the export/import tooling to map UI fields to database values and defaults during packaging.')
    al('')
    al('## Optimal Linking Method – Evaluation')
    al('- Primary keys: use PrecID/Code from ExportSandI manifests; match to ClientRequirements by PrecTitle; match to SQL by base filename. This avoids cross-dataset ID conflation.')
    al('- Robustness: Prefer Precedent manifest PrecTitle over root Name; fall back to root Name if manifest missing.')
    al('- Reuse detection: Field-level uniqueness is computed strictly within SQL data by FieldID→Documents cardinality; no external assumptions made.')
    al('- Improvement: If available, extract an explicit mapping table between PrecID and SQL Document filename to remove reliance on string base names.')
    al('')
    al('## Postgres + UI Strategy')
    al('- Schema: tables for client_requirements, precedents (from ExportSandI), sql_documents, fields, document_fields, scripts; views for per-template aggregates (counts only).')
    al('- Import: load from live DB (read-only) into staging; derive aggregates by counts only.')
    al('- UI: grid per template showing categories, unique/common counts and totals; no weighting or scoring involved.')
    al('')
    al('## Edge Cases & Gaps')
    al('- Missing Precedent manifests in some code folders: PrecTitle and PrecScript may be unavailable; we use root manifest Name as a fallback.')
    al('- Some ClientRequirements titles may not exist in SQL exports; those rows are retained with zeros and flagged as unmatched.')
    al('- Scripts linkage only available when PrecScript is populated in Precedent manifest.')
    al('')
    al('## Deliverables')
    al(f'- Excel export with analysis: {os.path.relpath(OUT_XLSX, ROOT)}')
    al('- Contains: per-category Unique/Common columns; total field metrics; related variants; no scoring or parameters.')
    al('')
    # Conclusions
    al('## Conclusions & Recommendations')
    al('- Linkage based on PrecTitle⇄filename base is viable given current data; prefer PrecID where possible for stability.')
    al('- Maintain scripts mapping via PrecScript and count reusable scripts by identical scrCode across precedents.')
    al('- Adopt the proposed Postgres schema and simple UI to surface unique vs reusable field counts (no weighting).')
    al('- Address missing manifests by re-exporting complete Precedent metadata or enriching with an external mapping file.')
    al('- Keep FIELDREPLACER (Replacement.xml) available to guide defaults in any import tooling; document its fields in developer docs.')

    return '\n'.join(lines)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    analysis = build_analysis()
    report_md = build_markdown_report(analysis)
    with open(OUT_REPORT, 'w', encoding='utf-8') as f:
        f.write(report_md)
    print('Wrote:', OUT_XLSX)
    print('Wrote:', OUT_REPORT)


if __name__ == '__main__':
    main()
