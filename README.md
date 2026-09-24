# Sumeragi native PC research project

Target: user-owned **PS4 Sengoku BASARA 4 Sumeragi Anniversary Edition**.
This is initial reconnaissance tooling, **not a playable port**. Extracted metadata
identifies CUSA01159 update 01.02 and exactly matches the supplied patch metadata.
The extracted inventory contains 7,894 files; all 6,324 ARC candidate tables passed
bounds checks. A bounded SELF entry range is readable. Anniversary content, full
patch overlay, engine, renderer and native compatibility remain unverified.

## First local inventory

From this project folder in PowerShell:

```powershell
.\Run-InitialAnalysis.ps1 -GameDirectory 'D:\YOUR_EXTRACTED_GAME_FOLDER'
```

Replace the example path with the actual extracted game folder. Original data is
read only. Output goes under `reports/`; the script prints the report location.
Keep the metadata bundle private until reviewed. Do not upload the game itself.
Package-only folders are also accepted for opaque file inventory. For a PKG's
accessible public header and plaintext build metadata, run:

```powershell
python tools/pkg_metadata.py 'D:\GAME\game.pkg' --output reports/pkg-metadata.json
```

This performs no payload decryption and does not inventory files inside the package.
If this Codex task can access the folder, supplying its path is sufficient.

See tools/local_probe/README.md for exact scope and limitations. Local inventory
is the first step; unsupported containers are recorded without decryption.

## Project memory

`tools/project_memory.py init` initializes local `SUMERAGI_PROJECT.sqlite` and
header-only CSV catalogs. The schema tracks provenance, knowledge, tests, and
decisions. `export` produces local JSON/JSONL/CSV/Markdown exports under `local/`.
The database and exports are private and ignored by Git.
`import-scan --id SCAN_ID --report reports/SCAN` imports our metadata manifest;
`search --query TERM` searches the knowledge FTS5 index where available.

See PROJECT_STATE.md, BUILD_WINDOWS.md, LEGAL_BOUNDARIES.md, and the complete
user instructions in docs/CANONICAL_PROJECT_INSTRUCTIONS.md.

Project repository: https://github.com/Ahmed-alghamdi9900/sumeragi-pc. No playable release exists.
A redistribution license has not yet
been selected; do not represent this initial repository as licensed for release.
