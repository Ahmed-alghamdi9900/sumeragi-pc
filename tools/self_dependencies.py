"""Resolve DT_NEEDED names locally from bounded SCE string-table metadata.

Return values contain private extracted names: never publish them or log them.
No loading, import binding or relocation execution is implemented.
"""
import hashlib
try:
    from .self_probe import parse_self
    from .self_dynamic_probe import parse_dynamic, mapped_range
    from .local_probe.scan_game import read_at
except ImportError:
    from self_probe import parse_self
    from self_dynamic_probe import parse_dynamic, mapped_range
    from local_probe.scan_game import read_at

STRTAB = 0x61000035
STRSZ = 0x61000037
DYNLIBDATA = 0x61000000


def unique(tags, tag):
    values = [x['value'] for x in tags if x['tag'] == tag]
    if len(values) != 1:
        raise ValueError('missing or duplicate required dynamic tag')
    return values[0]


def resolve_needed(stream, size, metadata, tags):
    containers = [p for p in metadata['programs'] if p['type'] == DYNLIBDATA]
    if len(containers) != 1:
        raise ValueError('expected unique SCE dynamic-data container')
    container = containers[0]
    relative, length = unique(tags, STRTAB), unique(tags, STRSZ)
    if not 1 <= length <= 1024 * 1024 or relative < 0 or relative + length > container['file_size']:
        raise ValueError('string table outside bounded dynamic-data container')
    offset = mapped_range(metadata, container['elf_offset'] + relative, length)
    strings = read_at(stream, offset, length, size)
    needed = [t['value'] for t in tags if t['tag'] == 1]
    names = []
    for index in needed:
        if not 0 <= index < length:
            raise ValueError('dependency string offset out of bounds')
        end = strings.find(b'\0', index, min(length, index + 1025))
        if end < 0 or end == index:
            raise ValueError('empty or unterminated dependency name')
        raw = strings[index:end]
        if any(b < 32 or b > 126 for b in raw):
            raise ValueError('unsupported dependency name encoding')
        names.append(raw.decode('ascii'))
    return dict(status='NEEDED_NAMES_READ_LOCALLY', dependency_names=names,
                dependency_count=len(names), unique_dependency_count=len(set(names)),
                string_table_range=dict(offset=offset, length=length,
                    sha256=hashlib.sha256(strings).hexdigest()),
                imports_bound=False, limitation='Names only; presence and ABI compatibility not established.')


def parse_dependencies(stream, size):
    metadata = parse_self(stream, size)
    dynamic = parse_dynamic(stream, size)
    result = resolve_needed(stream, size, metadata, dynamic['tags'])
    result['prerequisite_reads'] = dict(first_self=metadata['ranges'],
        second_self=dynamic['prerequisite_self_ranges'],
        dynamic=dict(offset=dynamic['source_offset'], length=dynamic['table_bytes'],
                     sha256=dynamic['table_sha256']))
    return result
