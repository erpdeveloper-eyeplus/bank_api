__version__ = "0.0.1"
import os, sys

# Ensure eazypay src is discoverable (apps/bank_api/src/eazypay)
src_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "src")
)
if src_path not in sys.path:
    sys.path.insert(0, src_path)
