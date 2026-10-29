"""Rebuilds the installed skill into a Firm Skill: the same files plus firm.json, which carries the firm's name
and the address of its library (see ADR-0004). Setup and Promotion both hand this .skill file back to the bookkeeper."""
import json
import re
import zipfile
from pathlib import Path

SKILL_NAME = "statement-parser"
SKILL_ROOT = Path(__file__).resolve().parent.parent
FIRM_FILE = "firm.json"
ARTIFACT_LINK = re.compile(r"^https://claude\.ai/(artifact/[A-Za-z0-9_-]+|code/artifact/[0-9a-f-]{36})$")


def is_artifact_link(address):
    return bool(ARTIFACT_LINK.match(address))


def firm_config(root=SKILL_ROOT):
    """The firm's name and library link, or None if this skill hasn't been through Setup."""
    path = root / FIRM_FILE
    return json.loads(path.read_text()) if path.exists() else None


def bundled_ids(root=SKILL_ROOT):
    return {p.stem for p in (root / "parsers").glob("*/*.py")}


def write_firm_skill(out, firm, library, version, promote_dir=None):
    """Writes the Firm Skill .skill file; returns (archive, number of Bundled Parsers, ids promoted now)."""
    promoting = sorted(Path(promote_dir).glob("*.py")) if promote_dir else []
    replaced = {f"parsers/promoted/{p.name}" for p in promoting}
    out.mkdir(parents=True, exist_ok=True)
    archive = out / f"{SKILL_NAME}.skill"  # a zip; Claude accepts it as a skill upload
    bundled = 0
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
        for path in sorted(SKILL_ROOT.rglob("*")):
            relative = path.relative_to(SKILL_ROOT).as_posix()
            if path.is_dir() or "__pycache__" in relative or relative == FIRM_FILE or relative in replaced:
                continue
            z.write(path, f"{SKILL_NAME}/{relative}")
            bundled += relative.startswith("parsers/") and relative.endswith(".py")
        for path in promoting:
            z.write(path, f"{SKILL_NAME}/parsers/promoted/{path.name}")
            bundled += 1
        config = {"firm": firm, "library": library, "version": version}
        z.writestr(f"{SKILL_NAME}/{FIRM_FILE}", json.dumps(config, indent=2) + "\n")
    return archive, bundled, [p.stem for p in promoting]
