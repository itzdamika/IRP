from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
lines = (ROOT / "new.py").read_text(encoding="utf-8").splitlines()
gov = Path(__file__).resolve().parents[1]

(gov / "constants.py").write_text(
    '"""Phases and contract metadata — same as new.py."""\nfrom typing import Dict, List\n\n'
    + "\n".join(lines[209:312]),
    encoding="utf-8",
)

(gov / "prompts.py").write_text(
    '"""GLOBAL_SYSTEM and AGENT_PROMPTS — verbatim from new.py."""\nfrom typing import Dict\n\n'
    + "\n".join(lines[317:702]),
    encoding="utf-8",
)

print("Wrote constants.py and prompts.py")
