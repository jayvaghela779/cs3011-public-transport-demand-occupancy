import sys
from pathlib import Path

# Make tests/sunt_fixture.py importable as a plain module.
sys.path.insert(0, str(Path(__file__).parent))
