"""Pickle SharedState for DB storage (trusted server-side only)."""
from __future__ import annotations

import pickle
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .engine import GovernanceEngine
    from .state import SharedState


def state_to_blob(state: SharedState) -> bytes:
    return pickle.dumps(state, protocol=pickle.HIGHEST_PROTOCOL)


def state_from_blob(blob: bytes) -> SharedState:
    return pickle.loads(blob)


def apply_state(engine: GovernanceEngine, state: SharedState) -> None:
    engine.state = state
