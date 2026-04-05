"""Generate short thread titles from conversation (optional LLM)."""
from __future__ import annotations

from sqlalchemy.orm import Session

from ..db.models import Message, Thread


def _conversation_excerpt(
    db: Session, thread_id: str, branch_id: str, max_messages: int = 14
) -> str:
    msgs = (
        db.query(Message)
        .filter(Message.thread_id == thread_id, Message.branch_id == branch_id)
        .order_by(Message.created_at.asc())
        .limit(max_messages)
        .all()
    )
    lines: list[str] = []
    for m in msgs:
        role = (m.role or "").upper()
        content = (m.content or "").strip().replace("\n", " ")
        if not content:
            continue
        if len(content) > 420:
            content = content[:417] + "…"
        lines.append(f"{role}: {content}")
    return "\n".join(lines)


def suggest_title_for_thread(db: Session, thread: Thread) -> str:
    bid = thread.active_branch_id
    excerpt = _conversation_excerpt(db, thread.id, bid)
    if not excerpt.strip():
        return thread.title
    try:
        from governance.llm import AzureLLM

        llm = AzureLLM()
        raw = llm.complete_text(
            "Name this software architecture chat in 3–7 words. Title Case. "
            "No quotes, no trailing punctuation, no emojis. Be specific to the product or domain.",
            f"Conversation excerpt:\n{excerpt[:8000]}",
            max_tokens=48,
            temperature=0.35,
        )
        line = (raw or "").strip().split("\n")[0].strip().strip('"').strip("'")
        if line and len(line) >= 3:
            return line[:120]
    except Exception:
        pass
    first = excerpt.split("\n", 1)[0]
    if first.upper().startswith("USER:"):
        u = first[5:].strip()
        if len(u) <= 56:
            return u or thread.title
        return u[:53].rstrip() + "…"
    return thread.title
