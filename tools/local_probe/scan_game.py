#!/usr/bin/env python3
"""Read-only initial inventory. Standard library only; never extracts game data."""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import contextmanager
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import stat
import struct
import sys
import zipfile

SCHEMA_VERSION = 1
CHUNK_SIZE = 1024 * 1024
SFO_LIMIT = 2 * 1024 * 1024
TABLE_LIMIT = 4096
BUNDLE_LIMIT = 32 * 1024 * 1024  # uncompressed metadata, not source bytes
PREVIEW_LIMIT = 1024 * 1024
REPARSE = 0x400
SFO_KEYS = frozenset({"TITLE", "TITLE_ID", "CONTENT_ID", "APP_VER", "VERSION",
                      "CATEGORY", "SYSTEM_VER", "ATTRIBUTE", "PUBTOOLINFO"})


def is_link(st):
    return stat.S_ISLNK(st.st_mode) or bool(getattr(st, "st_file_attributes", 0) & REPARSE)


def unchanged(a, b):
    # Windows stat/fstat can report creation/change time differently across Python
    # versions. Identity, size and last-write time are comparable on both APIs.
    keys = ("st_dev", "st_ino", "st_size", "st_mtime_ns")
    if os.name != "nt":
        keys += ("st_ctime_ns",)
    return all(getattr(a, key) == getattr(b, key) for key in keys)


@contextmanager
def open_source(path, buffering=-1):
    """Open a regular file without following its final symlink/reparse component."""
    before = path.lstat()
    if is_link(before) or not stat.S_ISREG(before.st_mode):
        raise OSError("source is not a regular non-link file")
    if os.name == "nt":
        import ctypes
        import msvcrt
        from ctypes import wintypes
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        create = kernel.CreateFileW
        create.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                           wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
        create.restype = wintypes.HANDLE
        # OPEN_REPARSE_POINT; share read only while hashing, disallow replacement/writers.
        handle = create(str(path), 0x80000000, 1, None, 3, 0x00200000, None)
        if handle == wintypes.HANDLE(-1).value:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            fd = msvcrt.open_osfhandle(handle, os.O_RDONLY | os.O_BINARY)
        except BaseException:
            kernel.CloseHandle.argtypes = [wintypes.HANDLE]
            kernel.CloseHandle(handle)
            raise
    else:
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    with os.fdopen(fd, "rb", buffering=buffering) as stream:
        opened = os.fstat(stream.fileno())
        if is_link(opened) or not stat.S_ISREG(opened.st_mode) or not unchanged(before, opened):
            raise OSError("source changed during open")
        yield stream, opened


def read_at(stream, offset, length, size):
    if offset < 0 or length < 0 or offset > size or length > size - offset:
        raise ValueError("metadata range outside file")
    stream.seek(offset)
    data = stream.read(length)
    if len(data) != length:
        raise ValueError("truncated metadata")
    return data


def signature(head):
    for magic, name in ((b"\x7fELF", "ELF"), (b"\x00PSF", "SFO"),
                        (b"\x4f\x15\x3d\x1d", "SELF_candidate"),
                        (b"SCE\x00", "SCE_container_candidate"),
                        (b"\x7fCNT", "PKG_candidate"),
                        (b"PK\x03\x04", "ZIP_candidate"), (b"DDS ", "DDS_candidate"),
                        (b"\x89PNG\r\n\x1a\n", "PNG_candidate"),
                        (b"OggS", "Ogg_candidate"), (b"RIFF", "RIFF_candidate")):
        if head.startswith(magic):
            return name
    return "unknown"


