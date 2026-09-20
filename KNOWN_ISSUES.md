# Known issues

- SOURCE-001: Edition, patch, executable and bundled content not yet verified.
- TOOL-001 (FIXED): First actual package read falsely failed from Windows timestamp
  mismatch. Regression tested; subsequent two-package scan succeeded. Failed report retained.
- TOOL-002: Windows SQLite connection lifecycle test exposed an open-handle cleanup
  failure. Explicit connection closure implemented; regression rerun passed.
- INFRA-001: Owner-created public repository verified. Automatic review rejected
  source push pending explicit payload/publication approval. No upload or remote CI.
- RUNTIME-001: Native runtime does not exist; all game functionality unvalidated.
- TEST-001: Actual symlink-creation test may skip without Windows privilege; modeled
  reparse detection still tested. Do not report skipped execution as a pass.
- SOURCE-002: Only packages available; accessible executable/asset contents have
  not been supplied or inspected. Probe does not decrypt package payloads.
- SOURCE-003: Supplied 1.02 patch metadata verified; latest official version and
  installed patched state not verified. Do not merge patch files speculatively.
- TOOL-003 (FIXED): Search CLI failed on Japanese content with legacy terminal
  encoding. Escaped JSON preserves text and passes strict-ASCII subprocess regression.
