import { readFileSync } from 'fs';
import { resolve } from 'path';
import { Pool } from 'pg';
import dotenv from 'dotenv';

dotenv.config();

async function main() {
  const pool = new Pool({
    host: process.env.DB_HOST || 'localhost',
    port: parseInt(process.env.DB_PORT || '5432'),
    database: process.env.DB_NAME || 'estimatedoc',
    user: process.env.DB_USER || 'estimatedoc_user',
    password: process.env.DB_PASSWORD || 'estimatedoc_user',
  });

  try {
    const schemaPath = resolve(__dirname, '../../../sql/01_create_schema.sql');
    const schemaSql = readFileSync(schemaPath, 'utf8');
    await pool.query(schemaSql);
    // Optional: Insert minimal records if desired; schema alone allows zero-count endpoints to work.
    // You can extend with additional inserts here or provide a separate seed SQL file.
    // Example minimal seed could be loaded similarly.
    // const seedPath = resolve(__dirname, '../../../sql/minimal_seed.sql');
    // const seedSql = readFileSync(seedPath, 'utf8');
    // await pool.query(seedSql);
    console.log('Schema applied successfully.');
  } finally {
    await pool.end();
  }
}

main().catch((err) => {
  console.error('Seed failed:', err);
  process.exit(1);
});

