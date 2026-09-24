// Local static-analysis scaffold; output contains private derived code.
// Does not apply relocations, bind imports, or execute the input program.
import ghidra.app.script.GhidraScript;
import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressSet;
import ghidra.program.model.listing.Function;
import ghidra.program.model.mem.MemoryBlock;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.charset.StandardCharsets;
import java.io.ByteArrayInputStream;
import java.io.InputStream;

public class AnalyzeEntry extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 5) throw new IllegalArgumentException("data path, data address, BSS size, entry address, output directory required");
        Path output = Path.of(args[4]);
        Files.createDirectory(output); // Refuse to overwrite an existing analysis result.
        Address dataAddress = toAddr(Long.decode(args[1]));
        long bssSize = Long.decode(args[2]);
        Address entry = toAddr(Long.decode(args[3]));
        if (currentProgram.getListing().getNumInstructions() != 0 || currentProgram.getFunctionManager().getFunctionCount() != 0)
            throw new IllegalArgumentException("fresh import with automatic analysis disabled required");
        byte[] data;
        try (InputStream input = Files.newInputStream(Path.of(args[0]))) {
            data = input.readNBytes(32 * 1024 * 1024 + 1);
        }
        if (data.length == 0 || data.length > 32 * 1024 * 1024 || bssSize < 0 || bssSize > 32 * 1024 * 1024)
            throw new IllegalArgumentException("data/BSS exceeds scaffold bounds");
        MemoryBlock code = currentProgram.getMemory().getBlock(entry);
        if (code == null || !code.isInitialized()) throw new IllegalArgumentException("entry not in initialized code");
        code.setRead(true); code.setWrite(false); code.setExecute(true);
        MemoryBlock block = currentProgram.getMemory().createInitializedBlock("mapped_data", dataAddress,
            new ByteArrayInputStream(data), data.length, monitor, false);
        block.setRead(true); block.setWrite(true); block.setExecute(false);
        if (bssSize != 0) {
            MemoryBlock bss = currentProgram.getMemory().createUninitializedBlock("mapped_bss", dataAddress.add(data.length), bssSize, false);
            bss.setRead(true); bss.setWrite(true); bss.setExecute(false);
        }
        // Deliberately bounded. This is an entry-window experiment, not full function recovery.
        Address last = entry.add(Math.min(255, code.getEnd().subtract(entry)));
        AddressSet window = new AddressSet(entry, last);
        DisassembleCommand command = new DisassembleCommand(entry, window, true);
        if (!command.applyTo(currentProgram, monitor)) throw new IllegalStateException("entry disassembly failed");
        Function function = createFunction(entry, "analysis_entry");
        if (function == null) throw new IllegalStateException("entry function creation failed");
        if (!window.contains(function.getBody()))
            throw new IllegalStateException("function body exceeds entry window");
        DecompInterface decompiler = new DecompInterface();
        try {
            if (!decompiler.openProgram(currentProgram)) throw new IllegalStateException("decompiler failed to open program");
            DecompileResults result = decompiler.decompileFunction(function, 30, monitor);
            boolean completed = result.decompileCompleted() && result.getDecompiledFunction() != null;
            String status = "decompile_completed=" + completed + "\n" +
                "instruction_count=" + currentProgram.getListing().getNumInstructions() + "\n" +
                "analysis_scope=256-byte entry window; mappings unrelocated; imports unbound\n" +
                "compiler_spec=" + currentProgram.getCompilerSpec().getCompilerSpecID() + "\n" +
                "diagnostic=" + result.getErrorMessage() + "\n";
            Files.writeString(output.resolve("status.txt"), status, StandardCharsets.UTF_8);
            if (completed) Files.writeString(output.resolve("entry.c"), result.getDecompiledFunction().getC(), StandardCharsets.UTF_8);
            if (!completed) throw new IllegalStateException("entry decompilation did not complete; see private status");
            println("Bounded entry decompilation completed; private output saved.");
        } finally { decompiler.dispose(); }
    }
}
