# Dependency names and broader archive sample

The bounded dependency parser mapped the SCE string table within its dynamic-data
container, required unique tags/mapping, validated offsets/terminators/ASCII names,
and recovered 46 distinct DT_NEEDED names. Names remain exclusively in ignored
reports/dependencies-20260924.json. A casefold exact-basename comparison found one
inventory filename match; 45 unmatched names do not imply 45 missing libraries.
System availability, module identities and ABI compatibility remain unknown.

Archive sample used the existing bounded payload probe. From 130 eligible numeric
type IDs, choose the first 32 in numeric order; within each type choose the median
entry by (stored size,relative path,index), retaining the 4 MiB stored-input cap.
All 32 entries across 24 archives validated as single complete zlib streams, totaling
348,436 stored bytes and 1,441,625 decoded bytes. This is deterministic coverage of
32 types, not a random/representative sample or proof of all-archive compatibility.
No decoded bytes were saved. Resource semantics and type-ID meanings remain unknown.

Private reproduction script: reports/run-dependencies-sample-20260924.py.
Private detailed sample: reports/arc-sample-20260924.json.
Sources were opened read-only and checked for changes. New tools did not modify them.
Prior manifest hashes and current observations are separate, not an atomic scan.

Independent dependency-parser review: no actionable findings. Reviewer also ran a
full synthetic SELF/dynamic/string-table integration and checked provenance.
Executed full suite: 62 tests, 61 passed and one Windows symlink-permission skip.

Format references:
- https://github.com/shadps4-emu/shadPS4/blob/main/src/core/loader/elf.h
- https://github.com/shadps4-emu/shadPS4/blob/main/src/core/module.cpp

No import binding, relocation execution, library loading or game milestone claimed.

