"""Try one ARC entry as one bounded zlib stream; retain only sizes and hashes.

No names, decoded assets, or payload bytes are emitted. No raw-deflate fallback.
Reference: https://docs.python.org/3/library/zlib.html
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import zlib
try:
    from .arc_probe import parse_arc
    from .local_probe.scan_game import open_source, read_at, unchanged, is_link
except ImportError:
    from arc_probe import parse_arc
    from local_probe.scan_game import open_source, read_at, unchanged, is_link

MAX_INPUT = 4 * 1024 * 1024
MAX_OUTPUT = 16 * 1024 * 1024


def probe_entry(stream, size, index, output_limit=MAX_OUTPUT):
    if not 1 <= output_limit <= MAX_OUTPUT:
        raise ValueError('invalid output limit')
    table = parse_arc(stream, size)
    if not 0 <= index < table['entry_count']:
        raise ValueError('entry index outside table')
    entry = table['entries'][index]
    if not 0 < entry['stored_size'] <= MAX_INPUT:
        raise ValueError('stored input outside bounded experiment limit')
    packed = read_at(stream, entry['offset'], entry['stored_size'], size)
    decoder = zlib.decompressobj()
    try:
        # One extra byte detects output overflow; never call unbounded flush().
        decoded = decoder.decompress(packed, output_limit + 1)
    except zlib.error as exc:
        raise ValueError('entry is not a valid supported zlib stream') from exc
    if len(decoded) > output_limit or decoder.unconsumed_tail:
        raise ValueError('decoded output exceeds limit')
    if not decoder.eof:
        raise ValueError('incomplete zlib stream')
    if decoder.unused_data:
        raise ValueError('trailing data or concatenated streams unsupported')
    return dict(tool='arc-payload-probe/0.1', status='SINGLE_ZLIB_STREAM_VALIDATED',
                entry_index=index, stored_size=len(packed), decoded_size=len(decoded),
                stored_sha256=hashlib.sha256(packed).hexdigest(),
                decoded_sha256=hashlib.sha256(decoded).hexdigest(),
                table_metadata_sha256=table['metadata_sha256'],
                size_flags_raw=entry['size_flags_raw'],
                output_limit=output_limit, payload_written=False, names_read=False,
                limitation='One entry only; decoded resource semantics and packed size flags remain unknown.')


def inspect(source, index):
    source = Path(os.path.abspath(source))
    for p in (source, *source.parents):
        if is_link(p.lstat()):
            raise ValueError('links/reparse paths unsupported')
    with open_source(source, buffering=0) as (stream, before):
        result = probe_entry(stream, before.st_size, index)
        if not unchanged(before, os.fstat(stream.fileno())) or not unchanged(before, source.lstat()):
            raise OSError('source changed during inspection')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('--entry', type=int, default=0)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        output = args.output.absolute()
        for p in (output, *output.parents):
            if (p.exists() or p.is_symlink()) and is_link(p.lstat()):
                raise ValueError('links/reparse output unsupported')
        if output.resolve().is_relative_to(args.archive.resolve().parent):
            raise ValueError('output must be outside source folder')
        result = inspect(args.archive, args.entry)
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open('x', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
            f.write('\n')
        print(result['status'])
    except (OSError, ValueError) as exc:
        parser.exit(2, f'Probe failed: {exc}\n')


if __name__ == '__main__':
    main()
