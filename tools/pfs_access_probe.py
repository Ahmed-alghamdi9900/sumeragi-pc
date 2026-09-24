"""Inspect only the public outer PFS header; never read/decrypt filesystem payload.

Layout: LibOrbisPkg PKG/PkgReader.cs and PFS/PfsStructs.cs (2026-09-20).
Header flags are evidence of declared format, not authenticity or full compatibility.
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


def parse_access(stream, size):
    ranges = []

    def read(offset, length):
        data = read_at(stream, offset, length, size)
        ranges.append({'offset': offset, 'length': length,
                       'sha256': hashlib.sha256(data).hexdigest()})
        return data

    if read(0, 4) != b'\x7fCNT':
        raise ValueError('not a CNT package')
    if struct.unpack('>Q', read(0x430, 8))[0] != size:
        raise ValueError('declared package size mismatch')
    flags, offset, length = struct.unpack('>QQQ', read(0x408, 24))
    result = {'tool': 'pfs-access-probe/0.1', 'pkg_pfs_flags': flags,
              'pfs_offset': offset, 'pfs_length': length, 'ranges': ranges,
              'payload_read': False, 'decryption_attempted': False}
    if offset == 0 and length == 0:
        result['status'] = 'NO_PFS_RANGE_DECLARED'
        return result
    if offset < 0x5a0 or length < 72 or offset > size or length > size - offset:
        raise ValueError('invalid PFS range')
    header = read(offset, 72)
    version, magic = struct.unpack_from('<qq', header)
    if version != 1 or magic != 20130315:
        result['status'] = 'UNRECOGNIZED_PFS_HEADER'
        return result
    mode = struct.unpack_from('<H', header, 28)[0]
    block_size = struct.unpack_from('<I', header, 32)[0]
    if block_size < 512 or block_size > 1024*1024 or block_size & (block_size-1) or block_size > length:
        raise ValueError('unsupported or invalid PFS block size')
    result.update(mode=mode, block_size=block_size,
                  encrypted_flag=bool(mode & 4), signed_flag=bool(mode & 1),
                  status='ENCRYPTED_FLAG_SET' if mode & 4 else 'NO_ENCRYPTION_FLAG_DECLARED',
                  limitation='Outer header only. No directory, executable, asset or nested-image accessibility established.')
    return result


def inspect(source):
    source = Path(os.path.abspath(source))
    for parent in (source, *source.parents):
        if is_link(parent.lstat()):
            raise ValueError('source path must not contain reparse points or links')
    # Avoid BufferedReader prefetch beyond the explicitly requested header bytes.
    with open_source(source, buffering=0) as (stream, before):
        result = parse_access(stream, before.st_size)
        if not unchanged(before, os.fstat(stream.fileno())) or not unchanged(before, source.lstat()):
            raise OSError('source changed during inspection')
    result['source'] = {'name': source.name, 'size': before.st_size,
                        'mtime_ns': before.st_mtime_ns, 'full_sha256': None}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('package', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        output = args.output.absolute()
        for parent in (output, *output.parents):
            if (parent.exists() or parent.is_symlink()) and is_link(parent.lstat()):
                raise ValueError('output path must not contain links or reparse points')
        if output.resolve().is_relative_to(args.package.resolve().parent):
            raise ValueError('output must be outside source folder')
        result = inspect(args.package)
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open('x', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=True)
            f.write('\n')
        print(result['status'])
    except (OSError, ValueError) as exc:
        parser.exit(2, f'Probe failed: {exc}\n')


if __name__ == '__main__':
    main()
