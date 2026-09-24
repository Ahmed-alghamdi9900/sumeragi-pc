import io
import unittest
from tools.self_dependencies import resolve_needed, STRTAB, STRSZ, DYNLIBDATA


class DependencyTests(unittest.TestCase):
    def fixture(self):
        strings=b'\0syntheticA.prx\0syntheticB.prx\0'
        metadata={'programs':[dict(type=DYNLIBDATA,index=0,elf_offset=100,file_size=len(strings))],
                  'segments':[dict(blocked=True,id=0,encrypted=False,compressed=False,
                                   offset=0,size=len(strings),memory_size=len(strings))]}
        tags=[dict(tag=STRTAB,value=0),dict(tag=STRSZ,value=len(strings)),
              dict(tag=1,value=1),dict(tag=1,value=16)]
        return strings,metadata,tags

    def test_valid_names(self):
        data,m,t=self.fixture(); t[-1]['value']=data.index(b'syntheticB')
        r=resolve_needed(io.BytesIO(data),len(data),m,t)
        self.assertEqual(r['dependency_names'],['syntheticA.prx','syntheticB.prx'])
        self.assertFalse(r['imports_bound'])

    def test_invalid_offset_empty_and_unterminated(self):
        for value in (-1,0,999):
            data,m,t=self.fixture();t[-1]['value']=value
            with self.subTest(value=value),self.assertRaises(ValueError):resolve_needed(io.BytesIO(data),len(data),m,t)
        data,m,t=self.fixture();data=data[:-1]+b'x'
        with self.assertRaises(ValueError):resolve_needed(io.BytesIO(data),len(data),m,t)

    def test_required_tags_and_container_bounds(self):
        for change in ('duplicate','missing','size','relative','protected'):
            data,m,t=self.fixture()
            if change=='duplicate':t.append(t[0])
            if change=='missing':t=t[1:]
            if change=='size':t[1]['value']=1048577
            if change=='relative':t[0]['value']=1
            if change=='protected':m['segments'][0]['encrypted']=True
            with self.subTest(change=change),self.assertRaises(ValueError):resolve_needed(io.BytesIO(data),len(data),m,t)

    def test_non_ascii_and_truncation(self):
        data,m,t=self.fixture()
        for bad in (data[:1]+b'\xff'+data[2:],data[:-1]):
            with self.assertRaises(ValueError):resolve_needed(io.BytesIO(bad),len(data),m,t)
