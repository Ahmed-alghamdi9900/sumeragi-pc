import io
import struct
import unittest
from tools.self_dynamic_probe import mapped_range, parse_dynamic
from tests.test_self_probe import fixture


class DynamicTests(unittest.TestCase):
    def metadata(self):
        return {'programs':[{'index':0,'elf_offset':100,'file_size':64}],
                'segments':[{'blocked':True,'id':0,'encrypted':False,'compressed':False,
                             'offset':256,'size':64,'memory_size':64}]}

    def test_mapping_and_boundaries(self):
        self.assertEqual(mapped_range(self.metadata(),116,16),272)
        for offset,length in ((99,16),(160,16),(100,0)):
            with self.assertRaises(ValueError): mapped_range(self.metadata(),offset,length)

    def test_protected_ambiguous_mismatched(self):
        for change in ('encrypted','compressed','size','duplicate'):
            m=self.metadata()
            if change=='duplicate': m['segments']*=2
            elif change=='size': m['segments'][0]['size']=63
            else: m['segments'][0][change]=True
            with self.subTest(change=change),self.assertRaises(ValueError): mapped_range(m,100,16)

    def test_dynamic_table(self):
        d=fixture()
        struct.pack_into('<I',d,128,2)
        d[256:320]=struct.pack('<qQqQqQqQ',1,8,1,16,0,0,99,999)
        result=parse_dynamic(io.BytesIO(d),len(d))
        self.assertEqual(result['standard_needed_tag_count'],2)
        self.assertEqual(len(result['tags']),2)
        self.assertFalse(result['names_read'])
        self.assertTrue(result['prerequisite_self_ranges'])
        self.assertIn('status', result['prerequisite_entry_mapping'])

    def test_missing_terminator_and_dimensions(self):
        for length in (63,64,65552):
            d=fixture(); struct.pack_into('<I',d,128,2)
            struct.pack_into('<Q',d,160,length)
            with self.subTest(length=length),self.assertRaises(ValueError): parse_dynamic(io.BytesIO(d),len(d))
