# Next actions

1. Done: synthetic parser/registry tests and independent review; evidence saved.
2. Done: hash both supplied packages and inspect accessible public metadata.
3. Done: associate findings with source manifests in SQLite, explicitly recording
   that metadata and full hashes are separate read-only observations.
4. Done: extracted inventory, SELF entry mapping and all ARC candidate table bounds.
   Payload decoding and executable semantics remain unverified.
5. Verify edition/patch/content against local evidence and official content list.
6. Choose the smallest executable or archive experiment; architecture remains open.
7. Done: owner explicitly approved source publication; initial source pushed to main.
   Windows/Linux synthetic CI passed for f9eb12d. Game data/private reports excluded.

Extracted Sc0/param.sfo exactly matches supplied 1.02 update SFO. Metadata confirms
1.02 presence, not completeness of the overlay. Latest official patch remains unknown.
Owner deferred the private-visibility change; continue with the public repository.

Next bounded experiments after reviewed probe publication:
- Done: one bounded ARC entry validates as a complete zlib stream.
- Done: 32 numeric type IDs sampled across 24 archives; all 32 zlib entries validated.
- Next: characterize selected decoded resource headers locally with format-specific bounds.
- Done: mapped numeric dynamic table, 215 tags and 46 standard DT_NEEDED records.
- Done: bounded string-table mapping recovered 46 unique dependency names locally.
- Done: symbol/relocation tables structurally audited; two mapped local analysis segments
  verified and bounded entry disassembly completed.
- Done: Ghidra local setup and bounded entry decompilation with explicit load mappings.
- Next: validate entry control flow, imported symbol/module associations and relocation
  semantics before expanding decompilation or choosing a runtime architecture.
- Distinguish bundled/system dependencies using identities rather than filename matching.
- Compare patch payload provenance if independent base/update files become available.

Completed table pass: all 6,324 ARC files, 203,531 entries, no range errors or overlaps.
Completed SELF probe: header-derived entry mapping and bounded 64-byte read only.
