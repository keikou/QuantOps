import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TEST_RUNTIME_DIR = ROOT / "runtime" / f"pytest-{os.getpid()}"
TEST_RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("AHB_RUNTIME_DIR", str(TEST_RUNTIME_DIR))
