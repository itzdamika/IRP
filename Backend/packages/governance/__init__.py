"""Governance agent package — backend reimplementation of new.py (no Rich / terminal)."""

from .constants import (
    PHASE_APPROVED,
    PHASE_DEVELOPMENT,
    PHASE_PLANNING,
    PHASE_REQUIREMENTS,
)
from .engine import GovernanceEngine
from .runner import dialogue_snapshot, rerun_last_turn, run_handle_turn_only, run_user_turn
from .state import ChatTurn, RequirementField, SharedState
from .ui_bridge import GovernanceUIBridge

__all__ = [
    "GovernanceEngine",
    "GovernanceUIBridge",
    "SharedState",
    "ChatTurn",
    "RequirementField",
    "run_user_turn",
    "run_handle_turn_only",
    "rerun_last_turn",
    "dialogue_snapshot",
    "PHASE_REQUIREMENTS",
    "PHASE_PLANNING",
    "PHASE_APPROVED",
    "PHASE_DEVELOPMENT",
]
