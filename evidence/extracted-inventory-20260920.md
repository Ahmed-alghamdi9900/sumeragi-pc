# Extracted source inventory

Owner replaced the package-only input with a locally extracted Image0/Sc0 tree.
Executed existing scanner read-only; 7,894 files / 30,057,475,874 bytes fully hashed,
742 directories, zero errors/skips. Private evidence: reports/extracted-20260920/.
Imported into local SQLite under scan ID extracted-20260920.

Sc0/param.sfo APP_VER=01.02, TITLE_ID=CUSA01159 and CATEGORY=gp. Its SHA-256 exactly
matches the earlier update package PARAM.SFO range hash. Local changeinfo.xml lists
01.02 and 01.01. Evidence: reports/extracted-version-check.json.

Conclusion: 1.02 update metadata is present in the extracted tree. No claim that
all overlay payloads were verified or that 1.02 is the latest official patch.

Image0/eboot.bin is present, 24,119,184 bytes, SELF candidate magic. Inventory also
finds 6,324 .arc, 1,248 .sspr, 153 .mp4 and 119 .stqr files. These are suffix counts,
not validated format catalogs. Code/format feasibility experiments follow.

No game bytes, extracted strings or private reports committed. Runtime/translation
remain 0% validated. Source preservation and no-decryption boundary remain binding.

## Bounded follow-up probes

All 6,324 ARC files passed candidate v7 numeric table bounds: 203,531 entries,
zero detected overlaps, 3,307,088 requested bytes. No names or payloads read.
Entries are not a count of unique assets. Private reports: arc-all.jsonl and
arc-all-summary.json under reports/. Manifest hashes are from a separate scan;
the table reads and original full-file hashes are not an atomic observation.

SELF/ELF metadata provided one executable entry mapping. The probe read 64 bytes
from that range and saved only a hash/numeric metadata in reports/self-entry-probe.json.
This is header-derived accessibility evidence; no instruction decoding, relocation,
dependency analysis or execution occurred. No decryption was attempted.

On 2026-09-24 the full synthetic suite ran 48 tests: 47 passed, one Windows
symlink-creation permission skip. Independent reviewer found missing SELF endian validation; fixed with rejection
tests for unsupported byte-order declarations. ARC review found no actionable issues.
Real SELF probe rerun after the fix reproduced the entry range/hash; private
report: reports/self-entry-probe-reviewed-20260924.json.
