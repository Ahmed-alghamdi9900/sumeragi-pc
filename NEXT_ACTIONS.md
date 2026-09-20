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
7. Initial local commit fa33d8a completed. GitHub public repository creation is pending
   explicit visibility approval after automatic review rejection; browser signed in.
   Connected API provides no repository-creation tool. Audit files before push.

Current source limitation: owner confirms only packages, no extracted folder.
Preserve the 1.02 update as a candidate canonical patch. Verify latest official
patch and correct base/update overlay before future executable analysis.