def parse_sfo(stream, size):
    if size > SFO_LIMIT:
        return {"status": "unsupported", "reason": "SFO exceeds 2 MiB metadata limit"}
    data = read_at(stream, 0, size, size)
    if len(data) < 20:
        raise ValueError("truncated SFO header")
    magic, version, keys, values, count = struct.unpack_from("<4sIIII", data)
    if magic != b"\x00PSF" or count > TABLE_LIMIT or not 20 + count * 16 <= keys <= values <= size:
        raise ValueError("invalid SFO table bounds")
    result = {}
    for i in range(count):
        keyoff, fmt, length, capacity, valueoff = struct.unpack_from("<HHIII", data, 20 + i * 16)
        start = keys + keyoff
        if not keys <= start < values:
            raise ValueError("invalid SFO key offset")
        end = data.find(b"\0", start, min(values, start + 256))
        if end < 0:
            raise ValueError("unterminated SFO key")
        key = data[start:end].decode("ascii", "strict")
        value_start = values + valueoff
        if length > capacity or value_start > size or capacity > size - value_start:
            raise ValueError("invalid SFO value bounds")
        if key not in SFO_KEYS:
            continue
        if key in result:
            raise ValueError("duplicate allowlisted SFO key")
        if length > 1024:
            raise ValueError("allowlisted SFO value exceeds 1024 bytes")
        value = data[value_start:value_start + length]
        if fmt == 0x0204:
            result[key] = value.rstrip(b"\0").decode("utf-8", "strict")
        elif fmt == 0x0404 and length == 4:
            result[key] = struct.unpack("<I", value)[0]
        else:
            result[key] = {"status": "unsupported", "format": fmt, "length": length}
    return {"status": "parsed", "format_version": version, "build_fields": result,
            "edition_verified": False}


def parse_elf(stream, size):
    ident = read_at(stream, 0, 16, size)
    if ident[4] not in (1, 2) or ident[5] not in (1, 2) or ident[6] != 1:
        raise ValueError("unsupported ELF class, endianness or identification version")
    bits = 32 if ident[4] == 1 else 64
    endian = "<" if ident[5] == 1 else ">"
    fmt = endian + ("HHIIIIIHHHHHH" if bits == 32 else "HHIQQQIHHHHHH")
    header_size = 16 + struct.calcsize(fmt)
    fields = struct.unpack(fmt, read_at(stream, 16, header_size - 16, size))
    names = ("type", "machine", "version", "entry", "program_offset", "section_offset",
             "flags", "header_size", "program_entry_size", "program_count",
             "section_entry_size", "section_count", "section_names_index")
    result = dict(zip(names, fields))
    result.update(status="parsed", bits=bits, byte_order="little" if endian == "<" else "big",
                  osabi=ident[7], abi_version=ident[8], imports_status="not_analyzed")
    if result["header_size"] != header_size or result["version"] != 1:
        raise ValueError("invalid ELF header size/version")
    if result["program_count"] == 0xffff or result["section_names_index"] == 0xffff or (
            result["section_count"] == 0 and result["section_offset"] != 0):
        result["status"] = "unsupported"
        result["reason"] = "ELF extended numbering not implemented"
        return result
    for table in ("program", "section"):
        count = result[table + "_count"]
        offset = result[table + "_offset"]
        stride = result[table + "_entry_size"]
        if table == "program":
            form = endian + ("IIIIIIII" if bits == 32 else "IIQQQQQQ")
            columns = (["type", "offset", "virtual_address", "physical_address", "file_size", "memory_size", "flags", "alignment"]
                       if bits == 32 else ["type", "flags", "offset", "virtual_address", "physical_address", "file_size", "memory_size", "alignment"])
        else:
            form = endian + ("IIIIIIIIII" if bits == 32 else "IIQQQQIIQQ")
            columns = ["name_index", "type", "flags", "address", "offset", "size", "link", "info", "alignment", "entry_size"]
        expected = struct.calcsize(form)
        if count > TABLE_LIMIT:
            result["status"] = "unsupported"
            result["reason"] = "ELF table exceeds 4096-entry limit"
            return result
        if count and (stride != expected or offset < header_size):
            raise ValueError("invalid ELF " + table + " table layout")
        records = []
        raw = read_at(stream, offset, count * stride, size)
        for i in range(count):
            record = dict(zip(columns, struct.unpack_from(form, raw, i * stride)))
            payload_size = record.get("file_size", record.get("size", 0))
            # NOBITS sections occupy memory only; PT_NULL entries have no defined payload.
            has_payload = record["type"] not in ((0, 8) if table == "section" else (0,))
            if has_payload and (record["offset"] > size or payload_size > size - record["offset"]):
                raise ValueError("ELF " + table + " payload outside file")
            records.append(record)
        result[table + "s"] = records
    return result


