"""Synthetic fixtures only: no commercial assets or platform keys."""
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import struct
import tempfile
import unittest
from unittest import mock
import zipfile

MODULE = Path(__file__).resolve().parents[1] / "tools" / "local_probe" / "scan_game.py"
spec = importlib.util.spec_from_file_location("scan_game", MODULE)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


def sfo(fields):
    keys = bytearray()
    values = bytearray()
    entries = bytearray()
    for name, value in fields:
        encoded = value.encode("utf-8") + b"\0"
        entries.extend(struct.pack("<HHIII", len(keys), 0x0204, len(encoded), len(encoded), len(values)))
        keys.extend(name.encode("ascii") + b"\0")
        values.extend(encoded)
    key_offset = 20 + len(entries)
    return struct.pack("<4sIIII", b"\0PSF", 0x101, key_offset, key_offset + len(keys), len(fields)) + entries + keys + values


def elf64():
    ident = b"\x7fELF" + bytes([2, 1, 1, 0]) + bytes(8)
    return ident + struct.pack("<HHIQQQIHHHHHH", 2, 62, 1, 0x400000, 64, 0, 0, 64, 56, 1, 0, 0, 0) + struct.pack("<IIQQQQQQ", 1, 5, 0, 0x400000, 0, 120, 120, 4096)


class ProbeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        self.source.mkdir()
        self.output = self.root / "reports"

    def test_full_hash_manifest_and_metadata_only_bundle(self):
        payload = b"PRIVATE_ASSET_MARKER_" * 80000
        (self.source / "data.bin").write_bytes(payload)
        (self.source / "nested").mkdir()
        (self.source / "nested" / "param.sfo").write_bytes(sfo([("TITLE_ID", "TEST00001"), ("TITLE", "Synthetic"), ("SECRET", "do not export")]))
        summary = probe.run_scan(self.source, self.output)
        self.assertTrue(summary["complete"])
        self.assertEqual(summary["files_hashed"], 2)
        records = [json.loads(line) for line in (self.output / "manifest.jsonl").read_text().splitlines()]
        data = next(row for row in records if row["path"] == "data.bin")
        self.assertEqual(data["sha256"], hashlib.sha256(payload).hexdigest())
        fields = next(row for row in records if row.get("signature") == "SFO")
        self.assertEqual(fields["metadata"]["build_fields"]["TITLE_ID"], "TEST00001")
        self.assertNotIn("SECRET", fields["metadata"]["build_fields"])
        with zipfile.ZipFile(self.output / "SUMERAGI_INITIAL_ANALYSIS.zip") as archive:
            self.assertEqual(set(archive.namelist()), {"manifest.jsonl", "errors.jsonl", "summary.json"})
            for name in archive.namelist():
                exported = archive.read(name)
                self.assertNotIn(b"PRIVATE_ASSET_MARKER", exported)
                self.assertNotIn(b"do not export", exported)
                self.assertNotIn(str(self.source).encode(), exported)
        self.assertEqual((self.source / "data.bin").read_bytes(), payload)

    def test_no_output_in_source_and_no_overwrite(self):
        with self.assertRaises(ValueError):
            probe.run_scan(self.source, self.source / "output")
        self.assertFalse((self.source / "output").exists())
        self.output.mkdir()
        sentinel = self.output / "keep"
        sentinel.write_text("preserve")
        with self.assertRaises(ValueError):
            probe.run_scan(self.source, self.output)
        self.assertEqual(sentinel.read_text(), "preserve")

    def test_empty_directory_is_not_usable(self):
        self.assertEqual(probe.main([str(self.source), "--output", str(self.output)]), 1)
        self.assertFalse(json.loads((self.output / "summary.json").read_text())["complete"])

    def test_invalid_sfo_is_explicit_nonzero_but_still_hashed(self):
        (self.source / "param.sfo").write_bytes(b"\0PSFbad")
        self.assertEqual(probe.main([str(self.source), "--output", str(self.output)]), 1)
        row = json.loads((self.output / "manifest.jsonl").read_text())
        self.assertEqual(row["status"], "metadata_error")
        self.assertEqual(len(row["sha256"]), 64)

    def test_valid_elf_and_out_of_bounds_segment(self):
        data = elf64()
        parsed = probe.parse_elf(io.BytesIO(data), len(data))
        self.assertEqual(parsed["machine"], 62)
        self.assertEqual(parsed["programs"][0]["file_size"], 120)
        self.assertEqual(parsed["imports_status"], "not_analyzed")
        invalid = bytearray(data)
        struct.pack_into("<Q", invalid, 64 + 32, 121)
        with self.assertRaises(ValueError):
            probe.parse_elf(io.BytesIO(invalid), len(invalid))

    def test_sfo_table_and_duplicate_bounds(self):
        valid = sfo([("APP_VER", "01.00")])
        self.assertEqual(probe.parse_sfo(io.BytesIO(valid), len(valid))["build_fields"]["APP_VER"], "01.00")
        malformed = bytearray(valid)
        struct.pack_into("<I", malformed, 16, 0xffffffff)
        with self.assertRaises(ValueError):
            probe.parse_sfo(io.BytesIO(malformed), len(malformed))
        duplicate = sfo([("TITLE_ID", "ONE"), ("TITLE_ID", "TWO")])
        with self.assertRaises(ValueError):
            probe.parse_sfo(io.BytesIO(duplicate), len(duplicate))

    def test_read_failure_does_not_claim_complete(self):
        (self.source / "unreadable.bin").write_bytes(b"test")
        with mock.patch.object(probe, "inspect_file", side_effect=PermissionError(13, "secret absolute source path")):
            result = probe.run_scan(self.source, self.output)
        self.assertFalse(result["complete"])
        self.assertNotIn("secret absolute", (self.output / "errors.jsonl").read_text())

    def test_changed_file_hash_discarded(self):
        path = self.source / "data.bin"
        path.write_bytes(b"test")
        with mock.patch.object(probe, "unchanged", side_effect=[True, False]):
            with self.assertRaises(OSError):
                probe.inspect_file(path)

    def test_link_and_reparse_detection(self):
        self.assertTrue(probe.is_link(mock.Mock(st_mode=stat.S_IFLNK, st_file_attributes=0)))
        self.assertTrue(probe.is_link(mock.Mock(st_mode=stat.S_IFDIR, st_file_attributes=0x400)))
        self.assertFalse(probe.is_link(mock.Mock(st_mode=stat.S_IFREG, st_file_attributes=0)))

    @unittest.skipUnless(os.name == "nt", "Windows timestamp API regression")
    def test_windows_cross_api_creation_change_time_difference(self):
        attrs = dict(st_dev=1, st_ino=2, st_size=3, st_mtime_ns=4)
        before = mock.Mock(**attrs, st_ctime_ns=100)
        opened = mock.Mock(**attrs, st_ctime_ns=200)
        self.assertTrue(probe.unchanged(before, opened))
        opened.st_mtime_ns = 5
        self.assertFalse(probe.unchanged(before, opened))

    def test_reparse_entry_skipped_without_reading_payload(self):
        path = self.source / "simulated_reparse.bin"
        path.write_bytes(b"must not read")
        with mock.patch.object(probe, "is_link", side_effect=lambda info: stat.S_ISREG(info.st_mode)), mock.patch.object(probe, "inspect_file") as inspect:
            result = probe.run_scan(self.source, self.output)
        inspect.assert_not_called()
        self.assertFalse(result["complete"])
        self.assertEqual(result["skipped"], 1)

    def test_symlink_never_hashed_when_supported(self):
        target = self.root / "outside.bin"
        target.write_bytes(b"outside")
        try:
            (self.source / "link.bin").symlink_to(target)
        except OSError:
            self.skipTest("OS does not permit creating symlinks for this account")
        result = probe.run_scan(self.source, self.output)
        self.assertFalse(result["complete"])
        self.assertEqual(result["files_hashed"], 0)
        self.assertEqual(result["skipped"], 1)

    def test_bundle_cap_omits_full_manifest_explicitly(self):
        (self.source / "data.bin").write_bytes(b"test")
        with mock.patch.object(probe, "BUNDLE_LIMIT", 2048), mock.patch.object(probe, "PREVIEW_LIMIT", 2000):
            result = probe.run_scan(self.source, self.output)
        self.assertFalse(result["bundle"]["full_manifest_included"])
        self.assertTrue((self.output / "manifest.jsonl").exists())
        with zipfile.ZipFile(self.output / "SUMERAGI_INITIAL_ANALYSIS.zip") as archive:
            self.assertNotIn("manifest.jsonl", archive.namelist())
            self.assertIn("manifest.preview.jsonl", archive.namelist())


if __name__ == "__main__":
    unittest.main()
