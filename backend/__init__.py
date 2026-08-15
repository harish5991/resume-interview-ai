import sys
import os
from pathlib import Path

# Automatically add project root to sys.path so imports work in any IDE or working directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
