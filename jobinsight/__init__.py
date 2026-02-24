from __future__ import annotations

from pathlib import Path

# Compatibility package to support imports like `import jobinsight.xxx`
# while project modules currently live at the repository root.
_PKG_DIR = Path(__file__).resolve().parent
_ROOT_DIR = _PKG_DIR.parent

__version__ = "0.1.0"
__path__ = [str(_ROOT_DIR)]
