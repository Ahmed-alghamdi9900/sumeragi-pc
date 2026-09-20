"""Synthetic-only boundary and non-extraction checks for PKG metadata."""
import io
import struct
import unittest

from tools.pkg_metadata import parse_pkg


def fixture(payload=b"\0PSF" + struct.pack("<IIII", 0x101, 20, 20, 0), flags=0):
    data = bytearray(0x1000 + len(payload))
    data[:4] = b"\x7fCNT"
    struct.pack_into(">I", data, 0x10, 1)
    struct.pack_into(">I", data, 0x18, 0x800)
    struct.pack_into(">Q", data, 0x430, len(data))
    struct.pack_into(">6I", data, 0x800, 0x1000, 0, flags, 0, 0x1000, len(payload))
    data[0x1000:] = payload
    return data


def parse(data):
    return parse_pkg(io.BytesIO(data), len(data))


class PkgMetadataTests(unittest.TestCase):
    def test_valid_plaintext_metadata(self):
        result = parse(fixture())
        self.assertEqual(result["param_sfo"]["status"], "parsed")
        self.assertEqual(result["source_identity"]["edition"], "UNKNOWN")
        self.assertTrue(all(len(r["sha256"]) == 64 for r in result["metadata_ranges"]))

    def test_encrypted_entry_never_read(self):
        result = parse(fixture(flags=0x80000000))
        self.assertEqual(result["param_sfo"]["reason"], "encrypted_flag_set")
        self.assertTrue(all(r["offset"] < 0x1000 for r in result["metadata_ranges"]))

    def test_non_plaintext_only_reads_magic(self):
        result = parse(fixture(b"SECRET_PAYLOAD"))
        self.assertEqual(result["param_sfo"]["reason"], "plaintext_sfo_magic_absent")
        self.assertEqual(result["metadata_ranges"][-1]["length"], 4)
        self.assertNotIn("SECRET", str(result))

    def test_non_sfo_payload_never_read(self):
        data = fixture(b"PROTECTED_PAYLOAD")
        struct.pack_into(">I", data, 0x800, 0x10)
        result = parse(data)
        self.assertEqual(result["param_sfo"]["status"], "absent")
        self.assertTrue(all(r["offset"] < 0x1000 for r in result["metadata_ranges"]))

    def test_allowlisted_build_field_only(self):
        keys = b"APP_VER\0PRIVATE_FIELD\0"
        values = b"01.23\0SECRET\0"
        sfo = (b"\0PSF" + struct.pack("<IIII", 0x101, 52, 52 + len(keys), 2)
               + struct.pack("<HHIII", 0, 0x204, 6, 6, 0)
               + struct.pack("<HHIII", 8, 0x204, 7, 7, 6) + keys + values)
        result = parse(fixture(sfo))
        self.assertEqual(result["param_sfo"]["build_fields"], {"APP_VER": "01.23"})
        self.assertNotIn("SECRET", str(result))

    def test_oversized_sfo_never_read(self):
        result = parse(fixture(b"x" * (2 * 1024 * 1024 + 1)))
        self.assertEqual(result["param_sfo"]["reason"], "exceeds_metadata_limit")
        self.assertTrue(all(r["offset"] < 0x1000 for r in result["metadata_ranges"]))

    def test_truncated_headers(self):
        for length in (0, 159, 0x437):
            with self.subTest(length=length), self.assertRaises(ValueError):
                parse(fixture()[:length])

    def test_invalid_magic_and_size(self):
        for offset, value in ((0, 0), (0x437, 1)):
            data = fixture()
            data[offset] = value
            with self.assertRaises(ValueError):
                parse(data)

    def test_table_limit_and_bounds(self):
        for offset, value in ((0x10, 4097), (0x18, 0), (0x18, 0xfffffff0)):
            data = fixture()
            struct.pack_into(">I", data, offset, value)
            with self.assertRaises(ValueError):
                parse(data)

    def test_entry_bounds_and_metadata_overlap(self):
        for offset in (0, 0x800, 0xffffffff):
            data = fixture()
            struct.pack_into(">I", data, 0x810, offset)
            with self.assertRaises(ValueError):
                parse(data)

    def test_duplicate_sfo_rejected(self):
        data = fixture()
        struct.pack_into(">I", data, 0x10, 2)
        data[0x820:0x840] = data[0x800:0x820]
        with self.assertRaises(ValueError):
            parse(data)

    def test_overlap_protected_entry_rejected(self):
        data = fixture()
        struct.pack_into(">I", data, 0x10, 2)
        struct.pack_into(">6I", data, 0x820, 0x10, 0, 0x80000000, 0, 0x1000, 4)
        with self.assertRaises(ValueError):
            parse(data)


if __name__ == "__main__":
    unittest.main()