def inspect_file(path):
    with open_source(path) as (stream, before):
        digest = hashlib.sha256()
        head = b""
        total = 0
        while True:
            data = stream.read(CHUNK_SIZE)
            if not data:
                break
            if total == 0:
                head = data[:16]
            digest.update(data)
            total += len(data)
        kind = signature(head)
        metadata = {"status": "unsupported" if kind != "unknown" else "unknown"}
        metadata_error = None
        try:
            if kind == "SFO":
                metadata = parse_sfo(stream, total)
            elif kind == "ELF":
                metadata = parse_elf(stream, total)
        except (ValueError, UnicodeError, struct.error) as exc:
            metadata = {"status": "invalid", "reason": str(exc)}
            metadata_error = str(exc)
        if total != before.st_size or not unchanged(before, os.fstat(stream.fileno())) or not unchanged(before, path.lstat()):
            raise OSError("source changed while reading; hash discarded")
        return {"kind": "file", "status": "metadata_error" if metadata_error else "ok",
                "size": total, "sha256": digest.hexdigest(), "signature": kind,
                "metadata": metadata}


def write_line(stream, value):
    stream.write(json.dumps(value, ensure_ascii=True, sort_keys=True) + "\n")


def validate_paths(game_dir, output_dir):
    source_input = Path(os.path.abspath(game_dir))
    for parent in (source_input, *source_input.parents):
        if is_link(parent.lstat()):
            raise ValueError("source path and ancestors must not be links/reparse points")
    source = source_input.resolve(strict=True)
    if not source.is_dir():
        raise ValueError("game directory must be an existing directory")
    output = Path(os.path.abspath(output_dir))
    for parent in (output, *output.parents):
        if parent.exists() or parent.is_symlink():
            if is_link(parent.lstat()):
                raise ValueError("output path and ancestors must not be links/reparse points")
    output = output.resolve()
    if output == source or source in output.parents:
        raise ValueError("output must be outside game directory")
    if output.exists():
        raise ValueError("output already exists; choose a new output directory")
    return source, output


