import io
import struct
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
from tools import pfs_access_probe
from tools.pfs_access_probe import parse_access


def fixture(mode=0xD):
    data = bytearray(0x3000)
    data[:4] = b'\x7fCNT'
    struct.pack_into('>Q', data, 0x430, len(data))
    struct.pack_into('>QQQ', data, 0x408, 0, 0x1000, 0x2000)
    struct.pack_into('<qq', data, 0x1000, 1, 20130315)
    struct.pack_into('<H', data, 0x101c, mode)
    struct.pack_into('<I', data, 0x1020, 0x1000)
    payload = b'PRIVATE_PAYLOAD!!'
    data[0x2000:0x2000+len(payload)] = payload
    return data


class AccessTests(unittest.TestCase):
    def test_inspection_uses_unbuffered_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'synthetic.pkg'
            source.write_bytes(fixture())
            with pfs_access_probe.open_source(source, buffering=0) as (stream, _):
                self.assertIsInstance(stream, io.FileIO)
                sizes = []
                original_read = stream.read
                def read(length=-1):
                    sizes.append(length)
                    return original_read(length)
                with patch.object(stream, 'read', side_effect=read):
                    parse_access(stream, source.stat().st_size)
                self.assertEqual(sizes, [4, 8, 24, 72])
            with patch.object(pfs_access_probe, 'open_source', wraps=pfs_access_probe.open_source) as opener:
                pfs_access_probe.inspect(source)
                opener.assert_called_once_with(source, buffering=0)

    def test_encrypted_stops_at_header(self):
        data = fixture()
        result = parse_access(io.BytesIO(data), len(data))
        self.assertEqual(result['status'], 'ENCRYPTED_FLAG_SET')
        self.assertFalse(result['payload_read'])
        self.assertEqual([(r['offset'],r['length']) for r in result['ranges']],
                         [(0,4),(0x430,8),(0x408,24),(0x1000,72)])
        self.assertNotIn('PRIVATE_PAYLOAD', str(result))

    def test_unencrypted_is_not_claimed_accessible(self):
        data = fixture(8)
        result = parse_access(io.BytesIO(data), len(data))
        self.assertEqual(result['status'], 'NO_ENCRYPTION_FLAG_DECLARED')
        self.assertFalse(result['payload_read'])

    def test_rejects_ranges_and_bad_block_sizes(self):
        for field, fmt, value in ((0x410,'>Q',0), (0x418,'>Q',0xFFFFFFFF),
                                 (0x1020,'<I',0), (0x1020,'<I',513)):
            data = fixture()
            struct.pack_into(fmt,data,field,value)
            with self.subTest(field=field,value=value), self.assertRaises(ValueError):
                parse_access(io.BytesIO(data), len(data))

    def test_unrecognized_and_absent(self):
        data = fixture()
        data[0x1000] = 2
        self.assertEqual(parse_access(io.BytesIO(data),len(data))['status'], 'UNRECOGNIZED_PFS_HEADER')
        struct.pack_into('>QQ', data, 0x410, 0, 0)
        self.assertEqual(parse_access(io.BytesIO(data),len(data))['status'], 'NO_PFS_RANGE_DECLARED')

    def test_truncation(self):
        with self.assertRaises(ValueError):
            parse_access(io.BytesIO(b'\x7fCNT'),4)
