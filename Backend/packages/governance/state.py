"""Session state dataclasses — same fields as new.py SharedState."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .constants import FIELD_PROMPTS, PHASE_REQUIREMENTS
from .helpers import now_iso


@dataclass
class RequirementField:
    value: str = ""
    source: str = ""
    confirmed: bool = False
    rationale: str = ""
    updated_at: str = ""


@dataclass
class AcceptedException:
    issue_id: str
    reason: str
    user_message: str
    created_at: str = field(default_factory=now_iso)


@dataclass
class ChatTurn:
    role: str
    content: str
    agent: Optional[str] = None
    timestamp: str = field(default_factory=now_iso)
    extra: Optional[Dict[str, Any]] = None


@dataclass
class SharedState:
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    phase: str = PHASE_REQUIREMENTS
    active_agent: str = "RequirementCoordinator"

    dialogue: List[ChatTurn] = field(default_factory=list)
    context_summary: str = ""

    requirement_contract: Dict[str, RequirementField] = field(
        default_factory=lambda: {key: RequirementField() for key in FIELD_PROMPTS.keys()}
    )
    pending_confirmations: List[str] = field(default_factory=list)

    requirements: Dict[str, Any] = field(
        default_factory=lambda: {
            "project": {},
            "frontend": {},
            "backend": {},
            "security": {},
            "data": {},
            "devops": {},
            "constraints": {},
            "open_questions": {},
            "confirmed_decisions": {},
        }
    )

    requirement_status: Dict[str, Any] = field(
        default_factory=lambda: {
            "ready_for_planning": False,
            "completeness_score": 0.0,
            "summary": "",
            "last_updated": None,
        }
    )
    last_requested_fields: List[str] = field(default_factory=list)
    fields_asked_this_session: List[str] = field(default_factory=list)
    planning_confirmation_requested: bool = False

    pass_threshold: float = 9.0
    max_requirement_hops: int = 12
    max_tool_rounds: int = 10
    max_planning_rounds: int = 10
    debug_mode: bool = False
    show_internal_panels: bool = True
    report_depth: str = "extreme"

    issue_ledger: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    revision_memory: Dict[str, Any] = field(default_factory=dict)
    accepted_exceptions: Dict[str, AcceptedException] = field(default_factory=dict)

    specialist_history: List[Dict[str, Any]] = field(default_factory=list)
    audit_history: List[Dict[str, Any]] = field(default_factory=list)

    current_plan: Dict[str, Any] = field(default_factory=dict)
    best_plan: Dict[str, Any] = field(default_factory=dict)
    current_audit: Dict[str, Any] = field(default_factory=dict)
    best_audit: Dict[str, Any] = field(default_factory=dict)

    report_package: Dict[str, Any] = field(default_factory=dict)
    development_package: Dict[str, Any] = field(default_factory=dict)
    final_pdf_path: str = ""
    artifacts_dir: str = ""

    internal_busy: bool = False
    shutdown: bool = False

    focus_issues: List[Dict[str, Any]] = field(default_factory=list)
    convergence_state: Dict[str, Any] = field(default_factory=dict)
    finalization_reason: str = ""

    generated_diagrams: Dict[str, str] = field(default_factory=dict)
