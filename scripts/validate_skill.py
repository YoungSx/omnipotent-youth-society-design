#!/usr/bin/env python3
"""Validates skill/SKILL.md against WorkBuddy Open Platform and Agent Skill standards."""
from pathlib import Path
import re
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skill"
SKILL_MD = SKILL_DIR / "SKILL.md"

REQUIRED_FRONTMATTER_FIELDS = [
    "name",
    "display_name",
    "display_name_en",
    "description",
    "description_zh",
    "description_en",
    "category",
    "version",
    "author",
]


def extract_frontmatter(content: str) -> tuple[dict, str]:
    if not content.startswith("---"):
        raise ValueError("SKILL.md must start with YAML frontmatter delimiters '---'")
    parts = content.split("---", 2)
    if len(parts) < 3:
        raise ValueError("Invalid frontmatter: missing closing '---'")
    frontmatter_raw = parts[1]
    body = parts[2]
    data = yaml.safe_load(frontmatter_raw)
    if not isinstance(data, dict):
        raise ValueError("Frontmatter must parse into a key-value dictionary")
    return data, body


def validate_skill():
    print(f"[*] Validating {SKILL_MD.relative_to(ROOT)}...")
    if not SKILL_MD.exists():
        sys.exit(f"Error: {SKILL_MD} does not exist!")

    content = SKILL_MD.read_text(encoding="utf-8")
    meta, body = extract_frontmatter(content)

    # 1. Frontmatter required fields
    print("[1] Checking WorkBuddy required frontmatter fields...")
    missing = [f for f in REQUIRED_FRONTMATTER_FIELDS if f not in meta or not str(meta[f]).strip()]
    if missing:
        sys.exit(f"Error: Missing required frontmatter fields: {missing}")
    for k in REQUIRED_FRONTMATTER_FIELDS:
        print(f"    ✓ {k}: {meta[k]}")

    # 2. Sub-resource directories
    print("[2] Checking standard sub-resource directories...")
    ref_dir = SKILL_DIR / "references"
    tmpl_dir = SKILL_DIR / "templates"
    if not ref_dir.is_dir():
        sys.exit(f"Error: references/ directory missing at {ref_dir}")
    print(f"    ✓ references/ exists ({len(list(ref_dir.glob('*')))} files)")

    if tmpl_dir.is_dir():
        print(f"    ✓ templates/ exists ({len(list(tmpl_dir.glob('*')))} files)")

    # 3. Check @references/ citations in body
    print("[3] Checking '@references/' citations in SKILL.md...")
    ref_mentions = re.findall(r"@references/([A-Za-z0-9_\-\.]+)", body)
    if not ref_mentions:
        print("    ⚠️ Warning: No '@references/' found in body.")
    else:
        for ref in set(ref_mentions):
            target = ref_dir / ref
            if not target.exists():
                sys.exit(f"Error: Referenced file @references/{ref} does not exist on disk!")
            print(f"    ✓ Valid reference: @references/{ref}")

    # 4. Check @templates/ citations in body
    print("[4] Checking '@templates/' citations in SKILL.md...")
    tmpl_mentions = re.findall(r"@templates/([A-Za-z0-9_\-\.]+)", body)
    if tmpl_mentions and tmpl_dir.is_dir():
        for tmpl in set(tmpl_mentions):
            target = tmpl_dir / tmpl
            if not target.exists():
                sys.exit(f"Error: Referenced template @templates/{tmpl} does not exist on disk!")
            print(f"    ✓ Valid template: @templates/{tmpl}")

    print("\n[SUCCESS] Skill validation passed! Meets WorkBuddy & Agent Skill specifications.")


if __name__ == "__main__":
    validate_skill()
