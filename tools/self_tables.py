"""Bounded numeric symbol/relocation audit. Does not apply relocations or execute.

SCE dynamic-data tag layout reference: shadPS4 core/loader/elf.h and core/module.cpp.
Reports have numeric counts/hashes only. Symbol names are not decoded.
"""
from collections import Counter
import hashlib
import struct
from .self_dependencies import unique, DYNLIBDATA, STRSZ
from .self_dynamic_probe import mapped_range
from .local_probe.scan_game import read_at


def load_mappings(metadata):
    loads = [p for p in metadata['programs'] if p['type'] == 1 and p['memory_size']]
    if not loads:
        raise ValueError('no loadable memory ranges')
    end = 0
    for p in sorted(loads, key=lambda x:x['virtual_address']):
        start = p['virtual_address']
        if start < end or start + p['memory_size'] > 1 << 64:
            raise ValueError('overlapping/overflowing loadable memory')
        end = start + p['memory_size']
        if p['file_size']:
            mapped_range(metadata, p['elf_offset'], p['file_size'])
    return loads


def audit_tables(stream, size, metadata, tags):
    loads = load_mappings(metadata)
    containers = [p for p in metadata['programs'] if p['type'] == DYNLIBDATA]
    if len(containers) != 1:
        raise ValueError('expected unique dynamic-data container')
    container = containers[0]
    ranges = []
    def table(offset_tag, size_tag, entry_size):
        relative, length = unique(tags, offset_tag), unique(tags, size_tag)
        if relative < 0 or length < 0 or length > 16*1024*1024 or length % entry_size or relative+length > container['file_size']:
            raise ValueError('invalid bounded table range or stride')
        if not length:
            return b''
        offset = mapped_range(metadata, container['elf_offset']+relative, length)
        data = read_at(stream, offset, length, size)
        ranges.append(dict(offset=offset,length=length,sha256=hashlib.sha256(data).hexdigest()))
        return data
    if unique(tags,0x6100003b) != 24 or unique(tags,0x61000033) != 24:
        raise ValueError('unsupported symbol/RELA entry size')
    if unique(tags,0x6100002b) != 7:
        raise ValueError('PLT table is not RELA')
    symbols = table(0x61000039,0x6100003f,24)
    symbol_count = len(symbols)//24
    if not symbol_count:
        raise ValueError('empty symbol table')
    string_size = unique(tags,STRSZ)
    if not 1 <= string_size <= 1024*1024:
        raise ValueError('invalid string table size')
    undefined=0
    for name,info,other,section,value,length in struct.iter_unpack('<IBBHQQ',symbols):
        if name >= string_size:
            raise ValueError('symbol string offset outside table')
        undefined += section == 0
    tables = {}
    for label,off_tag,size_tag in [('rela',0x6100002f,0x61000031),('plt_rela',0x61000029,0x6100002d)]:
        raw = table(off_tag,size_tag,24)
        types=Counter(); outside=0; unknown_width=0
        for address,info,addend in struct.iter_unpack('<QQq',raw):
            symbol,kind = info>>32, info&0xffffffff
            if symbol >= symbol_count:
                raise ValueError('relocation symbol index outside symbol table')
            types[kind]+=1
            # Validate eight-byte target ranges only for these known x86-64 types.
            if kind in (1,6,7,8,16):
                outside += not any(p['virtual_address']<=address and address+8<=p['virtual_address']+p['memory_size'] for p in loads)
            else:
                unknown_width += 1
        tables[label]=dict(entries=len(raw)//24,types=dict(types),known_width_targets_outside_loads=outside,unknown_target_width=unknown_width)
    return dict(status='NUMERIC_TABLES_AUDITED',symbol_count=symbol_count,
                undefined_symbol_records=undefined,relocations=tables,ranges=ranges,
                load_segment_count=len(loads),relocations_applied=False,
                limitation='Structural checks only; symbol names, relocation semantics and runtime compatibility unverified.')
