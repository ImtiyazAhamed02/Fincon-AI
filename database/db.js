// db.js - Database client using better-sqlite3
import Database from 'better-sqlite3';
import { readFileSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const dbPath = join(__dirname, 'fincon.db');
const schemaPath = join(__dirname, 'schema.sql');

// Initialize database
const db = new Database(dbPath, { verbose: console.log });

// Enable foreign keys
db.pragma('foreign_keys = ON');

// Read schema and initialize tables if needed
if (existsSync(schemaPath)) {
  const schema = readFileSync(schemaPath, 'utf8');
  db.exec(schema);
} else {
  console.warn('schema.sql not found, tables were not initialized automatically.');
}

export default db;
