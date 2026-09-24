# Current state

Canonical target: user-owned PS4 Sengoku BASARA 4 Sumeragi Anniversary Edition.
The user replaced the packages with an extracted tree (Image0 and Sc0). Full read-only
inventory succeeded: 7,894 files, 742 directories, 30,057,475,874 bytes, no errors/skips.
Sc0/param.sfo reports CUSA01159, APP_VER 01.02, category gp; its SHA-256 exactly
matches the previously inspected update package's plaintext PARAM.SFO. Local
changeinfo.xml lists 01.02 and 01.01. Update metadata is confirmed present. A complete
base/update overlay and latest official patch status are not yet independently proven.
Anniversary content remains unverified; no filename-based edition conclusion.

Current milestone: Phase 1 forensic inventory. Native M0 and all game milestones
remain open. Port completion: 0% validated game functionality. Translation: 0%
validated; total string count unknown. No runtime, renderer, playable build, or
PS4 behavioral comparison exists.

Implemented initial local probe, local SQLite registry, portable exports, catalog
schemas, synthetic test infrastructure and public-project documentation. The final
suite ran 62 tests: 61 passed, one skipped for Windows symlink-creation permission.
Independent reviews completed; SELF byte-order finding fixed and regression tested.

Current private inventory: reports/extracted-20260920/SUMERAGI_INITIAL_ANALYSIS.zip.
Executable present: Image0/eboot.bin (24,119,184 bytes), SELF candidate signature.
Asset extension counts include 6,324 .arc, 1,248 .sspr, 153 .mp4 and 119 .stqr.
Extensions are evidence for selecting probes, not proven format or engine identity.
All 6,324 ARC candidate tables passed range checks (203,531 entries, no overlaps).
One ARC entry validated as a complete zlib stream (75,598 stored bytes to
357,840 decoded bytes); decoded data was not written. A bounded executable dynamic
table read found 215 numeric tags, including 46 standard DT_NEEDED records.
46 distinct dependency names recovered into a private report; one exact basename
match in the inventory does not establish availability or ABI compatibility.
A broader sample validated 32 zlib entries across 24 archives and 32 numeric type IDs.
Relocation payloads and runtime behavior remain unverified. No decryption
was performed by project tools. Detailed feasibility work remains pending.

Historical package access probe: both outer PFS headers declared encryption (mode
0xD); see evidence/pfs-access-20260920.md. The user-provided extraction supersedes
that input blocker. A bounded SELF entry range was read; instruction semantics,
dependency resolution, relocation and execution remain untested.

GitHub owner verified through connector: Ahmed-alghamdi9900. Local Git uses that
login and GitHub noreply address; initial branch codex/initial-reconnaissance.
Initial commits fa33d8a and a0c8b0c saved the reviewed startup batch and terminal fix.
Owner-created public repository verified: https://github.com/Ahmed-alghamdi9900/sumeragi-pc.
Owner explicitly approved publication. Reviewed source was pushed to main at
f97f7421fdfbf9572a7e24843b4e47de0332f68e. Published follow-up adf19d3 passed both
Windows/Linux synthetic CI: https://github.com/Ahmed-alghamdi9900/sumeragi-pc/actions/runs/35497006125.
Game packages and private analysis remain local and excluded from Git.

Owner deferred the private-visibility change; repository remains public.

Reviewed probe revision d02ecb7 passed Windows/Linux CI run 35955727739.

Reviewed revision f9eb12d passed Windows/Linux CI run 35963824052.
