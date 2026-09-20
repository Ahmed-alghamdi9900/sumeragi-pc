"""Local evidence registry and portable exports; no game bytes are stored here."""
import argparse
import csv
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOGS = {
    'FUNCTION_DATABASE': 'Address,Original ID,Current Name,Probable Purpose,Subsystem,Arguments,Return Type,Calling Convention,Callers,Callees,Global References,String References,Structures Used,Confidence,Decompilation Status,Reimplementation Status,Tests,Notes',
    'STRUCTURE_DATABASE': 'ID,Name,Field Offset,Field Size,Type,Relationships,Serialization,Confidence,Functions,Evidence',
    'SYMBOL_DATABASE': 'ID,Address,Name,Subsystem,Confidence,Evidence',
    'ASSET_DATABASE': 'ID,Source Path,SHA256,Format,Subsystem,Status,Evidence',
    'SHADER_DATABASE': 'ID,Stage,Source Asset,Format,Resources,Constants,Variants,PC Shader,Status,Tests,Evidence',
    'AUDIO_DATABASE': 'ID,Source Path,Format,Codec,Loop,Status,Evidence',
    'SCRIPT_DATABASE': 'ID,Source Path,Format,Status,Evidence',
    'LOCALIZATION_DATABASE': 'String ID,Resource,Offset,Japanese,Reading,Speaker,Route,Scene,Screen,Character Limit,English,Confidence,Status,Notes',
    'TEST_DATABASE': 'ID,Subsystem,Command,Expected,Actual,Status,Evidence',
    'ANNIVERSARY_CONTENT_MANIFEST': 'ID,Content,Physical Evidence,Official Reference,Canonical Status,Validation Status,Notes',
    'GAME_COMPLETION_MATRIX': 'Character,Route,Stage,Boss,Ending,Difficulty,Feature,Status,Evidence',
    'TRANSLATION_STATUS': 'Resource,Total,Translated,Reviewed,Unresolved,Status,Evidence',
    'PERFORMANCE_RESULTS': 'ID,Commit,Source Build,Hardware,Driver,Scene,Settings,Average FPS,1% Low,0.1% Low,Frame Time Variance,Stutters,Memory,VRAM,Evidence',
    'GRAPHICS_FEATURE_MATRIX': 'Feature,Original PS4 Behavior,PC Implementation,Minimum,Medium,High,Ultra,Maximum,Performance Cost,VRAM Cost,Visual Difference,Validation Status,Known Issues,Notes',
    'BASARA_TRANSLATION_MEMORY': 'ID,Japanese,English,Context,Confidence,Status,Evidence',
    'BASARA_GLOSSARY': 'Japanese,English,Category,Official Reference,Status',
    'UI_TEXTURE_TEXT_INDEX': 'ID,Source,Region,OCR,Verified Text,English,Status,Evidence',
}

@contextmanager
def connect(root):
    db = sqlite3.connect(root / 'SUMERAGI_PROJECT.sqlite')
    db.execute('PRAGMA foreign_keys=ON')
    db.executescript('''
      CREATE TABLE IF NOT EXISTS evidence (
        id TEXT PRIMARY KEY, category TEXT NOT NULL, status TEXT NOT NULL,
        claim TEXT NOT NULL, artifact TEXT, created_utc TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS knowledge (
        id TEXT PRIMARY KEY, kind TEXT NOT NULL, identifier TEXT,
        subsystem TEXT, confidence TEXT NOT NULL, data_json TEXT NOT NULL,
        evidence_id TEXT REFERENCES evidence(id));
      CREATE TABLE IF NOT EXISTS files (
        scan_id TEXT NOT NULL, path TEXT NOT NULL, sha256 TEXT,
        size INTEGER, format TEXT, status TEXT, metadata_json TEXT,
        PRIMARY KEY(scan_id,path));
      CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY,value TEXT);
    ''')
    try:
        db.execute('CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(id UNINDEXED, text)')
        db.executescript('''
          CREATE TRIGGER IF NOT EXISTS knowledge_ai AFTER INSERT ON knowledge BEGIN
            INSERT INTO knowledge_fts VALUES (new.id, new.kind || ' ' || coalesce(new.identifier,'') || ' ' || coalesce(new.subsystem,'') || ' ' || new.data_json);
          END;
          CREATE TRIGGER IF NOT EXISTS knowledge_ad AFTER DELETE ON knowledge BEGIN
            DELETE FROM knowledge_fts WHERE id=old.id;
          END;
          CREATE TRIGGER IF NOT EXISTS knowledge_au AFTER UPDATE ON knowledge BEGIN
            DELETE FROM knowledge_fts WHERE id=old.id;
            INSERT INTO knowledge_fts VALUES (new.id, new.kind || ' ' || coalesce(new.identifier,'') || ' ' || coalesce(new.subsystem,'') || ' ' || new.data_json);
          END;
        ''')
        db.execute("INSERT OR REPLACE INTO settings VALUES ('fts5','available')")
    except sqlite3.OperationalError:
        db.execute("INSERT OR REPLACE INTO settings VALUES ('fts5','unavailable')")
    try:
        with db:
            yield db
    finally:
        db.close()

