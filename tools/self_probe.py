"""Bounded SELF/ELF metadata and entry-range mapping. No execution or decryption.

Layout reference: shadps4-emu/shadPS4 src/core/loader/elf.h.
Reports contain numeric metadata and hashes, never instruction bytes or strings.
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


def parse_self(stream, size):
    ranges = []
    def read(offset, length):
        data = read_at(stream, offset, length, size)
        ranges.append({'offset':offset,'length':length,'sha256':hashlib.sha256(data).hexdigest()})
        return data
    header = read(0,32)
    if header[:4] != bytes.fromhex('4f153d1d'):
        raise ValueError('not a SELF container')
    if header[6] != 1:
        raise ValueError('only little-endian SELF containers supported')
    header_size, metadata_size, declared_size = struct.unpack_from('<HHI',header,12)
    count = struct.unpack_from('<H',header,24)[0]
    if not 1 <= count <= 256 or declared_size > size or declared_size < header_size + metadata_size:
        raise ValueError('invalid SELF dimensions')
    elf_offset = 32 + count*32
    if elf_offset + 64 > header_size:
        raise ValueError('SELF descriptors exceed header')
    descriptors = read(32,count*32)
    segments = []
    for i in range(count):
        flags, offset, length, memory = struct.unpack_from('<QQQQ',descriptors,i*32)
        if offset > declared_size or length > declared_size-offset:
            raise ValueError('SELF segment outside declared file')
        if length and offset < header_size+metadata_size:
            raise ValueError('SELF segment overlaps headers')
        segments.append({'index':i,'flags':flags,'offset':offset,'size':length,'memory_size':memory,
                         'id':(flags>>20)&0xfff,'blocked':bool(flags&0x800),
                         'encrypted':bool(flags&2),'compressed':bool(flags&8)})
    elf = read(elf_offset,64)
    if elf[:7] != b'\x7fELF\x02\x01\x01':
        raise ValueError('only ELF64 little-endian version 1 supported')
    fields = struct.unpack_from('<HHIQQQIHHHHHH',elf,16)
    etype,machine,version,entry,phoff,shoff,flags,ehsize,phentsize,phnum,_,_,_ = fields
    if machine != 62 or version != 1 or ehsize != 64 or phentsize != 56 or not 1 <= phnum <= 256:
        raise ValueError('unsupported ELF machine/header dimensions')
    if phoff < 64 or elf_offset+phoff+phnum*56 > header_size:
        raise ValueError('ELF program table outside SELF header')
    raw = read(elf_offset+phoff,phnum*56)
    programs = []
    for i in range(phnum):
        t,pflags,offset,vaddr,paddr,filesz,memsz,align = struct.unpack_from('<IIQQQQQQ',raw,i*56)
        if t==1 and (filesz>memsz or vaddr+memsz > 1<<64):
            raise ValueError('invalid PT_LOAD memory range')
        programs.append({'index':i,'type':t,'flags':pflags,'elf_offset':offset,
                         'virtual_address':vaddr,'file_size':filesz,'memory_size':memsz,'alignment':align})
    mapping = {'status':'NO_UNIQUE_EXECUTABLE_ENTRY_MAPPING'}
    targets = [p for p in programs if p['type']==1 and p['flags']&1
               and p['virtual_address'] <= entry < p['virtual_address']+p['file_size']]
    if len(targets)==1:
        p=targets[0]
        matching=[s for s in segments if s['blocked'] and s['id']==p['index']]
        if len(matching)==1:
            s=matching[0]
            if s['encrypted'] or s['compressed']:
                mapping={'status':'PROTECTED_OR_COMPRESSED_SEGMENT_NOT_READ'}
            elif s['size']!=p['file_size'] or s['memory_size']!=p['file_size']:
                mapping={'status':'SEGMENT_SIZE_MISMATCH_NOT_READ'}
            else:
                delta=entry-p['virtual_address']
                offset=s['offset']+delta
                length=min(64,s['size']-delta)
                window=read(offset,length)
                mapping={'status':'BOUNDED_ENTRY_BYTES_READ', 'program_index':p['index'],
                         'self_segment_index':s['index'],'source_offset':offset,'length':length,
                         'sha256':hashlib.sha256(window).hexdigest(),
                         'instruction_decode':'NOT_PERFORMED','behavior_validation':'NOT_PERFORMED'}
    return {'tool':'self-probe/0.1','declared_size':declared_size,'actual_size':size,
            'trailing_bytes':size-declared_size,'elf_offset':elf_offset,'elf_type':etype,
            'machine':machine,'entry_address':entry,'segments':segments,'programs':programs,
            'entry_mapping':mapping,'ranges':ranges,'decryption_attempted':False,
            'limitations':['Header-derived mapping only; no authenticity or instruction semantics validation.',
                           'No ELF reconstruction, relocation, dependency analysis or execution.']}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    try:
        source=args.source.absolute()
        output=args.output.absolute()
        for p in (source,*source.parents,output,*output.parents):
            if (p.exists() or p.is_symlink()) and is_link(p.lstat()):
                raise ValueError('links/reparse paths not supported')
        if output.resolve().is_relative_to(source.resolve().parent):
            raise ValueError('output must be outside source folder')
        with open_source(source,buffering=0) as (stream,before):
            result=parse_self(stream,before.st_size)
            if not unchanged(before,os.fstat(stream.fileno())) or not unchanged(before,source.lstat()):
                raise OSError('source changed during inspection')
        result['source_name']=source.name
        output.parent.mkdir(parents=True,exist_ok=True)
        with output.open('x',encoding='utf-8') as f:
            json.dump(result,f,indent=2)
            f.write('\n')
        print(json.dumps(result['entry_mapping']))
    except (OSError,ValueError) as exc:
        parser.exit(2,f'Probe failed: {exc}\n')

if __name__=='__main__':
    main()
