# Initial engineering batch — 2026-09-20

Milestone: Phase 1 reconnaissance; no native M0 claim.

Executed using bundled Python from repository root:

```text
python -m unittest discover -s tests -v
python tools/local_probe/scan_game.py <private-source-folder> --output reports/initial-20260920-r3
python tools/pkg_metadata.py <private-base-pkg> --output reports/pkg-base-20260920.json
python tools/pkg_metadata.py <private-update-pkg> --output reports/pkg-update-20260920.json
python tools/project_memory.py import-scan --id initial-r3 --report reports/initial-20260920-r3
python tools/record_initial_findings.py
```

The last command is a one-time recorder for this dated evidence batch. Do not rerun
it against an already populated database; duplicate evidence IDs are rejected.

Latest suite: 28 tests executed, 27 passed, 1 skipped. No current failures. Actual
symlink creation unavailable for this Windows account; simulated reparse skipping
was tested. The test log's deliberately incomplete fixture reports are expected
negative cases, not a failed real scan. No PS4 behavioral tests ran.

Earlier failures preserved in task history/private reports: SQLite connection
remained open on Windows; source open incorrectly compared Windows timestamps
from APIs with differing semantics. Both fixed and independently reviewed; explicit
regression tests pass. A draft simulated reparse test also needed its fixture fixed
because Windows DirEntry inode reporting differed from Path.lstat.

Real scan: two package files, 29,916,069,888 bytes hashed, zero read errors/skips.
Readable metadata: same CUSA01159 identifier; base APP_VER 01.00 and update 01.02.
Update presence does not prove installation. Container descriptors are not a full
internal asset inventory. No authenticity, latest-patch, or Anniversary-content claim.

Independent review: separate reviewer verified PKG layouts against primary upstream
source, bounds and protected-entry exclusions, memory transaction/search behavior,
launcher, and complete synthetic suite. No outstanding material review findings.

Source fingerprints identify the tested Python files before the initial commit.
Local Git identity was subsequently configured from the authenticated GitHub account.
No remote CI run or public push has occurred.

Original source files were opened read-only. Compact bundle contains only metadata
allowlist, no raw SFO, executable, assets, keys or package payload. Reports and SQLite
remain private and ignored. SHA-256 inventory and metadata are separate observations;
the bundle describes their association without claiming an atomic capture.

Blocked game-dependent work: only packages available. Need accessible game logic
and assets before executable feasibility/architecture experiments. Port functionality
and translation both remain 0% validated; total scope cannot yet be measured.
