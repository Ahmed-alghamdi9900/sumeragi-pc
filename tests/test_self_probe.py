import io
import struct
import unittest
from tools.self_probe import parse_self

def fixture(flags=0x804):
    data=bytearray(320)
    data[:4]=bytes.fromhex('4f153d1d')
    data[6]=1
    struct.pack_into('<HHI',data,12,256,0,len(data))
    struct.pack_into('<H',data,24,1)
    struct.pack_into('<QQQQ',data,32,flags,256,64,64)
    data[64:71]=b'\x7fELF\x02\x01\x01'
    struct.pack_into('<HHIQQQIHHHHHH',data,80,0xfe10,62,1,0x1004,64,0,0,64,56,1,0,0,0)
    struct.pack_into('<IIQQQQQQ',data,128,1,5,0,0x1000,0,64,64,16)
    data[256:320]=b'X'*64
    return data

class SelfTests(unittest.TestCase):
    def test_unsupported_self_endian_stops_after_header(self):
        for endian in (0,2,255):
            d=fixture(); d[6]=endian; stream=io.BytesIO(d)
            with self.subTest(endian=endian),self.assertRaisesRegex(ValueError,'little-endian SELF'):
                parse_self(stream,len(d))
            self.assertEqual(stream.tell(),32)
    def test_entry_maps_with_correct_remaining_length(self):
        d=fixture(); r=parse_self(io.BytesIO(d),len(d))
        self.assertEqual(r['entry_mapping']['source_offset'],260)
        self.assertEqual(r['entry_mapping']['length'],60)
        self.assertNotIn('XXXX',str(r))
    def test_protected_or_compressed_no_entry_read(self):
        for flag in (0x806,0x80c):
            d=fixture(flag); r=parse_self(io.BytesIO(d),len(d))
            self.assertEqual(r['entry_mapping']['status'],'PROTECTED_OR_COMPRESSED_SEGMENT_NOT_READ')
            self.assertTrue(all(x['offset']+x['length']<=256 for x in r['ranges']))
    def test_invalid_ranges(self):
        for offset,fmt,value in ((24,'<H',257),(40,'<Q',319),(48,'<Q',65),(120,'<H',257)):
            d=fixture(); struct.pack_into(fmt,d,offset,value)
            with self.subTest(offset=offset),self.assertRaises(ValueError):parse_self(io.BytesIO(d),len(d))
    def test_entry_outside_segment(self):
        d=fixture();struct.pack_into('<Q',d,88,0x2000)
        self.assertEqual(parse_self(io.BytesIO(d),len(d))['entry_mapping']['status'],'NO_UNIQUE_EXECUTABLE_ENTRY_MAPPING')
    def test_truncation(self):
        for n in (0,31,63,100):
            d=fixture()[:n]
            with self.subTest(n=n),self.assertRaises(ValueError):parse_self(io.BytesIO(d),len(d))
