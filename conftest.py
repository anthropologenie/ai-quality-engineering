"""Ensures the repository root is importable during test collection.

No pytest configuration (pytest.ini/pyproject.toml) or package structure
(__init__.py) existed anywhere in the repository prior to Sprint P2.2.1 —
flagged as an open convention gap during Sprint P2.2.0's discovery. This
file is the minimal, dependency-free fix so `pytest` (not just
`python -m pytest`) can resolve `import sample_rag...` from any invocation
directory.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
