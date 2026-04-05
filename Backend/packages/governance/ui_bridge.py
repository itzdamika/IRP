"""Replace Rich console — collect structured UI events for APIs or streaming."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Tuple

EmitHandler = Callable[["GovernanceUIBridge"], None] | None


@dataclass
class GovernanceUIBridge:
    """Append JSON-serializable events; optional on_emit for live HTTP/job streaming."""

    events: List[Dict[str, Any]] = field(default_factory=list)
    on_emit: EmitHandler = None

    def _emit(self) -> None:
        fn = self.on_emit
        if fn is not None:
            fn(self)

    def panel(self, title: str, body: str, color: str = "green") -> None:
        self.events.append({"type": "panel", "title": title, "body": body, "color": color})
        self._emit()

    def thinking(self, agent: str, body: str) -> None:
        self.events.append({"type": "thinking", "agent": agent, "body": body})
        self._emit()

    def rule(self, message: str) -> None:
        self.events.append({"type": "rule", "message": message})
        self._emit()

    def log(self, message: str) -> None:
        self.events.append({"type": "log", "message": message})
        self._emit()

    def status_table(self, title: str, rows: List[Tuple[str, str]]) -> None:
        self.events.append({"type": "status_table", "title": title, "rows": [list(r) for r in rows]})
        self._emit()

    def round_tables(
        self,
        round_no: int,
        plan_rows: List[Tuple[str, str]],
        audit_rows: List[Tuple[str, str]],
    ) -> None:
        self.events.append(
            {
                "type": "round_tables",
                "round": round_no,
                "plan_rows": [list(r) for r in plan_rows],
                "audit_rows": [list(r) for r in audit_rows],
            }
        )
        self._emit()

    def clear(self) -> None:
        self.events.clear()
        self._emit()
