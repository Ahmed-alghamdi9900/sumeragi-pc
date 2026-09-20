# Research log

2026-09-20: Inspected empty repository and supplied source folder; user subsequently
placed one PKG file there. Initial source read failed; preserve report rather than
claiming an inventory pass. Follow-up diagnostics pending.

Resolved: Windows lstat/fstat timestamp mismatch, independently reproduced and
regression tested. Base hash completed, then user added the update and a new full
scan hashed both files successfully. PKG public metadata verified by bounded reader.

Capcom's [official content correction](https://www.capcom.co.jp/support/faq/platform_ps4_basara_15thae_0146729.html)
states that eight planned attribute-change weapons were replaced with increased
starter and inscribed-weapon set quantities. Do not use the early 66-item marketing
claim as a local completeness criterion. Physical content still unverified.

The [official PlayStation product listing](https://store.playstation.com/ja-jp/product/JP0102-CUSA01159_00-VXGAMEXPACKAGEXV)
uses the content identifier observed in both packages. This supports title association,
not package authenticity, Anniversary inclusion, or update completeness.

Searches of official Capcom information did not establish the current final PS4
patch version. Record 01.02 as observed supplied update, not confirmed latest.

Public format references (hypotheses to validate against local bytes):

- [LibOrbisPkg header reader](https://github.com/maxton/LibOrbisPkg/blob/master/LibOrbisPkg/PKG/PkgReader.cs)
- [LibOrbisPkg structures](https://github.com/maxton/LibOrbisPkg/blob/master/LibOrbisPkg/PKG/Pkg.cs)

Use only header/metadata layouts. No project dependency or crypto implementation
is imported. Local evidence remains authoritative. Mutable upstream references
should be pinned before future format work depends on revisions.
