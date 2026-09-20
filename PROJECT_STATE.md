# Current state

Canonical target: user-owned PS4 Sengoku BASARA 4 Sumeragi Anniversary Edition.
Exact internal build, patch and content remain unverified. The provided directory
now contains a 29,887,234,048-byte base package and a 28,835,840-byte update package.
Both were fully SHA-256 hashed. Readable PARAM.SFO metadata reports CUSA01159,
base APP_VER 01.00/category gd and update APP_VER 01.02/category gp, with matching
content IDs. This does not authenticate packages or establish installed state.
No filename-based edition conclusion. User requests latest update; 1.02 is the
supplied candidate, but latest official patch status has not been independently verified.

Current milestone: Phase 1 forensic inventory. Native M0 and all game milestones
remain open. Port completion: 0% validated game functionality. Translation: 0%
validated; total string count unknown. No runtime, renderer, playable build, or
PS4 behavioral comparison exists.

Implemented initial local probe, local SQLite registry, portable exports, catalog
schemas, synthetic test infrastructure and public-project documentation. The final
suite ran 29 tests: 28 passed, one skipped for Windows symlink-creation permission.
Independent review completed; see evidence/initial-batch-20260920.md.

User confirms only the packages are available. The present probe reads public
metadata only; executable, assets, engine, Anniversary content and patch application
remain uninspected. No decryption was attempted. Next game-dependent work requires
accessible executable/assets; do not claim the package inventory is a full internal
game-file inventory. Private compact bundle: reports/initial-20260920-r3/SUMERAGI_INITIAL_ANALYSIS.zip.

GitHub owner verified through connector: Ahmed-alghamdi9900. Local Git uses that
login and GitHub noreply address; initial branch codex/initial-reconnaissance.
Initial commit fa33d8a saved the reviewed startup batch. No remote exists yet.
Browser is signed in; public repository creation awaits explicit visibility approval
after automatic approval review rejected the creation click. Nothing is published.
