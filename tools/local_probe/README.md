# Initial local reconnaissance

This Python 3.10+ standard-library tool inventories a local, legally owned game directory. It reads source files without modifying their contents, executes nothing from the game, and sends nothing over the network.

From the project directory in PowerShell:

```powershell
python tools/local_probe/scan_game.py "D:\YourGameDirectory" --output "reports\initial-001"
```

Replace the example game path with the actual directory. The output directory must be new and outside the game directory. Every regular file is read completely for SHA-256, so scanning a large package takes time and disk bandwidth. Keep the game directory unchanged until the scan finishes.

## Output and exit status

- `manifest.jsonl`: complete local inventory, one JSON record per encountered entry, including directories, hashes, sizes, signature candidates, bounded metadata, skips and errors. Paths are relative to the supplied root. Enumeration order is filesystem dependent.
- `GAME_FILE_MANIFEST.csv`: machine-readable projection of the inventory. Filenames are preserved verbatim; import paths as text if using spreadsheet software.
- `errors.jsonl`: explicit error/skip records with relative paths.
- `summary.json`: counts, completion status, limitations and unresolved source identity.
- `SUMERAGI_INITIAL_ANALYSIS.zip`: metadata only, suitable for review before sharing. Contains no commercial binary payloads, extracted assets, raw header dumps or bulk strings.

Exit `0` means all encountered regular files were hashed without read or parser errors. Exit `1` means incomplete: any skipped link/special file, inaccessible entry, changed file, invalid supported metadata or an empty source makes the scan incomplete. Exit `2` means invalid arguments, setup or report-writing failure. A failed report-write may leave partial output; preserve it for diagnosis and choose a new output directory for retries.

The ZIP has a fixed 32 MiB uncompressed metadata budget. When the complete manifest and error log do not fit, it includes at most 1 MiB of complete initial lines from each and explicitly declares omitted full reports in `summary.json`. The complete local reports remain available. A ZIP preview is not a complete manifest and must not be treated as one by downstream tooling. The CSV is local only to avoid duplicating the manifest in the upload.

## Implemented scope

Known magic bytes conservatively distinguish ELF, SFO and candidate SELF/SCE/PKG, ZIP, DDS, PNG, Ogg and RIFF containers. A matching magic does not prove that the file is valid, decryptable, from PS4, or from a particular edition.

The SFO parser checks tables and value ranges, reads at most 2 MiB, and exports only these allowlisted fields: `TITLE`, `TITLE_ID`, `CONTENT_ID`, `APP_VER`, `VERSION`, `CATEGORY`, `SYSTEM_VER`, `ATTRIBUTE`, `PUBTOOLINFO`. It does not export arbitrary strings or values. Values remain evidence, not a verified Anniversary Edition conclusion.

The ELF parser records 32/64-bit header and program/section table numbers, checks file ranges, supports either byte order and limits each table to 4,096 records. It does not export section contents or section names. Extended numbering is explicitly unsupported. Imports, relocations, disassembly, engine identification, assets, shaders, audio, localization, archives and encryption are not analyzed. PKG/SELF are currently signature candidates only. Unsupported and unknown formats are reported without guessed content.

The tool does not verify edition, installed patch, bundled DLC or runtime compatibility. Those remain unknown until separate evidence establishes them. A directory containing a single package yields an inventory of that package, not its internal contents. No decryption, protection bypass, key discovery or downloading is implemented.

## Filesystem boundaries

Source/output roots and their ancestors must not be symlinks or Windows reparse points. Encountered links, junctions, reparse points and special files are skipped and reported. Final file opens use `O_NOFOLLOW` where available or Windows `FILE_FLAG_OPEN_REPARSE_POINT`; opened identity is compared to the path. Windows file sharing permits other readers but blocks writers/deletion for the duration of each file read. File size, identity and modification time are checked before and after hashing.

This is a static-tree inventory, not an atomic snapshot or a defense against another process deliberately replacing ancestor directories during enumeration. Use a quiescent local directory. Files added after a directory is enumerated cannot be detected reliably. Normal operating-system access-time updates may occur even though source contents are opened read-only.

## Synthetic validation

```powershell
python -m unittest discover -s tests -p test_probe.py -v
```

Fixtures are generated inside temporary directories. Tests exercise full hashes, report privacy, SFO allowlisting and invalid bounds, ELF ranges, changed-file rejection, empty sources, errors, output containment/refusal, bundle omission and link classification. A real symlink test is skipped if the OS account lacks permission to create symlinks. Synthetic success does not validate a real game's formats or playability.
