"""Keep the landing page and its local documentation links complete."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_readme_has_only_six_entry_sections():
    readme = (ROOT / "README.md").read_text()
    assert re.findall(r"^## (.+)$", readme, re.MULTILINE) == ["What", "How", "Where", "When", "Why", "Who"]
    assert not re.search(r"^#{3,} ", readme, re.MULTILINE)


def test_local_documentation_links_exist():
    documents = [ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md"))]
    for document in documents:
        for target in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", document.read_text()):
            if "://" not in target and not target.startswith("#"):
                assert (document.parent / target.split("#", 1)[0]).is_file(), f"{document.name}: {target}"


def test_readme_inlines_multiple_valid_app_captures():
    readme = (ROOT / "README.md").read_text()
    targets = re.findall(r"!\[[^\]]+\]\((docs/screenshots/[^)]+\.png)\)", readme)
    assert len(set(targets)) >= 3
    for target in targets:
        assert (ROOT / target).read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
