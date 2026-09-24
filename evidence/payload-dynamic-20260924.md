# Bounded payload and dynamic metadata experiments

Executed 2026-09-24 against local extracted source, opened read-only with no
buffered prefetch and source identity/size/mtime checks before and after.

One ARC entry validated as exactly one complete zlib stream: 75,598 input bytes,
357,840 decoded bytes. Strict limits: 4 MiB stored, 16 MiB decoded plus one
rejection-detection byte. No unbounded flush, trailing stream acceptance, raw
fallback, asset output or names. Only hashes/numeric metadata retained privately
in reports/arc-payload-20260924.json. Resource semantics remain unknown; this
sample does not establish compression support across all archives.

The SELF dynamic probe mapped a 3,456-byte PT_DYNAMIC through a unique plain
blocked SELF segment using ELF file-range containment. It read 215 non-null
numeric tags before DT_NULL, including 46 standard DT_NEEDED records. No dependency
names, string tables, symbol tables or relocation payloads read. Header/entry
reads inherited from the SELF probe also occur. Private report:
reports/self-dynamic-reviewed-20260924.json. No loader or game behavior validated.

Synthetic suite: 58 tests executed, 57 passed and one Windows symlink privilege
skip. ARC payload independent review found no actionable findings. Dynamic
review found test import and prerequisite-read reporting gaps; both fixed.
Direct test-module execution now passes; real rerun confirms the same tag count. Tests include overflow, corruption, truncation, concatenation,
exact output limit, invalid indexes and ambiguous/protected ELF mappings.

References used for API/format interpretation:
- https://docs.python.org/3/library/zlib.html
- https://github.com/shadps4-emu/shadPS4/blob/main/src/core/loader/elf.h

Architecture remains pending; no game milestone completed. Game-derived outputs
remain ignored and local; source data unchanged by the tools.