def run_scan(game_dir, output_dir):
    source, output = validate_paths(game_dir, output_dir)
    output.mkdir(parents=True, exist_ok=False)
    counts = Counter()
    types = Counter()
    manifest_path = output / "manifest.jsonl"
    error_path = output / "errors.jsonl"
    with manifest_path.open("x", encoding="utf-8", newline="\n") as manifest, error_path.open("x", encoding="utf-8", newline="\n") as errors, (output / "GAME_FILE_MANIFEST.csv").open("x", encoding="utf-8", newline="") as csv_file:
        csv_writer = csv.DictWriter(csv_file, fieldnames=["path", "kind", "status", "size", "sha256", "signature"], extrasaction="ignore")
        csv_writer.writeheader()
        def report_error(relative, reason):
            counts["errors"] += 1
            write_line(errors, {"path": relative, "reason": reason})

        pending = [source]
        while pending:
            directory = pending.pop()
            relative_dir = directory.relative_to(source).as_posix()
            try:
                if is_link(directory.lstat()) or not directory.resolve().is_relative_to(source):
                    raise OSError("directory became a link or escaped source")
                with os.scandir(directory) as entries:
                    for entry in entries:
                        path = Path(entry.path)
                        relative = path.relative_to(source).as_posix()
                        try:
                            info = entry.stat(follow_symlinks=False)
                            if is_link(info):
                                record = {"kind": "skipped", "status": "skipped", "reason": "symlink_or_reparse_point"}
                                counts["skipped"] += 1
                                report_error(relative, record["reason"])
                            elif stat.S_ISDIR(info.st_mode):
                                pending.append(path)
                                counts["directories"] += 1
                                record = {"kind": "directory", "status": "ok"}
                            elif stat.S_ISREG(info.st_mode):
                                record = inspect_file(path)
                                counts["files_hashed"] += 1
                                counts["bytes_hashed"] += record["size"]
                                types[record["signature"]] += 1
                                if record["status"] != "ok":
                                    report_error(relative, record["metadata"]["reason"])
                            else:
                                record = {"kind": "skipped", "status": "skipped", "reason": "special_file"}
                                counts["skipped"] += 1
                                report_error(relative, record["reason"])
                        except OSError as exc:
                            # Do not emit exception filenames, which can disclose absolute paths.
                            record = {"kind": "error", "status": "error", "reason": "source_read_failed", "errno": exc.errno, "winerror": getattr(exc, "winerror", None)}
                            report_error(relative, record["reason"])
                        record["path"] = relative
                        write_line(manifest, record)
                        # CSV is for machine import, not automatic spreadsheet execution.
                        csv_writer.writerow(record)
            except OSError as exc:
                report_error(relative_dir, "directory_read_failed")
                write_line(manifest, {"path": relative_dir, "kind": "error", "status": "error", "reason": "directory_read_failed", "errno": exc.errno})
        if counts["files_hashed"] == 0:
            report_error(".", "no_regular_files_hashed_source_not_usable")
    summary = {"schema_version": SCHEMA_VERSION, "tool": "sumeragi-local-probe/0.1",
               "created_utc": datetime.now(timezone.utc).isoformat(),
               "complete": counts["errors"] == 0,
               **{key: counts[key] for key in ("files_hashed", "bytes_hashed", "directories", "errors", "skipped")},
               "signature_counts": dict(types),
               "source_identity": {"status": "unverified", "canonical_target": "PS4 Sengoku BASARA 4 Sumeragi Anniversary Edition",
                                   "edition": "unknown", "patch_state": "unknown", "bundled_content": "unknown"},
               "limitations": ["No decryption, extraction, imports, strings, shader or archive payload analysis.",
                               "Signature labels are candidates, not proof of platform or content.",
                               "A complete inventory does not verify edition or port compatibility.",
                               "Scan a quiescent tree; this is not an atomic filesystem snapshot."]}
    full_size = manifest_path.stat().st_size + error_path.stat().st_size
    include_full = full_size <= BUNDLE_LIMIT - PREVIEW_LIMIT
    summary["bundle"] = {"full_manifest_included": include_full, "uncompressed_limit_bytes": BUNDLE_LIMIT,
                         "omitted": [] if include_full else ["full manifest.jsonl", "full errors.jsonl"]}
    summary_bytes = (json.dumps(summary, indent=2, sort_keys=True) + "\n").encode("utf-8")
    (output / "summary.json").write_bytes(summary_bytes)
    with zipfile.ZipFile(output / "SUMERAGI_INITIAL_ANALYSIS.zip", "x", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("summary.json", summary_bytes)
        if include_full:
            archive.write(manifest_path, "manifest.jsonl")
            archive.write(error_path, "errors.jsonl")
        else:
            for path in (manifest_path, error_path):
                with path.open("rb") as stream:
                    preview = stream.read(PREVIEW_LIMIT)
                preview = preview[:preview.rfind(b"\n") + 1]
                archive.writestr(path.stem + ".preview.jsonl", preview)
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("game_dir", help="Local, legally owned game directory; read only")
    parser.add_argument("--output", required=True, help="New directory outside game directory")
    args = parser.parse_args(argv)
    try:
        result = run_scan(args.game_dir, args.output)
    except (OSError, ValueError) as exc:
        print("Probe failed: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps({key: result[key] for key in ("complete", "files_hashed", "bytes_hashed", "errors", "skipped")}))
    print("Reports: " + str(Path(args.output).resolve()))
    return 0 if result["complete"] else 1


if __name__ == "__main__":
    sys.exit(main())
