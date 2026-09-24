"""Read numeric ELF64 dynamic tags through a unique unprotected SELF mapping.

No string tables, symbol names, dependency names or relocation payloads are read.
"""
import hashlib
import struct
try:
    from .self_probe import parse_self
    from .local_probe.scan_game import read_at
except ImportError:
    from self_probe import parse_self
    from local_probe.scan_game import read_at


def mapped_range(metadata, offset, length):
    if offset < 0 or length <= 0 or offset + length > 1 << 64:
        raise ValueError('invalid requested ELF range')
    candidates = []
    for program in metadata['programs']:
        start = program['elf_offset']
        if start <= offset and offset + length <= start + program['file_size']:
            for segment in metadata['segments']:
                if segment['blocked'] and segment['id'] == program['index']:
                    candidates.append((program, segment))
    if len(candidates) != 1:
        raise ValueError('no unique SELF mapping for dynamic range')
    program, segment = candidates[0]
    if segment['encrypted'] or segment['compressed']:
        raise ValueError('protected/compressed mapping unsupported')
    if segment['size'] != program['file_size'] or segment['memory_size'] != program['file_size']:
        raise ValueError('mapped segment sizes disagree')
    return segment['offset'] + offset - program['elf_offset']


def parse_dynamic(stream, size):
    metadata = parse_self(stream, size)
    dynamic = [p for p in metadata['programs'] if p['type'] == 2]
    if len(dynamic) != 1:
        raise ValueError('expected one PT_DYNAMIC')
    dynamic = dynamic[0]
    length = dynamic['file_size']
    if not 16 <= length <= 65536 or length % 16:
        raise ValueError('unsupported dynamic table size')
    offset = mapped_range(metadata, dynamic['elf_offset'], length)
    raw = read_at(stream, offset, length, size)
    tags = []
    for tag, value in struct.iter_unpack('<qQ', raw):
        if tag == 0:
            break
        tags.append({'tag': tag, 'value': value})
    else:
        raise ValueError('dynamic table missing DT_NULL terminator')
    return dict(tool='self-dynamic-probe/0.1', status='NUMERIC_DYNAMIC_TABLE_READ',
                source_offset=offset, table_bytes=length,
                table_sha256=hashlib.sha256(raw).hexdigest(), tags=tags,
                prerequisite_self_ranges=metadata['ranges'],
                prerequisite_entry_mapping=metadata['entry_mapping'],
                standard_needed_tag_count=sum(t['tag']==1 for t in tags),
                names_read=False, relocation_payload_read=False,
                limitation='Header-derived numeric table only; dependency resolution and relocation semantics unverified.')
