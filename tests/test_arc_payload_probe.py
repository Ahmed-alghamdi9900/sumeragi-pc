import hashlib
import io
import struct
import unittest
import zlib
from tools.arc_payload_probe import probe_entry, MAX_INPUT


def fixture(payload):
    return struct.pack('<4sHH', b'ARC\0', 7, 1) + b'N'*64 + struct.pack('<IIII', 1, len(payload), 0, 88) + payload


class PayloadTests(unittest.TestCase):
    def probe(self, payload, limit=1024):
        data=fixture(payload)
        return probe_entry(io.BytesIO(data), len(data), 0, limit)

    def test_valid_and_exact_limit(self):
        original=b'synthetic data'*20
        result=self.probe(zlib.compress(original), len(original))
        self.assertEqual(result['decoded_sha256'], hashlib.sha256(original).hexdigest())
        self.assertEqual(result['decoded_size'], len(original))
        self.assertNotIn('synthetic data', str(result))

    def test_empty_decoded_stream(self):
        self.assertEqual(self.probe(zlib.compress(b''))['decoded_size'],0)

    def test_overflow(self):
        with self.assertRaisesRegex(ValueError,'exceeds limit'):
            self.probe(zlib.compress(b'A'*10000),100)

    def test_truncated_corrupt_trailing_and_concatenated(self):
        packed=zlib.compress(b'fixture')
        for bad in (packed[:-1], packed[:-1]+bytes([packed[-1]^1]), packed+b'x', packed+packed, b'bad'):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                self.probe(bad)

    def test_index_and_limits(self):
        data=fixture(zlib.compress(b'a'))
        for index,limit in ((-1,1),(1,1),(0,0),(0,16777217)):
            with self.subTest(index=index,limit=limit),self.assertRaises(ValueError):
                probe_entry(io.BytesIO(data),len(data),index,limit)

    def test_oversized_input_rejected_before_payload_read(self):
        data=bytearray(fixture(b'x'))
        struct.pack_into('<I',data,76,MAX_INPUT+1)
        stream=io.BytesIO(data)
        with self.assertRaisesRegex(ValueError,'stored input'):
            probe_entry(stream,88+MAX_INPUT+1,0)
        self.assertEqual(stream.tell(),88)
