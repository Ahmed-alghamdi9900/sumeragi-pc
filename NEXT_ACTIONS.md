# Next actions

1. Done: synthetic parser/registry tests and independent review; evidence saved.
2. Done: hash both supplied packages and inspect accessible public metadata.
3. Done: associate findings with source manifests in SQLite, explicitly recording
   that metadata and full hashes are separate read-only observations.
4. Determine whether accessible executable and asset data exists. If only opaque
   package payload is available, request the smallest accessible metadata/files
   needed; never request full-game uploads or implement bypass/decryption.
5. Verify edition/patch/content against local evidence and official content list.
6. Choose the smallest executable or archive experiment; architecture remains open.
7. Done: owner explicitly approved source publication; initial source pushed to main.
   Check remote Windows/Linux synthetic CI. Game data and private reports excluded.

Current source limitation: owner confirms only packages, no extracted folder.
Preserve the 1.02 update as a candidate canonical patch. Verify latest official
patch and correct base/update overlay before future executable analysis.
