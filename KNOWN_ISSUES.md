# Known issues

- SOURCE-001: Edition, patch, executable and bundled content not yet verified.
- TOOL-001 (FIXED): First actual package read falsely failed from Windows timestamp
  mismatch. Regression tested; subsequent two-package scan succeeded. Failed report retained.
- TOOL-002: Windows SQLite connection lifecycle test exposed an open-handle cleanup
  failure. Explicit connection closure implemented; regression rerun passed.
- INFRA-001 (RESOLVED): Owner explicitly approved publication; reviewed source pushed
  to public repository. Published startup revision passed Windows/Linux synthetic CI.
- RUNTIME-001: Native runtime does not exist; all game functionality unvalidated.
- TEST-001: Actual symlink-creation test may skip without Windows privilege; modeled
  reparse detection still tested. Do not report skipped execution as a pass.
- SOURCE-002 (SUPERSEDED): User supplied extracted Image0/Sc0 tree. Original package
  PFS encryption flag no longer blocks file inventory. A bounded SELF entry range is readable; executable semantics and
  asset decoding remain to be established; no decryption is implemented.
- SOURCE-003: Extracted metadata exactly matches supplied 1.02 patch SFO; latest
  official version and complete overlay not verified. Do not merge files speculatively.
- TOOL-003 (FIXED): Search CLI failed on Japanese content with legacy terminal
  encoding. Escaped JSON preserves text and passes strict-ASCII subprocess regression.
