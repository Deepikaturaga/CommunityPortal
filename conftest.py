"""Root conftest — add src/ to sys.path so tests can import archpilot.*."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
