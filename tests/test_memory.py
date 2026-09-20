import importlib.util
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('memory', Path(__file__).resolve().parents[1] / 'tools/project_memory.py')
memory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(memory)

class MemoryTests(unittest.TestCase):
    def test_search_tracks_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            memory.init(root)
            with memory.connect(root) as db:
                if db.execute("SELECT value FROM settings WHERE key='fts5'").fetchone()[0] != 'available':
                    self.skipTest('SQLite build lacks FTS5')
                db.execute("INSERT INTO knowledge VALUES ('k1','function','0x123','audio','UNKNOWN','voice candidate','startup-source')")
            self.assertEqual(memory.search(root, 'voice')[0][0], 'k1')
            with memory.connect(root) as db:
                db.execute("UPDATE knowledge SET data_json='music candidate' WHERE id='k1'")
            self.assertEqual(memory.search(root, 'voice'), [])
            self.assertEqual(len(memory.search(root, 'music')), 1)
            with memory.connect(root) as db:
                db.execute("DELETE FROM knowledge WHERE id='k1'")
            self.assertEqual(memory.search(root, 'music'), [])

    def test_scan_import_rolls_back_invalid_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            memory.init(root)
            report = root / 'reports'
            report.mkdir()
            (report / 'summary.json').write_text('{"complete":true}')
            entry = {'path':'synthetic','kind':'file','size':3,'sha256':'synthetic-only','signature':'unknown','status':'ok'}
            (report / 'manifest.jsonl').write_text(json.dumps(entry)+'\n'+json.dumps(entry)+'\n')
            with self.assertRaises(sqlite3.IntegrityError):
                memory.import_scan(root,report,'scan-1')
            with memory.connect(root) as db:
                self.assertEqual(db.execute('SELECT COUNT(*) FROM files').fetchone()[0], 0)
                self.assertEqual(db.execute("SELECT COUNT(*) FROM evidence WHERE id='scan-1'").fetchone()[0], 0)
            (report / 'manifest.jsonl').write_text(json.dumps(entry)+'\n')
            memory.import_scan(root,report,'scan-1')
            with memory.connect(root) as db:
                self.assertEqual(db.execute('SELECT path FROM files').fetchone()[0], 'synthetic')

    def test_idempotent_init_preserves_catalog_and_exports_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            memory.init(root)
            catalog = root / 'FUNCTION_DATABASE.csv'
            catalog.write_text('preserved user catalog', encoding='utf-8')
            memory.init(root)
            self.assertEqual(catalog.read_text(), 'preserved user catalog')
            memory.record(root,'test-1','test','PASS','Synthetic evidence only','tests/test_memory.py')
            data = json.loads((memory.export(root) / 'memory.json').read_text())
            self.assertEqual(len(data['evidence']), 2)
            self.assertTrue(any(row['id']=='test-1' for row in data['evidence']))
            with memory.connect(root) as db:
                with self.assertRaises(sqlite3.IntegrityError):
                    db.execute("INSERT INTO knowledge VALUES ('bad','function','x','x','UNKNOWN','{}','missing')")

if __name__ == '__main__':
    unittest.main()
