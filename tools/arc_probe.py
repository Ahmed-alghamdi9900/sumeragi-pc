"""Bounded ARC v7 table metadata; never reads names or archive payloads.

Layout reference: https://github.com/mikewii/ARCTool/blob/master/include/ARC.hpp
The 8-byte header and 80-byte records are a candidate layout, validated by bounds.
Packed size flags and compression methods deliberately remain uninterpreted.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import struct

try:
    from .local_probe.scan_game import open_source, read_at, unchanged, is_link
except ImportError:
    from local_probe.scan_game import open_source, read_at, unchanged, is_link


def parse_arc(stream, size):
    header = read_at(stream, 0, 8, size)
    magic, version, count = struct.unpack('<4sHH', header)
    if magic != b'ARC\0' or version != 7:
        raise ValueError('only little-endian ARC version 7 is supported')
    table_end = 8 + count * 80
    if table_end > size:
        raise ValueError('archive table exceeds file bounds')
    digest = hashlib.sha256(header)
    entries = []
    for index in range(count):
        # Skip the 64-byte filename field entirely, including in read provenance.
        raw = read_at(stream, 8 + index * 80 + 64, 16, size)
        digest.update(raw)
        type_id, stored_size, size_flags, offset = struct.unpack('<IIII', raw)
        if offset < table_end or offset > size or stored_size > size - offset:
            raise ValueError(f'entry {index} payload range outside supported bounds')
        entries.append(dict(index=index, type_id=type_id, stored_size=stored_size,
                            size_flags_raw=size_flags, offset=offset))
    spans = sorted((e['offset'], e['offset'] + e['stored_size'])
                   for e in entries if e['stored_size'])
    overlap_count = 0
    furthest = table_end
    for start, end in spans:
        overlap_count += start < furthest
        furthest = max(furthest, end)
    return dict(tool='arc-table-probe/0.1', status='TABLE_RANGES_IN_BOUNDS',
                version=version, entry_count=count, table_end=table_end,
                entries=entries, overlapping_range_count=overlap_count,
                total_stored_bytes=sum(e['stored_size'] for e in entries),
                bytes_read=8 + 16 * count,
                metadata_sha256=digest.hexdigest(),
                metadata_hash_definition='header followed by each 16-byte numeric record suffix in index order',
                names_read=False, payload_read=False, decompression_attempted=False,
                limitation='Candidate table structure only. Packed size flags, compression, resource types, engine identity and payload validity remain unverified.')


def inspect(source):
    source = Path(os.path.abspath(source))
    for parent in (source, *source.parents):
        if is_link(parent.lstat()):
            raise ValueError('source path must not contain links or reparse points')
    with open_source(source, buffering=0) as (stream, before):
        result = parse_arc(stream, before.st_size)
        if not unchanged(before, os.fstat(stream.fileno())) or not unchanged(before, source.lstat()):
            raise OSError('source changed during inspection')
    result['source'] = dict(size=before.st_size, mtime_ns=before.st_mtime_ns,
                            full_sha256=None)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    try:
        output = args.output.absolute()
        for parent in (output, *output.parents):
            if (parent.exists() or parent.is_symlink()) and is_link(parent.lstat()):
                raise ValueError('output path must not contain links or reparse points')
        if output.resolve().is_relative_to(args.archive.resolve().parent):
            raise ValueError('output must be outside source folder')
        result = inspect(args.archive)
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open('x', encoding='utf-8') as stream:
            json.dump(result, stream, indent=2)
            stream.write('\n')
        print(result['status'])
    except (OSError, ValueError) as exc:
        parser.exit(2, f'Probe failed: {exc}\n')


if __name__ == '__main__':
    main()
