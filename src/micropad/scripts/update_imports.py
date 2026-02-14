#!/usr/bin/env python3
"""Update imports in migrated files."""
import re
from pathlib import Path

# Import mapping: old -> new
IMPORT_MAP = {
    "from logging_manager import": "from micropad.logging.manager import",
    "from repository_parser import": "from micropad.repository.parser import",
    "from repository_graph import": "from micropad.repository.graph import",
    "from pattern_analyzer import": "from micropad.analysis.pattern_analyzer import",
    "from report_generator import": "from micropad.reporting.generator import",
    "from evaluation_metrics import": "from micropad.data.metrics import",
    "from cost_tracking import": "from micropad.core.cost_tracking import",
    "from detection_logging import": "from micropad.logging.detection import",
    "from ui_output import": "from micropad.logging.ui import",
    "from ai_agent import": "from micropad.llm.agent import",
    "from llm_client import": "from micropad.llm.client import",
    "from llm_helper import": "from micropad.llm.helpers import",
    "from prompt_builder import": "from micropad.llm.prompts import",
    "from code_parsers import": "from micropad.repository.code_parsers import",
    "import config": "from micropad.config import settings as config",
}


def update_file(file_path: Path):
    """Update imports in a single file."""
    try:
        content = file_path.read_text(encoding="utf-8")
        original = content

        for old, new in IMPORT_MAP.items():
            content = content.replace(old, new)

        if content != original:
            file_path.write_text(content, encoding="utf-8")
            print(f"✓ Updated: {file_path}")
            return True
        return False
    except Exception as e:
        print(f"✗ Error in {file_path}: {e}")
        return False


def main():
    """Update all Python files in micropad package."""
    micropad_dir = Path("micropad")
    updated = 0

    for py_file in micropad_dir.rglob("*.py"):
        if py_file.name != "__init__.py":
            if update_file(py_file):
                updated += 1

    print(f"\n✅ Updated {updated} files")


if __name__ == "__main__":
    main()
