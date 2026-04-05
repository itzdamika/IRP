"""High-level entrypoints for HTTP services — wraps GovernanceEngine turns."""
from __future__ import annotations

import logging
from dataclasses import asdict
from typing import Any, Dict, List

from .constants import (
    PHASE_APPROVED,
    PHASE_DEVELOPMENT,
    PHASE_PLANNING,
    PHASE_REQUIREMENTS,
)
from .engine import GovernanceEngine
from .state import ChatTurn


def dialogue_snapshot(dialogue: List[ChatTurn]) -> List[Dict[str, Any]]:
    return [asdict(t) for t in dialogue]


def _attach_assistant_turn_meta(engine: GovernanceEngine, user_message_index: int) -> bool:
    """Persist UI transcript + client hints on the last assistant reply for this user turn."""
    events = list(engine._ui.events)
    segment = engine.state.dialogue[user_message_index:]
    has_planning_rounds = any(
        isinstance(e, dict) and e.get("type") == "round_tables" for e in events
    )

    def _ev_planningish(ev: object) -> bool:
        return isinstance(ev, dict) and ev.get("type") in (
            "round_tables",
            "thinking",
            "rule",
            "log",
            "panel",
            "status_table",
        )

    planningish = events and any(_ev_planningish(e) for e in events)
    planning_transcript = bool(
        events
        and (
            has_planning_rounds
            or (
                engine.state.phase
                in (PHASE_PLANNING, PHASE_DEVELOPMENT, PHASE_APPROVED)
                and planningish
                and len(events) >= 1
            )
            or (len(events) >= 3 and planningish)
        )
    )
    suggest_next = False
    for turn in reversed(segment):
        if turn.role != "assistant":
            continue
        ex = dict(getattr(turn, "extra", None) or {})
        if planning_transcript:
            serial: list[Any] = []
            for e in events:
                serial.append(dict(e) if isinstance(e, dict) else e)
            ex["planning_ui_events"] = serial
        ast = (turn.content or "").strip()
        if ast:
            suggest_next = engine.assistant_message_offers_planning_handoff(ast)
        ex["suggest_stream_planning_next"] = suggest_next
        # Explicit client hint: only True when engine is waiting for "yes" to start planning.
        # (Avoids false positives from suggest_next alone on routine requirement replies.)
        ex["planning_confirmation_prompt"] = bool(
            suggest_next
            and engine.state.phase == PHASE_REQUIREMENTS
            and getattr(engine.state, "planning_confirmation_requested", False)
        )
        turn.extra = ex
        break
    # Background WebSocket streaming only during PLANNING — not on requirement follow-ups
    # (handoff suggestion alone would run a job with no UI events until the turn ends).
    return engine.state.phase == PHASE_PLANNING


def run_handle_turn_only(engine: GovernanceEngine, user_text: str) -> Dict[str, Any]:
    """
    Call handle_turn only (user message must already be last in dialogue).
    Same return shape as run_user_turn.
    """
    engine._ui.clear()
    engine.maybe_compact_context()
    err: str | None = None
    try:
        engine.handle_turn(user_text.strip())
    except Exception as e:
        logging.exception("run_handle_turn_only")
        err = str(e)
    ui = len(engine.state.dialogue) - 1
    while ui >= 0 and engine.state.dialogue[ui].role != "user":
        ui -= 1
    stream_live = False
    if ui >= 0:
        stream_live = _attach_assistant_turn_meta(engine, ui)
    events = list(engine._ui.events)
    return {
        "session_id": engine.state.session_id,
        "phase": engine.state.phase,
        "active_agent": engine.state.active_agent,
        "dialogue": dialogue_snapshot(engine.state.dialogue),
        "ui_events": events,
        "final_pdf_path": engine.state.final_pdf_path,
        "report_package": engine.state.report_package,
        "quick_replies": suggest_quick_replies(engine),
        "stream_planning_live": stream_live,
        "error": err,
    }


