"""One-off helper: generate engine.py body from ../new.py (repo root new.py)."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
NEW_PY = ROOT / "new.py"
OUT = Path(__file__).resolve().parents[1] / "engine.py"

lines = NEW_PY.read_text(encoding="utf-8").splitlines()
# GovernanceHybridApp: lines 891-3508 (1-based) -> slice [890:3508]
chunk = lines[890:3508]
text = "\n".join(chunk)

text = text.replace("class GovernanceHybridApp:", "class GovernanceEngine:")
text = text.replace(
    """    def __init__(self) -> None:
        self.console = Console()
        self.state = SharedState()
        self.llm = AzureLLM()

        self.state.artifacts_dir = str(Path("artifacts") / self.state.session_id[:8])
        Path(self.state.artifacts_dir).mkdir(parents=True, exist_ok=True)
        Path(self.state.artifacts_dir, "diagrams").mkdir(parents=True, exist_ok=True)""",
    """    def __init__(
        self,
        artifacts_base: Optional[str] = None,
        ui: Optional["GovernanceUIBridge"] = None,
    ) -> None:
        self._ui = ui if ui is not None else GovernanceUIBridge()
        self.state = SharedState()
        self.llm = AzureLLM()

        base = Path(artifacts_base or "artifacts")
        self.state.artifacts_dir = str(base / self.state.session_id[:8])
        Path(self.state.artifacts_dir).mkdir(parents=True, exist_ok=True)
        Path(self.state.artifacts_dir, "diagrams").mkdir(parents=True, exist_ok=True)""",
)

text = text.replace(
    """    def panel(self, title: str, body: str, color: str = "green") -> None:
        self.console.print(Panel(body, title=title, border_style=color))""",
    """    def panel(self, title: str, body: str, color: str = "green") -> None:
        self._ui.panel(title, body, color)""",
)

text = text.replace(
    """    def thinking(self, agent: str, summary: Any, next_action: str = "", confidence: Optional[float] = None) -> None:
        if not self.state.show_internal_panels:
            return
        body = as_text(summary, 2000)
        if confidence is not None:
            body += f"\\n\\n[dim]confidence: {confidence:.2f}[/dim]"
        if next_action:
            body += f"\\n[dim]next: {next_action}[/dim]"
        self.console.print(Panel(body, title=f"[bold yellow]THINKING · {agent}[/bold yellow]", border_style="yellow"))""",
    """    def thinking(self, agent: str, summary: Any, next_action: str = "", confidence: Optional[float] = None) -> None:
        if not self.state.show_internal_panels:
            return
        body = as_text(summary, 2000)
        if confidence is not None:
            body += f"\\n\\nconfidence: {confidence:.2f}"
        if next_action:
            body += f"\\nnext: {next_action}"
        self._ui.thinking(agent, body)""",
)

text = text.replace(
    """    def show_status(self) -> None:
        t = Table(title="Runtime Status", box=box.SIMPLE_HEAVY)
        t.add_column("Field", style="cyan", width=28)
        t.add_column("Value")
        t.add_row("Phase", self.state.phase)
        t.add_row("Active agent", self.state.active_agent)
        t.add_row("Threshold", f"{self.state.pass_threshold:.2f}")
        t.add_row("Pending confirmations", ", ".join(self.state.pending_confirmations) or "None")
        t.add_row("Missing required", ", ".join(self.missing_required_fields()) or "None")
        t.add_row("Planning rounds", str(self.state.max_planning_rounds))
        t.add_row("Known issues", str(len(self.state.issue_ledger)))
        t.add_row("Best score", f"{self.state.best_audit.get('score', 0):.2f}" if self.state.best_audit else "N/A")
        t.add_row("Approved PDF", self.state.final_pdf_path or "None")
        self.console.print(t)""",
    """    def show_status(self) -> None:
        rows = [
            ("Phase", self.state.phase),
            ("Active agent", self.state.active_agent),
            ("Threshold", f"{self.state.pass_threshold:.2f}"),
            ("Pending confirmations", ", ".join(self.state.pending_confirmations) or "None"),
            ("Missing required", ", ".join(self.missing_required_fields()) or "None"),
            ("Planning rounds", str(self.state.max_planning_rounds)),
            ("Known issues", str(len(self.state.issue_ledger))),
            ("Best score", f"{self.state.best_audit.get('score', 0):.2f}" if self.state.best_audit else "N/A"),
            ("Approved PDF", self.state.final_pdf_path or "None"),
        ]
        self._ui.status_table("Runtime Status", rows)""",
)

text = text.replace(
    "        self.console.print(Rule(\"[bold magenta]Internal Planning & Audit Started\"))",
    '        self._ui.rule("Internal Planning & Audit Started")',
)
text = text.replace(
    "                self.console.print(Rule(f\"[bold cyan]Architecture Round {round_no}\"))",
    '                self._ui.rule(f"Architecture Round {round_no}")',
)
text = text.replace(
    "                    self.console.print(Rule(\"[bold green]Plan Approved - Generating Comprehensive Report\"))",
    '                    self._ui.rule("Plan Approved - Generating Comprehensive Report")',
)

text = text.replace(
    """    def show_round_tables(self, round_no: int, plan: Dict[str, Any], audit: Dict[str, Any]) -> None:
        pt = Table(title=f"Architecture Draft Round {round_no}", box=box.SIMPLE_HEAVY)
        pt.add_column("Field", style="cyan", width=22)
        pt.add_column("Value")
        pt.add_row("Title", str(plan.get("title")))
        pt.add_row("Summary", as_text(plan.get("executive_summary"), 320))
        self.console.print(pt)

        at = Table(title=f"Audit Result Round {round_no}", box=box.SIMPLE_HEAVY)
        at.add_column("Metric", style="magenta", width=24)
        at.add_column("Value")
        rubric = audit.get("rubric_scores", {}) or {}
        at.add_row("Requirements", f"{float(rubric.get('requirements_alignment', 0.0)):.2f}")
        at.add_row("Architecture", f"{float(rubric.get('architecture_quality', 0.0)):.2f}")
        at.add_row("Security", f"{float(rubric.get('security', 0.0)):.2f}")
        at.add_row("Operability", f"{float(rubric.get('operability', 0.0)):.2f}")
        at.add_row("Consistency", f"{float(rubric.get('internal_consistency', 0.0)):.2f}")
        at.add_row("Final score", f"{audit['score']:.2f}")
        at.add_row("Passed", str(audit["passed"]))
        at.add_row("Summary", as_text(audit.get("summary"), 320))
        self.console.print(at)""",
    """    def show_round_tables(self, round_no: int, plan: Dict[str, Any], audit: Dict[str, Any]) -> None:
        plan_rows = [
            ("Title", str(plan.get("title"))),
            ("Summary", as_text(plan.get("executive_summary"), 320)),
        ]
        rubric = audit.get("rubric_scores", {}) or {}
        audit_rows = [
            ("Requirements", f"{float(rubric.get('requirements_alignment', 0.0)):.2f}"),
            ("Architecture", f"{float(rubric.get('architecture_quality', 0.0)):.2f}"),
            ("Security", f"{float(rubric.get('security', 0.0)):.2f}"),
            ("Operability", f"{float(rubric.get('operability', 0.0)):.2f}"),
            ("Consistency", f"{float(rubric.get('internal_consistency', 0.0)):.2f}"),
            ("Final score", f"{audit['score']:.2f}"),
            ("Passed", str(audit["passed"])),
            ("Summary", as_text(audit.get("summary"), 320)),
        ]
        self._ui.round_tables(round_no, plan_rows, audit_rows)""",
)

text = text.replace(
    "        self.console.print(Rule(\"[bold cyan]Building Comprehensive Architecture Report\"))",
    '        self._ui.rule("Building Comprehensive Architecture Report")',
)
text = text.replace(
    '        self.console.print("[cyan]Step 1/5: Generating execution plan...[/cyan]")',
    '        self._ui.log("Step 1/5: Generating execution plan...")',
)
text = text.replace(
    '        self.console.print("[cyan]Step 2/5: Generating development playbook...[/cyan]")',
    '        self._ui.log("Step 2/5: Generating development playbook...")',
)
text = text.replace(
    '        self.console.print("[cyan]Step 3/5: Generating QA and testing package...[/cyan]")',
    '        self._ui.log("Step 3/5: Generating QA and testing package...")',
)
text = text.replace(
    '        self.console.print("[cyan]Step 4/5: Generating architecture diagrams...[/cyan]")',
    '        self._ui.log("Step 4/5: Generating architecture diagrams...")',
)
text = text.replace(
    '        self.console.print("[cyan]Step 5/5: Writing comprehensive report sections...[/cyan]")',
    '        self._ui.log("Step 5/5: Writing comprehensive report sections...")',
)
text = text.replace(
    '        self.console.print("[cyan]Building PDF report...[/cyan]")',
    '        self._ui.log("Building PDF report...")',
)
text = text.replace(
    '        self.console.print(f"[green]Report complete: {self.state.final_pdf_path}[/green]")',
    '        self._ui.log(f"Report complete: {self.state.final_pdf_path}")',
)
text = text.replace(
    '            self.console.print(f"  [dim]Writing: {section_title}...[/dim]")',
    '            self._ui.log(f"  Writing: {section_title}...")',
)

text = text.replace(
    """    def banner(self) -> None:
        self.console.print(Rule("[bold cyan]Architectural Governance Terminal"))
        self.console.print("[dim]Type your project idea. Type 'exit' to quit.[/dim]")
        self.console.print(
            "[dim]Commands: :threshold 9.0 | :rounds 10 | :debug on/off | "
            ":thinking on/off | :status | :export[/dim]\\n"
        )""",
    """    def banner(self) -> None:
        self._ui.rule("Architectural Governance Terminal")
        self._ui.log("Type your project idea. Type 'exit' to quit.")
        self._ui.log("Commands: :threshold 9.0 | :rounds 10 | :debug on/off | :thinking on/off | :status | :export")""",
)

header = '''"""
Governance engine — same behavior as new.py GovernanceHybridApp; UI via GovernanceUIBridge.
ArchitectAgent / AuditorAgent prompts live in prompts.py unchanged.
"""
from __future__ import annotations

import json
import re
import textwrap
import traceback
import uuid
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .constants import (
    ALL_AGENTS,
    CONTRACT_TO_NOTE_PATH,
    CORE_REQUIRED_FIELDS,
    FIELD_PROMPTS,
    INTERNAL_PLANNING_FIELDS,
    PHASE_APPROVED,
    PHASE_DEVELOPMENT,
    PHASE_PLANNING,
    PHASE_REQUIREMENTS,
    POST_APPROVAL_AGENTS,
    PROJECT_CLASS_DEFAULT_CAPABILITIES,
    REASONERS,
    SPECIALISTS,
)
from .helpers import (
    as_text,
    compact_json,
    deep_set,
    ensure_list,
    ensure_list_of_str,
    get_diagram_image,
    now_iso,
    safe_json_loads,
    unique_strs,
    write_json,
)
from .llm import AzureLLM
from .prompts import AGENT_PROMPTS, GLOBAL_SYSTEM
from .state import AcceptedException, ChatTurn, RequirementField, SharedState
from .ui_bridge import GovernanceUIBridge

'''

OUT.write_text(header + text, encoding="utf-8")
print("Wrote", OUT, "lines", len(text.splitlines()) + len(header.splitlines()))
