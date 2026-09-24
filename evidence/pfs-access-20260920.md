# Package filesystem access experiment

Question: is the outer filesystem marked as encrypted, or merely unsupported by
the initial probe? This is an access prerequisite, not a port architecture choice.

Implemented tools/pfs_access_probe.py. It reads exactly 108 bytes per recognized
package: CNT signature (4), declared package size (8), PFS placement fields (24),
and outer PFS header prefix (72). No inode tables, content payload, seeds, keys,
decryption or extraction. Records offsets/lengths/range hashes in private reports.

Executed against both supplied packages. Each reports recognized version/magic,
mode 13 (0xD), encryption flag set, and block size 65,536. This supports the specific
conclusion that both outer filesystems declare encryption. It does not authenticate
the packages or demonstrate access to nested filesystems, executable or assets.

Private final evidence: reports/pfs-base-r2.json, reports/pfs-update-r2.json,
reports/pfs-tests-r2.txt. First reports retained for audit.
Full source hashes remain in initial-r3 manifest. These header observations were
made separately; no new full hash or atomic association claimed.

Commands from repository root (private paths abbreviated):

```text
python tools/pfs_access_probe.py <base.pkg> --output reports/pfs-base.json
python tools/pfs_access_probe.py <update.pkg> --output reports/pfs-update.json
python -m unittest discover -s tests -v
```

Full local suite: 35 tests, 34 pass, 1 real symlink permission skip. Initial draft
fixture accidentally changed bytearray length; declared-size validation caught it.
Fixed fixture length and reran. No production validation was removed.

Independent review caught Python buffered input prefetching beyond requested ranges.
Probe now explicitly uses unbuffered FileIO; regression checks actual read call
sizes [4,8,24,72]. Both packages re-inspected after the fix. OS/device block caching
is outside this byte-request claim. No adjacent data was emitted by the earlier probe.

Format references:
- https://github.com/maxton/LibOrbisPkg/blob/master/LibOrbisPkg/PKG/PkgReader.cs
- https://github.com/maxton/LibOrbisPkg/blob/master/LibOrbisPkg/PFS/PfsStructs.cs

Next prerequisite: legally accessible readable executable/assets, ideally reflecting
the intended update. The owner has confirmed only packages exist. Do not repeat this
probe or full hashing without changed source/new evidence. No bypass is implemented.
