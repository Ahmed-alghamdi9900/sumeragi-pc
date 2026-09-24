# Executable analysis foundation

Executed read-only against the extracted executable. Source identity/size/mtime
checks passed. No source writes, relocation application or execution occurred.

Structural audit: two loadable memory ranges with unique supported SELF mappings;
566 dynamic symbol records (all section index zero); 125,600 RELA and 442 PLT RELA
records. Symbol-name offsets fall within declared string-table size, but symbol
strings were not decoded. Symbol indexes passed bounds checks. All relocation
types observed have known eight-byte target widths in this probe, and every target
falls within loadable memory. This does not prove correct relocation semantics.

Private analysis image: two load-segment files totaling 20,950,064 bytes, with virtual
addresses, flags and BSS zero-fill lengths in local/analysis-image-20260924/layout.json.
Written-file hashes matched source-range hashes. This is a segment analysis copy,
not a reconstructed runnable ELF, executable patch or port.

Capstone 5.0.6 installed into ignored local/python-deps. A synthetic nop/ret sanity
check passed. Linear decoding of the entry window yielded 50 instructions covering
256 bytes. Listing stays private in reports/entry-disassembly-20260924.json.
No function boundary, control-flow, semantics or game behavior validation claimed.
Initial Capstone phase did not configure a higher-level decompiler; see follow-up below. Dynamic symbols do not provide
original source or debug information; other symbol sources remain uninvestigated.

Private reproduction: reports/run-analysis-20260924.py. Numeric audit report:
reports/self-tables-20260924.json. Independent parser review found no actionable
issues; additional truncation/duplicate-tag checks passed. Full synthetic suite:
67 tests executed, 66 passed, one Windows symlink-permission skip.

Remaining foundations: high-level decompiler setup with explicit mappings, import
association/ABI investigation, entry control-flow validation, patch overlay provenance.
Architecture selection and game milestones remain pending.

References:
- https://www.capstone-engine.org/lang_python.html
- https://github.com/shadps4-emu/shadPS4/blob/main/src/core/loader/elf.h
- https://github.com/shadps4-emu/shadPS4/blob/main/src/core/module.cpp

Private extraction review found a provenance gap. Added source inventory path/hash,
explicit separate-observation caveat, extraction script hash and tool version to
analysis layout, disassembly and audit reports. No payload recopy was needed.

## Ghidra follow-up

Official Ghidra 12.1.4 and Temurin JDK 21.0.12.1+1 archives were downloaded into
ignored local/tool-downloads and verified against their published SHA-256 values.
Extracted only under local/tools. No global installation or PATH change.

Synthetic return-zero input decompiled successfully. Independent script review
found an input allocation before the size check; fixed with a bounded read.
Fresh-import/zero-analysis preconditions and function-body window containment
are now enforced. Oversized synthetic input rejected without entry.c output.

Real fresh import mapped the two verified load segments plus BSS, with base zero
and provisional x86-64 gcc compiler specification. Auto-analysis disabled.
Restricted entry disassembly produced 30 instructions; decompiler completed with
no reported diagnostic. Generated C and project database remain ignored/local:
local/ghidra-entry-reviewed and local/ghidra-projects. Provenance includes script
hash, segment/source hashes, tool versions and unrelocated/unbound caveats.

This is a bounded 256-byte entry experiment, not a whole-game decompilation.
No original C source recovered, no runtime executed, and no semantic correctness
claim. Independent review findings closed. Python suite: 66 passed, one skip;
Ghidra integrations separately executed on synthetic and real analysis inputs.