def import_scan(root, report, scan_id):
    """Import our own metadata report transactionally; never extract ZIP contents."""
    summary = json.loads((report / 'summary.json').read_text(encoding='utf-8'))
    with connect(root) as db:
        db.execute('INSERT INTO evidence VALUES (?,?,?,?,?,?)', (
            scan_id, 'inventory', 'COMPLETE_SCAN' if summary.get('complete') else 'INCOMPLETE_SCAN',
            json.dumps(summary, ensure_ascii=False), str(report.relative_to(root)),
            datetime.now(timezone.utc).isoformat()))
        with (report / 'manifest.jsonl').open(encoding='utf-8') as f:
            for line in f:
                entry = json.loads(line)
                db.execute('INSERT INTO files VALUES (?,?,?,?,?,?,?)', (
                    scan_id, entry['path'], entry.get('sha256'), entry.get('size'),
                    entry.get('signature'), entry.get('status'),
                    json.dumps(entry.get('metadata', {}), ensure_ascii=False)))

def search(root, query):
    with connect(root) as db:
        return db.execute('SELECT id,text FROM knowledge_fts WHERE knowledge_fts MATCH ? LIMIT 50', (query,)).fetchall()

def init(root):
    root.mkdir(parents=True, exist_ok=True)
    with connect(root) as db:
        db.execute('INSERT OR IGNORE INTO evidence VALUES (?,?,?,?,?,?)', (
            'startup-source', 'source', 'UNVERIFIED',
            'User identifies canonical source as PS4 Anniversary Edition; internal build unverified.',
            'docs/CANONICAL_PROJECT_INSTRUCTIONS.md', datetime.now(timezone.utc).isoformat()))
    for name, columns in CATALOGS.items():
        p = root / (name + '.csv')
        if not p.exists():
            with p.open('w', encoding='utf-8', newline='') as f:
                csv.writer(f).writerow(columns.split(','))

def export(root):
    destination = root / 'local' / 'memory_exports'
    destination.mkdir(parents=True, exist_ok=True)
    with connect(root) as db:
        db.row_factory = sqlite3.Row
        tables = {}
        for table in ('evidence', 'knowledge', 'files', 'settings'):
            cursor = db.execute('SELECT * FROM ' + table + ' ORDER BY 1,2')
            columns = [c[0] for c in cursor.description]
            rows = [dict(r) for r in cursor]
            tables[table] = rows
            with (destination / (table + '.csv')).open('w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=columns)
                writer.writeheader()
                writer.writerows(rows)
            with (destination / (table + '.jsonl')).open('w', encoding='utf-8') as f:
                for row in rows:
                    f.write(json.dumps(row, ensure_ascii=False) + '\n')
        (destination / 'memory.json').write_text(json.dumps(tables, ensure_ascii=False, indent=2), encoding='utf-8')
        (destination / 'README.md').write_text(
            '# Local memory export\n\n' + '\n'.join(f'- {k}: {len(v)} records' for k,v in tables.items()) +
            '\n\nPrivate generated metadata; review before sharing.\n', encoding='utf-8')
    return destination

def record(root, identifier, category, status, claim, artifact):
    with connect(root) as db:
        db.execute('INSERT INTO evidence VALUES (?,?,?,?,?,?)', (
            identifier, category, status, claim, artifact, datetime.now(timezone.utc).isoformat()))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['init', 'export', 'record', 'import-scan', 'search'])
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--id')
    parser.add_argument('--category', default='inspection')
    parser.add_argument('--status', default='UNKNOWN')
    parser.add_argument('--claim')
    parser.add_argument('--artifact', default='')
    parser.add_argument('--report', type=Path)
    parser.add_argument('--query')
    args = parser.parse_args()
    if args.action == 'init':
        init(args.root)
    elif args.action == 'export':
        print(export(args.root))
    elif args.action == 'import-scan':
        if not args.id or not args.report:
            parser.error('import-scan requires --id and --report')
        import_scan(args.root.resolve(), args.report.resolve(), args.id)
    elif args.action == 'search':
        if not args.query:
            parser.error('search requires --query')
        print(json.dumps(search(args.root, args.query), ensure_ascii=False, indent=2))
    else:
        if not args.id or not args.claim:
            parser.error('record requires --id and --claim')
        record(args.root,args.id,args.category,args.status,args.claim,args.artifact)

if __name__ == '__main__':
    main()
