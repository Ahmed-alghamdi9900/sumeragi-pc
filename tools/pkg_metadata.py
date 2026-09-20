#!/usr/bin/env python3
"""Bounded, read-only PKG metadata probe; no decryption or payload extraction.

Layout references (accessed 2026-09-20): maxton/LibOrbisPkg master,
LibOrbisPkg/PKG/{PkgReader.cs,Entry.cs,Enums.cs}. Only header fields, numeric
entry descriptors and allowlisted fields from plaintext PARAM.SFO are reported.
Reports are private local evidence, never public repository content.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import struct
import sys

try:
    from .local_probe.scan_game import open_source, unchanged, read_at, parse_sfo, is_link, SFO_LIMIT
except ImportError:
    from local_probe.scan_game import open_source, unchanged, read_at, parse_sfo, is_link, SFO_LIMIT

TOOL_VERSION = "pkg-metadata/0.1"
ENTRY_LIMIT = 4096
PARAM_SFO = 0x1000


def parse_pkg(stream, size):
    ranges = []

    def read(offset, length, purpose):
        data = read_at(stream, offset, length, size)
        ranges.append({"offset": offset, "length": length, "purpose": purpose,
                       "sha256": hashlib.sha256(data).hexdigest()})
        return data

    header = read(0, 0xa0, "public_header")
    if header[:4] != b"\x7fCNT":
        raise ValueError("not a CNT package")
    package_size = struct.unpack(">Q", read(0x430, 8, "declared_package_size"))[0]
    if package_size != size:
        raise ValueError("declared package size differs from source size")
    fields = {name: struct.unpack_from(">I", header, off)[0] for name, off in (
        ("flags", 4), ("entry_count", 0x10), ("entry_table_offset", 0x18),
        ("content_type", 0x74), ("content_flags", 0x78))}
    fields["package_size"] = package_size
    content_id = header[0x40:0x70].split(b"\0", 1)[0]
    if any(c < 0x20 or c > 0x7e for c in content_id):
        raise ValueError("content ID is not printable ASCII")
    fields["content_id"] = content_id.decode("ascii")
    count, table_offset = fields["entry_count"], fields["entry_table_offset"]
    if count > ENTRY_LIMIT:
        raise ValueError("entry count exceeds 4096-entry probe limit")
    if table_offset < 0x438:
        raise ValueError("entry table overlaps required header")
    raw = read(table_offset, count * 32, "numeric_entry_table")
    entries = []
    for i in range(count):
        values = struct.unpack_from(">6I", raw, i * 32)
        entry = dict(zip(("id", "name_offset", "flags1", "flags2", "offset", "size"), values))
        if entry["offset"] > size or entry["size"] > size - entry["offset"]:
            raise ValueError("entry range outside package")
        entry["encrypted_flag"] = bool(entry["flags1"] & 0x80000000)
        entries.append(entry)
    candidates = [entry for entry in entries if entry["id"] == PARAM_SFO]
    sfo = {"status": "absent"}
    if len(candidates) > 1:
        raise ValueError("duplicate PARAM.SFO entries")
    if candidates:
        entry = candidates[0]
        start, length = entry["offset"], entry["size"]
        end = start + length
        if entry["encrypted_flag"]:
            sfo = {"status": "not_read", "reason": "encrypted_flag_set"}
        elif length > SFO_LIMIT:
            sfo = {"status": "not_read", "reason": "exceeds_metadata_limit"}
        elif start < 0x438 or (start < table_offset + count * 32 and table_offset < end):
            raise ValueError("PARAM.SFO overlaps header or table")
        elif any(other is not entry and other["size"] and
                 start < other["offset"] + other["size"] and other["offset"] < end
                 for other in entries):
            raise ValueError("PARAM.SFO overlaps another entry")
        else:
            # Check magic before reading the bounded SFO. Never try decryption.
            magic = read(start, min(4, length), "param_sfo_magic")
            if magic != b"\0PSF":
                sfo = {"status": "not_read", "reason": "plaintext_sfo_magic_absent"}
            else:
                data = read(start, length, "plaintext_param_sfo")
                sfo = parse_sfo(io.BytesIO(data), length)
    return {"schema_version": 1, "tool": TOOL_VERSION, "status": "parsed",
            "header": fields, "entries": entries, "param_sfo": sfo,
            "metadata_ranges": ranges,
            "source_identity": {"edition": "UNKNOWN", "patch_state": "UNKNOWN",
                                "bundled_content": "UNKNOWN", "executable_accessibility": "UNKNOWN"},
            "limitations": ["No authenticity/signature verification.",
                            "Numeric entries are container metadata, not a game file inventory.",
                            "No filename-based edition inference, decryption or extraction.",
                            "Range hashes are not a full source SHA-256."]}


def inspect_pkg(path):
    path = Path(os.path.abspath(path))
    for ancestor in (path, *path.parents):
        if is_link(ancestor.lstat()):
            raise ValueError("source and ancestors must not be links/reparse points")
    with open_source(path) as (stream, before):
        result = parse_pkg(stream, before.st_size)
        if not unchanged(before, os.fstat(stream.fileno())) or not unchanged(before, path.lstat()):
            raise OSError("source changed during metadata inspection")
    result["source"] = {"relative_path": path.name, "size": before.st_size,
                        "mtime_ns": before.st_mtime_ns, "ctime_ns": before.st_ctime_ns,
                        "device": before.st_dev, "inode": before.st_ino,
                        "full_sha256": None}
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package")
    parser.add_argument("--output", required=True, help="New private JSON report outside source directory")
    args = parser.parse_args(argv)
    try:
        source = Path(args.package).absolute()
        output = Path(args.output).absolute()
        for ancestor in (output, *output.parents):
            if ancestor.exists() or ancestor.is_symlink():
                if is_link(ancestor.lstat()):
                    raise ValueError("output and ancestors must not be links/reparse points")
        if output.resolve().is_relative_to(source.resolve().parent):
            raise ValueError("output must be outside source directory")
        result = inspect_pkg(source)
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("x", encoding="utf-8") as report:
            json.dump(result, report, indent=2, ensure_ascii=True)
            report.write("\n")
    except (OSError, ValueError, struct.error) as exc:
        print("Metadata probe failed: " + str(exc), file=sys.stderr)
        return 2
    print("Private PKG metadata report written; edition and content remain unverified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
