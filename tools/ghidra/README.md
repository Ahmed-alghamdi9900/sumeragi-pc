# Bounded Ghidra entry experiment

AnalyzeEntry.java is original scaffolding for a fresh raw-binary import, not a
PS4 loader. Use x86:LE:64:default, explicit base address, provisional gcc compiler
specification and -noanalysis. Verify local segment hashes against the private
analysis layout before import. Never supply original SELF directly as raw code.

Post-script arguments in order: data-segment file, data virtual address, BSS size,
entry virtual address, new private output directory. It maps data/BSS, limits
entry disassembly to at most 256 bytes, requires function-body containment, and
gives the decompiler 30 seconds. It refuses preexisting instructions/functions.
Data reads are bounded to 32 MiB plus one rejection byte. Outputs contain derived
commercial code: use ignored local directories only and never publish them.

Tested with Ghidra 12.1.4 and Temurin JDK 21.0.12.1+1. Synthetic code bytes
31 c0 c3 at base/entry zero, eight zero data bytes at 0x1000 and zero BSS produced
return-zero C. A 32 MiB + 1 byte data file rejected. Full game behavior is untested.

Ghidra may log a script failure while returning a successful process exit code.
Check fresh status.txt for decompile_completed=true and inspect diagnostics;
never infer success from shell exit status alone.

No relocations applied or imports bound. gcc calling conventions are provisional.
Generated C is an analysis draft, not original source or a native implementation.
