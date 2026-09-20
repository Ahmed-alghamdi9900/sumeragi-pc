# Windows tooling validation

The initial toolkit uses Python 3.11+ and only the standard library. No dependency
installation is needed. A native game runtime build does not exist yet; M0 is open.

Run from the repository root with a working Python interpreter:

```powershell
python -m unittest discover -s tests -v
python tools/project_memory.py init
python tools/project_memory.py export
```

`Run-InitialAnalysis.ps1` searches for the Codex bundled Python or Python 3.11+.
It does not install software or change execution policy. Debug/Release native
build configurations will be added after the evidence-based architecture decision.
