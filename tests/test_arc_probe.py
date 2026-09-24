import io
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from tools import arc_probe


def fixture(entries=((168, 4), (172, 4))):
    data = bytearray(max([8 + 80 * len(entries)] + [o + n for o, n in entries]))
    struct.pack_into('<4sHH', data, 0, b'ARC\0', 7, len(entries))
    for i, (offset, length) in enumerate(entries):
        data[8+i*80:8+i*80+64] = b'SYNTHETIC_PRIVATE_NAME'.ljust(64, b'\0')
        struct.pack_into('<IIII', data, 72+i*80, 123, length, 0x40000010, offset)
    return data


class ArcProbeTests(unittest.TestCase):
    def test_only_header_and_numeric_suffixes_read(self):
        data = fixture()
        stream = io.BytesIO(data)
        ranges = []
        original = stream.read
        def read(length=-1):
            ranges.append((stream.tell(), length))
            return original(length)
        with patch.object(stream, 'read', side_effect=read):
            result = arc_probe.parse_arc(stream, len(data))
        self.assertEqual(ranges, [(0, 8), (72, 16), (152, 16)])
        self.assertEqual(result['bytes_read'], 40)
        self.assertEqual(result['entry_count'], 2)
        self.assertFalse(result['payload_read'])
        self.assertNotIn('SYNTHETIC_PRIVATE_NAME', json.dumps(result))

    def test_short_table_and_wrong_formats(self):
        for data in (b'', fixture()[:100], b'CRA\0'+fixture()[4:],
                     b'ARC\0\x08\x00'+fixture()[6:]):
            with self.subTest(length=len(data)), self.assertRaises(ValueError):
                arc_probe.parse_arc(io.BytesIO(data), len(data))

    def test_payload_bounds(self):
        for offset, length in ((0, 4), (167, 4), (177, 0), (174, 4), (0xffffffff, 4)):
            data = fixture()
            struct.pack_into('<I', data, 76, length)
            struct.pack_into('<I', data, 84, offset)
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                arc_probe.parse_arc(io.BytesIO(data), len(data))

    def test_overlaps_are_reported_without_inventing_format_rule(self):
        data = fixture(((168, 8), (172, 4)))
        result = arc_probe.parse_arc(io.BytesIO(data), len(data))
        self.assertEqual(result['overlapping_range_count'], 1)

    def test_empty_archive_and_zero_length_end(self):
        for entries in ((), ((88, 0),)):
            data = fixture(entries)
            result = arc_probe.parse_arc(io.BytesIO(data), len(data))
            self.assertEqual(result['entry_count'], len(entries))

    def test_truncated_stream_with_claimed_larger_size(self):
        with self.assertRaises(ValueError):
            arc_probe.parse_arc(io.BytesIO(fixture()[:75]), 176)

    def test_inspect_unbuffered_and_source_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp)/'synthetic.arc'
            data = fixture()
            source.write_bytes(data)
            with patch.object(arc_probe, 'open_source', wraps=arc_probe.open_source) as opener:
                result = arc_probe.inspect(source)
            opener.assert_called_once_with(source, buffering=0)
            self.assertEqual(source.read_bytes(), data)
            self.assertIsNone(result['source']['full_sha256'])
            with patch.object(arc_probe, 'unchanged', return_value=False):
                with self.assertRaises(OSError):
                    arc_probe.inspect(source)


if __name__ == '__main__':
    unittest.main()
