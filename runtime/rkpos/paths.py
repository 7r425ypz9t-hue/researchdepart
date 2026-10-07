from pathlib import Path
import os

ROOT = Path(os.environ.get("RKPOS_ROOT", Path(__file__).resolve().parents[2]))
AGENTS = ROOT / "agents"
SPECS = AGENTS / "_specs"
SCHEMAS = ROOT / "schemas"
WORKFLOWS = ROOT / "workflows"
PROJECTS = ROOT / "projects"
LOGS = ROOT / "logs"
CONFIG = ROOT / "config"
GOVERNANCE = ROOT / "governance"
PROMPTS = ROOT / "prompts"
DOCS = ROOT / "documentation"

TYPE_DIRS = {
    "core": "core",
    "specialist": "specialists",
    "supervisory": "supervisors",
    "utility": "utilities",
    "on_demand": "on-demand",
}
