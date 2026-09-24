import io
import struct
import unittest
from tools.self_tables import audit_tables,load_mappings
from tools.self_dependencies import DYNLIBDATA,STRSZ


class TableTests(unittest.TestCase):
    def fixture(self):
        data=struct.pack('<IBBHQQ',0,0,0,0,0,0)+struct.pack('<QQq',0x1000,8,0)
        m={'programs':[dict(type=1,index=0,elf_offset=0,virtual_address=0x1000,file_size=48,memory_size=64),
                       dict(type=DYNLIBDATA,index=1,elf_offset=0,virtual_address=0,file_size=48,memory_size=0)],
           'segments':[dict(blocked=True,id=0,offset=0,size=48,memory_size=48,encrypted=False,compressed=False)]}
        values={0x6100003b:24,0x61000033:24,0x6100002b:7,0x61000039:0,0x6100003f:24,STRSZ:1,0x6100002f:24,0x61000031:24,0x61000029:48,0x6100002d:0}
        return data,m,[dict(tag=k,value=v) for k,v in values.items()]

    def test_valid_and_bss_target(self):
        data,m,t=self.fixture()
        data=data[:24]+struct.pack('<QQq',0x1038,8,0)
        r=audit_tables(io.BytesIO(data),len(data),m,t)
        self.assertEqual(r['symbol_count'],1)
        self.assertEqual(r['relocations']['rela']['known_width_targets_outside_loads'],0)

    def test_bad_symbol_reference_and_name(self):
        data,m,t=self.fixture()
        for bad in (struct.pack('<I',1)+data[4:],data[:24]+struct.pack('<QQq',0x1000,(1<<32)|8,0)):
            with self.assertRaises(ValueError):audit_tables(io.BytesIO(bad),len(bad),m,t)

    def test_outside_target_reported(self):
        data,m,t=self.fixture();data=data[:24]+struct.pack('<QQq',0x1039,8,0)
        self.assertEqual(audit_tables(io.BytesIO(data),len(data),m,t)['relocations']['rela']['known_width_targets_outside_loads'],1)

    def test_bad_stride_bounds_and_protection(self):
        for tag,value in ((0x6100003b,16),(0x61000031,25),(0x6100002f,40),(0x6100002b,0)):
            data,m,t=self.fixture()
            for item in t:
                if item['tag']==tag:item['value']=value
            with self.subTest(tag=tag),self.assertRaises(ValueError):audit_tables(io.BytesIO(data),len(data),m,t)
        data,m,t=self.fixture();m['segments'][0]['encrypted']=True
        with self.assertRaises(ValueError):audit_tables(io.BytesIO(data),len(data),m,t)

    def test_load_overlap_rejected(self):
        _,m,_=self.fixture();m['programs'].append(dict(m['programs'][0]))
        with self.assertRaises(ValueError):load_mappings(m)
