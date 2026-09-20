"""Record this initial local evidence batch; no game source bytes are copied."""
import hashlib
import json
from pathlib import Path
import zipfile

import project_memory as memory

ROOT = Path(__file__).resolve().parents[1]

def main():
    report = ROOT / 'reports/initial-20260920-r3'
    records = [json.loads(line) for line in (report / 'manifest.jsonl').read_text().splitlines()]
    by_name = {item['path']: item for item in records if item['kind'] == 'file'}
    metadata = []
    for role in ('base', 'update'):
        origin = ROOT / ('reports/pkg-' + role + '-20260920.json')
        data = json.loads(origin.read_text())
        source = by_name[data['source']['relative_path']]
        if data['source']['size'] != source['size']:
            raise ValueError('metadata/inventory size mismatch')
        # These are separate observations, not a falsely claimed atomic capture.
        data['inventory_association'] = {
            'scan_id': 'initial-r3', 'sha256': source['sha256'],
            'method': 'same relative filename and size in separate read-only observations',
            'atomic_with_metadata_read': False,
        }
        destination = report / ('pkg_' + role + '_metadata.json')
        destination.write_text(json.dumps(data, indent=2, ensure_ascii=True)+'\n', encoding='utf-8')
        metadata.append((role, data, destination))
    bundle = report / 'SUMERAGI_INITIAL_ANALYSIS.zip'
    # Rebuild from an explicit metadata allowlist, never traverse game directories.
    names = ['summary.json','manifest.jsonl','errors.jsonl','GAME_FILE_MANIFEST.csv',
             'pkg_base_metadata.json','pkg_update_metadata.json']
    if sum((report / name).stat().st_size for name in names) > 32*1024*1024:
        raise ValueError('batch metadata bundle exceeds cap')
    with zipfile.ZipFile(bundle, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for name in names:
            archive.write(report / name, name)
    with zipfile.ZipFile(bundle) as archive:
        if archive.testzip() is not None or set(archive.namelist()) != set(names):
            raise ValueError('bundle verification failed')
    memory.record(ROOT, 'tooling-tests-20260920', 'test', 'PASS_WITH_SKIP',
                  '28 executed tests: 27 passed, 1 real symlink creation test skipped for Windows permissions; no game behavior tested.',
                  'evidence/tooling-tests-20260920.txt')
    memory.record(ROOT, 'independent-review-20260920', 'review', 'REVIEWED',
                  'Independent review found and verified fixes for SQLite handle lifecycle and Windows cross-API timestamp mismatch; PKG bounds and full suite reviewed.',
                  'evidence/initial-batch-20260920.md')
    memory.record(ROOT, 'official-content-correction', 'reference', 'DOCUMENTED_NOT_LOCALLY_VERIFIED',
                  'Capcom states 8 planned attribute-change weapons were replaced by increased starter/inscribed-weapon set quantities. Local DLC presence unknown.',
                  'https://www.capcom.co.jp/support/faq/platform_ps4_basara_15thae_0146729.html')
    for role, data, destination in metadata:
        evidence_id = 'pkg-' + role + '-metadata'
        memory.record(ROOT, evidence_id, 'metadata', 'OBSERVED',
                      json.dumps(data['param_sfo']['build_fields'], ensure_ascii=False),
                      str(destination.relative_to(ROOT)))
        with memory.connect(ROOT) as db:
            db.execute('INSERT INTO knowledge VALUES (?,?,?,?,?,?,?)', (
                'build-' + role, 'build', data['param_sfo']['build_fields']['TITLE_ID'],
                'source', 'MEASURED_METADATA_ONLY', json.dumps(data, ensure_ascii=False), evidence_id))
    memory.record(ROOT, 'source-access-blocker', 'blocker', 'OPEN',
                  'User confirms only two PKGs available. Game executable/assets not inspected; no payload decryption implemented. Anniversary identity and content remain unknown.',
                  'PROJECT_STATE.md')
    fingerprints = {}
    for folder in ('tools','tests'):
        for path in sorted((ROOT / folder).rglob('*.py')):
            fingerprints[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    (ROOT / 'evidence/source-fingerprints-20260920.json').write_text(json.dumps(fingerprints,indent=2)+'\n', encoding='utf-8')
    memory.export(ROOT)
    print(json.dumps({'bundle_bytes':bundle.stat().st_size,'inventoried_files':len(by_name),'metadata_reports':len(metadata)}))

if __name__ == '__main__':
    main()
