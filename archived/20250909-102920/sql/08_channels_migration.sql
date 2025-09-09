-- Channel-aware schema migration

BEGIN;

-- Communication modes lookup
CREATE TABLE IF NOT EXISTS communication_modes (
  id SERIAL PRIMARY KEY,
  code VARCHAR(20) UNIQUE NOT NULL, -- letter|email|both|unknown
  label VARCHAR(50) NOT NULL
);

-- Excel row to channel mapping (one row can imply multiple modes)
CREATE TABLE IF NOT EXISTS excel_template_channels (
  id SERIAL PRIMARY KEY,
  excel_row_id INTEGER NOT NULL REFERENCES excel_templates(row_id) ON DELETE CASCADE,
  mode_id INTEGER NOT NULL REFERENCES communication_modes(id) ON DELETE RESTRICT,
  source VARCHAR(50) NOT NULL DEFAULT 'excel_description', -- excel_description|manual_override
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (excel_row_id, mode_id)
);
CREATE INDEX IF NOT EXISTS idx_excel_template_channels_row ON excel_template_channels(excel_row_id);
CREATE INDEX IF NOT EXISTS idx_excel_template_channels_mode ON excel_template_channels(mode_id);

-- Document to channel mapping (documents can be used for multiple modes in edge cases)
CREATE TABLE IF NOT EXISTS document_channels (
  id SERIAL PRIMARY KEY,
  document_id INTEGER NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
  mode_id INTEGER NOT NULL REFERENCES communication_modes(id) ON DELETE RESTRICT,
  source VARCHAR(50) NOT NULL DEFAULT 'filename', -- filename|manifest_name|content|override
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (document_id, mode_id)
);
CREATE INDEX IF NOT EXISTS idx_document_channels_doc ON document_channels(document_id);
CREATE INDEX IF NOT EXISTS idx_document_channels_mode ON document_channels(mode_id);

-- Persist mode on matches for stable reporting
DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name='template_matches' AND column_name='mode_id'
  ) THEN
    ALTER TABLE template_matches
      ADD COLUMN mode_id INTEGER NULL REFERENCES communication_modes(id) ON DELETE RESTRICT;
  END IF;
END $$;
CREATE INDEX IF NOT EXISTS idx_template_matches_mode ON template_matches(mode_id);

-- Ensure one match row per excel_row_id to support upserts
DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_indexes WHERE schemaname = 'public' AND indexname = 'uq_template_matches_excel_row'
  ) THEN
    CREATE UNIQUE INDEX uq_template_matches_excel_row ON template_matches(excel_row_id);
  END IF;
END $$;

-- Seed modes
INSERT INTO communication_modes (code, label)
VALUES
  ('letter','Letter'),
  ('email','Email'),
  ('both','Both'),
  ('unknown','Unknown')
ON CONFLICT (code) DO NOTHING;

COMMIT;