def run_user_turn(engine: GovernanceEngine, user_text: str) -> Dict[str, Any]:
    """
    Append the user message, run the same pipeline as the terminal (handle_turn),
    return phase, full dialogue, UI events from this turn, and optional error.
    """
    engine._ui.clear()
    before = len(engine.state.dialogue)
    engine.append_dialogue("user", user_text.strip())
    engine.maybe_compact_context()
    err: str | None = None
    try:
        engine.handle_turn(user_text.strip())
    except Exception as e:
        logging.exception("run_user_turn")
        err = str(e)
    stream_live = _attach_assistant_turn_meta(engine, before)
    events = list(engine._ui.events)
    return {
        "session_id": engine.state.session_id,
        "phase": engine.state.phase,
        "active_agent": engine.state.active_agent,
        "dialogue": dialogue_snapshot(engine.state.dialogue),
        "ui_events": events,
        "final_pdf_path": engine.state.final_pdf_path,
        "report_package": engine.state.report_package,
        "quick_replies": suggest_quick_replies(engine),
        "stream_planning_live": stream_live,
        "error": err,
    }


def rerun_last_turn(engine: GovernanceEngine) -> Dict[str, Any]:
    """
    Remove the last assistant message and re-run handle_turn with the previous user message
    (no duplicate user row).
    """
    d = engine.state.dialogue
    if not d:
        return {"error": "empty_dialogue"}
    if d[-1].role != "assistant":
        return {"error": "last_turn_not_assistant"}
    user_text = ""
    for t in reversed(d[:-1]):
        if t.role == "user":
            user_text = (t.content or "").strip()
            break
    if not user_text:
        return {"error": "no_prior_user_message"}
    d.pop()
    engine._ui.clear()
    engine.maybe_compact_context()
    err: str | None = None
    try:
        engine.handle_turn(user_text)
    except Exception as e:
        logging.exception("rerun_last_turn")
        err = str(e)
    ui = len(d) - 1
    while ui >= 0 and d[ui].role != "user":
        ui -= 1
    stream_live = False
    if ui >= 0:
        stream_live = _attach_assistant_turn_meta(engine, ui)
    events = list(engine._ui.events)
    return {
        "session_id": engine.state.session_id,
        "phase": engine.state.phase,
        "active_agent": engine.state.active_agent,
        "dialogue": dialogue_snapshot(engine.state.dialogue),
        "ui_events": events,
        "final_pdf_path": engine.state.final_pdf_path,
        "report_package": engine.state.report_package,
        "quick_replies": suggest_quick_replies(engine),
        "stream_planning_live": stream_live,
        "error": err,
    }


def suggest_quick_replies(engine: GovernanceEngine) -> List[Dict[str, Any]]:
    """After a turn in REQUIREMENTS, suggest chips (yes/no, etc.) from last assistant text."""
    from .constants import PHASE_REQUIREMENTS

    if engine.state.phase != PHASE_REQUIREMENTS:
        return []
    last = ""
    for t in reversed(engine.state.dialogue):
        if t.role == "assistant":
            c = (t.content or "").strip()
            if c:
                last = c
            break
    if not last or len(last) < 8:
        return []
    prompt = """
You help a chat UI show quick-reply buttons after the assistant's last message.
Return ONLY valid JSON:
{ "replies": [ { "id": "string", "label": "short label", "value": "text sent as user message", "kind": "boolean_yes_no" | "choice" | "text_suggestion" } ] }

Rules:
- If the assistant asked a yes/no question, return exactly two replies: Yes and No (kind boolean_yes_no).
- If the assistant offered clear options, mirror them (kind choice).
- Otherwise return [] or 1-3 helpful text_suggestion chips (short).
- Max 6 replies total.
- Labels must be under 40 characters.
"""
    try:
        raw = engine.ai_json(
            prompt,
            {"last_assistant_message": last[:4000], "phase": engine.state.phase},
            max_tokens=350,
        )
        out = []
        for item in raw.get("replies") or []:
            if not isinstance(item, dict):
                continue
            rid = str(item.get("id") or "").strip() or f"q{len(out)}"
            label = str(item.get("label") or "").strip()
            val = str(item.get("value") or label).strip()
            kind = str(item.get("kind") or "choice").strip()
            if label and val:
                out.append({"id": rid, "label": label, "value": val, "kind": kind})
        return out[:6]
    except Exception:
        return []
