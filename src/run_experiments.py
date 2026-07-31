import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

subprocess.run(
    [sys.executable, "-u", "-m", "src.diagnostic_test"],
    cwd=PROJECT_ROOT,
    check=True
)
subprocess.run(
    [sys.executable, "-u", str(PROJECT_ROOT / "src" / "test_rag_system.py"), "--evaluate", "all"],
    cwd=PROJECT_ROOT,
    check=True
)
