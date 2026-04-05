"""Shared helpers — same implementations as new.py."""
from __future__ import annotations

import base64
import json
import re
import textwrap
import urllib.parse
import urllib.request
import zlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_json_loads(text: str) -> Dict[str, Any]:
    if not text:
        return {}
    try:
        return json.loads(text)
    except Exception:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except Exception:
            return {}
    return {}


def as_text(value: Any, limit: int = 200000) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        s = value
    else:
        try:
            s = json.dumps(value, indent=2, ensure_ascii=False)
        except Exception:
            s = str(value)
    return s if len(s) <= limit else s[:limit] + "\n...<truncated>..."


def compact_json(obj: Any, limit: int = 12000) -> str:
    try:
        s = json.dumps(obj, ensure_ascii=False, indent=2)
    except Exception:
        s = str(obj)
    return s[:limit]


def ensure_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def ensure_list_of_str(value: Any) -> List[str]:
    out: List[str] = []
    seen = set()
    for item in ensure_list(value):
        s = str(item).strip()
        if s and s not in seen:
            out.append(s)
            seen.add(s)
    return out


def unique_strs(items: List[Any]) -> List[str]:
    out: List[str] = []
    seen = set()
    for item in items:
        s = str(item).strip()
        if s and s not in seen:
            seen.add(s)
            out.append(s)
    return out


def deep_set(d: Dict[str, Any], path: str, value: Any) -> None:
    keys = path.split(".")
    cur = d
    for k in keys[:-1]:
        if k not in cur or not isinstance(cur[k], dict):
            cur[k] = {}
        cur = cur[k]
    cur[keys[-1]] = value


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def render_mermaid_to_image(mermaid_code: str, output_path: Path, timeout: int = 20) -> bool:
    try:
        b64 = base64.urlsafe_b64encode(mermaid_code.encode("utf-8")).decode("utf-8")
        url = f"https://mermaid.ink/img/{b64}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
        if data and len(data) > 500:
            output_path.write_bytes(data)
            return True
        return False
    except Exception:
        return False


def render_mermaid_via_kroki(mermaid_code: str, output_path: Path, timeout: int = 20) -> bool:
    try:
        compressed = zlib.compress(mermaid_code.encode("utf-8"), 9)
        b64 = base64.urlsafe_b64encode(compressed).decode("utf-8")
        url = f"https://kroki.io/mermaid/png/{b64}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
        if data and len(data) > 500:
            output_path.write_bytes(data)
            return True
        return False
    except Exception:
        return False


def get_diagram_image(mermaid_code: str, output_path: Path) -> Optional[Path]:
    if render_mermaid_via_kroki(mermaid_code, output_path):
        return output_path
    if render_mermaid_to_image(mermaid_code, output_path):
        return output_path
    return None
