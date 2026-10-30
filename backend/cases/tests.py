"""Keep `manage.py test cases` compatible with the centralized test directory."""
from pathlib import Path


def load_tests(loader, suite, pattern):
    root = Path(__file__).resolve().parents[1]
    if not (root / 'tests' / 'backend').exists():
        root = root.parent
    return loader.discover(str(root / 'tests' / 'backend'), pattern=pattern or 'test*.py', top_level_dir=str(root))
