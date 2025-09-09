#!/usr/bin/env python3
"""
Backfill channel classifications for Excel rows and Documents.
Requires 08_channels_migration.sql to be applied.
"""
import os
import re
import psycopg2
from pathlib import Path

def load_dotenv_file(path: Path):
    try:
        if path.exists():
            for line in path.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    k, v = line.split('=', 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    os.environ.setdefault(k, v)
    except Exception:
        pass

REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv_file(REPO_ROOT / '.env')

def get_db_config():
    host = os.getenv('Host') or os.getenv('DB_HOST') or 'localhost'
    port = int(os.getenv('Port') or os.getenv('DB_PORT') or '5432')
    name = os.getenv('Database') or os.getenv('DB_NAME') or 'estimatedoc'
    user = os.getenv('User') or os.getenv('DB_USER') or 'estimatedoc_user'
    password = os.getenv('Password') or os.getenv('DB_PASSWORD') or 'estimatedoc_user'
    return {'host': host, 'port': port, 'database': name, 'user': user, 'password': password}

DB_CONFIG = get_db_config()

def classify_text(text: str):
    t = (text or '').lower()
    is_email = bool(re.search(r'\b(e-?mail|outlook|mail to|emailed)\b', t))
    is_letter = bool(re.search(r'\b(letter|ltr|postal|hardcopy|printed|post)\b', t))
    if is_email and is_letter:
        return ['both']
    if is_email:
        return ['email']
    if is_letter:
        return ['letter']
    return ['unknown']

def get_mode_map(cur):
    cur.execute("SELECT id, code FROM communication_modes")
    return {code: mid for (mid, code) in cur.fetchall()}

def backfill_excel(cur, modes):
    cur.execute("SELECT row_id, template_code, description FROM excel_templates")
    rows = cur.fetchall()
    count = 0
    for row_id, code, desc in rows:
        for m in classify_text(f"{code} {desc}"):
            mid = modes.get(m)
            if mid:
                cur.execute(
                    """
                    INSERT INTO excel_template_channels (excel_row_id, mode_id, source)
                    VALUES (%s, %s, 'excel_description')
                    ON CONFLICT (excel_row_id, mode_id) DO NOTHING
                    """,
                    (row_id, mid)
                )
                count += 1
    return count

def backfill_documents(cur, modes):
    cur.execute("SELECT document_id, filename FROM documents")
    rows = cur.fetchall()
    count = 0
    for doc_id, filename in rows:
        for m in classify_text(filename):
            mid = modes.get(m)
            if mid:
                cur.execute(
                    """
                    INSERT INTO document_channels (document_id, mode_id, source)
                    VALUES (%s, %s, 'filename')
                    ON CONFLICT (document_id, mode_id) DO NOTHING
                    """,
                    (doc_id, mid)
                )
                count += 1
    return count

if __name__ == '__main__':
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    modes = get_mode_map(cur)
    excel = backfill_excel(cur, modes)
    docs = backfill_documents(cur, modes)
    conn.commit()
    print(f"Backfilled excel_template_channels: {excel}, document_channels: {docs}")
    cur.close()
    conn.close()
