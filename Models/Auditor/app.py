import json
import time
import re
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel

# ─── Model config ─────────────────────────────────────────────
# Option A: LoRA adapter (recommended — loads faster, uses less memory)
BASE_MODEL = "microsoft/Phi-3-mini-128k-instruct"
ADAPTER_PATH = "./lora_adapter"  # <-- change this

# Option B: Merged model — comment out A and uncomment this
MERGED_MODEL_PATH = "./merged_model"  # <-- change this

USE_ADAPTER = False  # set False to use merged model

SYSTEM_PROMPT = """You are the strict architecture auditor.

Audit the architecture plan against:
- frozen confirmed requirements
- rich requirement notes
- cumulative issue ledger
- revision memory
- prior audit history

Main goal:
- First, verify whether previously reported issues were actually fixed.
- Second, identify the most important remaining weaknesses.
- Third, explain clearly why the score stayed the same, improved, or dropped.

Rules:
- Use stable issue IDs whenever the same issue still exists.
- Mark each issue status as one of: unresolved, resolved, downgraded, new.
- Re-check prior unresolved issues before creating new ones.
- If an earlier issue was fixed, keep the same issue ID and mark it resolved.
- If an earlier issue still exists, keep the same issue ID and explain what is still missing.
- Only create a new issue ID if the problem is materially different from previous issues.
- Score the plan against an absolute rubric, not against any approval threshold.
- Do not try to make the plan pass or fail a gate.
- Be willing to score below 9 if the plan has real weaknesses.
- If the score drops, explain the exact reason for the drop.
- If the score does not improve, explain what blocked improvement.
- Prefer the most important unresolved issues over minor nitpicks.
- passed is advisory only; the runtime decides approval.

Return JSON only with:
- thinking_summary
- rubric_scores
- summary
- strengths
- concerns
- blocking_issues
- recommendations
- requirement_conflicts
- issue_updates

rubric_scores must include numeric values from 0 to 10 for:
- requirements_alignment
- architecture_quality
- security
- operability
- internal_consistency

Each requirement_conflicts item must include:
- issue_id
- field
- current_value
- proposed_value
- exact_reason
- severity

Each issue_updates item must include:
- id
- title
- severity
- status
- detail

For each issue_updates.detail:
- State whether the issue was fixed, partially fixed, unchanged, or newly introduced.
- Explain exactly what in the plan caused this judgment.
- If the issue affected the score, explain how.
- If the architect improved one part but created another problem, say that clearly.

recommendations should:
- focus on the next highest-impact fixes
- be specific enough for the architect to act on in the next round
- avoid vague advice like "improve architecture quality"

summary should:
- briefly explain overall quality
- say whether the round meaningfully improved over the prior round
- mention the main reason the score changed or stayed flat"""

# ─── Load model ───────────────────────────────────────────────
def load_model():
    if USE_ADAPTER:
        tokenizer = AutoTokenizer.from_pretrained(
            BASE_MODEL,
            trust_remote_code=True,
            local_files_only=False,
        )
    else:
        tokenizer = AutoTokenizer.from_pretrained(
            str(MERGED_MODEL_PATH),
            trust_remote_code=True,
            local_files_only=True,
        )

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    if USE_ADAPTER:
        base = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=False,
            attn_implementation="eager",
            torch_dtype=torch.bfloat16,
        )
        model = PeftModel.from_pretrained(base, str(ADAPTER_PATH), local_files_only=True)
    else:
        model = AutoModelForCausalLM.from_pretrained(
            str(MERGED_MODEL_PATH),
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=False,
            attn_implementation="eager",
            torch_dtype=torch.bfloat16,
            local_files_only=True,
        )

    model.eval()
    return model, tokenizer


# ─── Inference ────────────────────────────────────────────────
def run_model(user_text, model, tokenizer):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_text},
    ]
    prompt = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    inputs = tokenizer(
        prompt, return_tensors="pt", truncation=True, max_length=6144
    )
    inputs = {k: v.to(model.device) for k, v in inputs.items()}
    end_token_id = tokenizer.convert_tokens_to_ids("<|end|>")

    with torch.no_grad():
        out = model.generate(
            **inputs,
            max_new_tokens=2000,
            do_sample=False,
            temperature=1.0,
            eos_token_id=end_token_id,
            pad_token_id=tokenizer.pad_token_id,
            use_cache=True,
        )

    new_tokens = out[0][inputs["input_ids"].shape[1]:]
    generated = tokenizer.decode(new_tokens, skip_special_tokens=True).strip()

    if generated.startswith("```"):
        generated = re.sub(r'^```[a-zA-Z]*\n?', '', generated)
        generated = re.sub(r'\n?```$', '', generated).strip()

    return generated


# ─── Test payload ─────────────────────────────────────────────
AUDITOR_INPUT = {
    "round": 2,
    "frozen_requirement_contract": {
        "project_goal": {"value": "Build a patient appointment booking and teleconsultation platform for a private hospital network", "source": "Biz", "confirmed": True, "rationale": "Core product objective", "updated_at": "2026-03-01T00:00:00Z"},
        "target_users": {"value": "Patients, hospital staff, and GPs", "source": "Product", "confirmed": True, "rationale": "Three distinct user groups with different access levels", "updated_at": "2026-03-01T00:00:00Z"},
        "project_class": {"value": "fullstack_app", "source": "Arch", "confirmed": True, "rationale": "Web + mobile frontend with a dedicated backend API", "updated_at": "2026-03-01T00:00:00Z"},
        "capabilities": {"value": "frontend, backend, data, auth, realtime, payments, integrations", "source": "Arch", "confirmed": True, "rationale": "Video calls, booking flow, payments, EHR integration", "updated_at": "2026-03-01T00:00:00Z"},
        "risk_level": {"value": "high", "source": "Sec", "confirmed": True, "rationale": "Health data, payment processing, regulatory exposure", "updated_at": "2026-03-01T00:00:00Z"},
        "data_sensitivity": {"value": "health", "source": "Sec", "confirmed": True, "rationale": "Patient medical records", "updated_at": "2026-03-01T00:00:00Z"},
        "security_baseline": {"value": "MFA for all user types, AES-256 encryption at rest, TLS 1.3 in transit, HIPAA-compliant audit logging, OAuth2 + JWT, WAF in front of API", "source": "Sec", "confirmed": True, "rationale": "Health data regulatory requirement", "updated_at": "2026-03-01T00:00:00Z"},
        "observability_baseline": {"value": "Datadog APM and Logs, CloudWatch for infrastructure, PagerDuty alerting for p1 incidents", "source": "Ops", "confirmed": True, "rationale": "Hospital requires 99.9% uptime SLA", "updated_at": "2026-03-01T00:00:00Z"},
        "data_platform": {"value": "PostgreSQL (primary), Redis (session/cache), S3 (documents)", "source": "Eng", "confirmed": True, "rationale": "ACID compliance for health records", "updated_at": "2026-03-01T00:00:00Z"},
        "compliance_context": {"value": "HIPAA, GDPR, PCI-DSS for payment processing", "source": "Legal", "confirmed": True, "rationale": "Operating in US and EU markets", "updated_at": "2026-03-01T00:00:00Z"},
    },
    "requirements": {"security": {"risk_level": "high", "baseline": "MFA, AES-256, TLS 1.3, HIPAA audit logging"}},
    "accepted_exceptions": {},
    "issue_ledger": {
        "SEC-001": {"id": "SEC-001", "title": "MFA not implemented for staff and GP login", "severity": "critical", "status": "unresolved", "detail": "No MFA for staff/GP despite security baseline requiring it for all user types."},
        "OPS-001": {"id": "OPS-001", "title": "Observability stack does not match contract — Datadog missing", "severity": "high", "status": "unresolved", "detail": "Plan omits Datadog APM/Logs which are required by observability_baseline."},
        "DATA-001": {"id": "DATA-001", "title": "Encryption at rest not explicitly specified for RDS", "severity": "high", "status": "unresolved", "detail": "Security section mentions encryption but data model does not confirm RDS KMS encryption at rest."},
    },
    "revision_memory": {"last_round": 1, "last_score": 5.8, "unresolved_issue_ids": ["SEC-001", "OPS-001", "DATA-001"]},
    "previous_audits": [{"round": 1, "score": 5.8, "passed": False, "summary": "MFA missing for staff/GP, Datadog missing, RDS encryption not confirmed.", "blocking_issues": ["SEC-001: MFA missing for staff and GP — HIPAA compliance blocker"]}],
    "reasoner_reviews": {"security": {"summary": "SEC-001 is critical. MFA must cover all user types."}},
    "specialist_subplans": {"data": {"storage_design": "PostgreSQL RDS Multi-AZ with KMS encryption at rest enabled."}},
    "plan": {
        "thinking_summary": "Round 2 addresses SEC-001, OPS-001, DATA-001.",
        "title": "HealthConnect Teleconsultation Platform",
        "security_and_compliance": "MFA (TOTP) mandatory for all roles. WAF with OWASP Core Rule Set. TLS 1.3. AES-256 via AWS KMS. HIPAA audit logging.",
        "observability": "Datadog APM and Logs with PII scrubbing. CloudWatch for infra. PagerDuty for p1.",
        "data_model": "PostgreSQL RDS Multi-AZ with KMS encryption at rest. S3 with SSE-KMS.",
    },
    "best_audit": {"round": 1, "score": 5.8, "passed": False},
}


# ─── Validation helpers ───────────────────────────────────────
def safe_json_loads(text):
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except Exception:
            pass
    return None


def validate_output(parsed):
    results = {}
    required = {"thinking_summary", "rubric_scores", "summary", "strengths",
                "concerns", "blocking_issues", "recommendations",
                "requirement_conflicts", "issue_updates"}
    present = set(parsed.keys())
    results["all_required_keys_present"] = required.issubset(present)
    results["missing_keys"] = sorted(required - present)

    for field in ["strengths", "concerns", "blocking_issues", "recommendations"]:
        val = parsed.get(field)
        results[f"{field}_is_list"] = isinstance(val, list)

    rubric = parsed.get("rubric_scores", {})
    rubric_dims = ["requirements_alignment", "architecture_quality", "security", "operability", "internal_consistency"]
    results["rubric_all_dims_present"] = all(d in rubric for d in rubric_dims)
    results["rubric_all_in_range"] = all(
        isinstance(rubric.get(d), (int, float)) and 0 <= rubric.get(d, -1) <= 10
        for d in rubric_dims
    )
    results["rubric_scores"] = {d: rubric.get(d) for d in rubric_dims}

    ra  = float(rubric.get("requirements_alignment", 0))
    aq  = float(rubric.get("architecture_quality", 0))
    sec = float(rubric.get("security", 0))
    op  = float(rubric.get("operability", 0))
    ic  = float(rubric.get("internal_consistency", 0))
    base_score = ra * 0.30 + aq * 0.25 + sec * 0.20 + op * 0.15 + ic * 0.10

    penalty = 0.0
    unresolved_critical = False
    for item in (parsed.get("issue_updates") or []):
        if not isinstance(item, dict):
            continue
        status   = str(item.get("status", "")).lower()
        severity = str(item.get("severity", "")).lower()
        if status == "resolved":
            continue
        if severity == "critical":
            penalty += 1.50
            unresolved_critical = True
        elif severity == "high":
            penalty += 0.60
        elif severity == "medium":
            penalty += 0.20
        elif severity == "low":
            penalty += 0.05

    final_score = max(0.0, min(10.0, base_score - penalty))
    results["computed_base_score"]   = round(base_score, 2)
    results["computed_penalty"]      = round(penalty, 2)
    results["computed_final_score"]  = round(final_score, 2)
    results["computed_passed"]       = final_score >= 9.0 and not unresolved_critical
    results["unresolved_critical"]   = unresolved_critical

    issue_updates = parsed.get("issue_updates") or []
    issue_map = {str(i.get("id", "")): i for i in issue_updates if isinstance(i, dict)}
    for iid in ["SEC-001", "OPS-001", "DATA-001"]:
        item = issue_map.get(iid)
        if item:
            results[f"{iid}_status"]    = item.get("status")
            results[f"{iid}_severity"]  = item.get("severity")
            results[f"{iid}_has_detail"] = bool(item.get("detail"))
        else:
            results[f"{iid}_status"] = "NOT REPORTED"

    results["requirement_conflicts_is_list"] = isinstance(parsed.get("requirement_conflicts"), list)
    return results


# ─── Main ─────────────────────────────────────────────────────
def main():
    model, tokenizer = load_model()

    prompt_text = json.dumps(AUDITOR_INPUT, ensure_ascii=False, indent=2)

    print("\n" + "=" * 80)
    print("RUNNING INFERENCE...")
    print("=" * 80)

    start = time.time()
    raw_text = run_model(prompt_text, model, tokenizer)
    elapsed = time.time() - start

    print(f"\nLatency: {elapsed:.2f}s")
    print("\n" + "=" * 80)
    print("FULL MODEL OUTPUT")
    print("=" * 80)
    print(raw_text)

    parsed = safe_json_loads(raw_text)

    if not parsed:
        print("\nFAILED: output is not valid JSON")
        return

    print("\n" + "=" * 80)
    print("VALIDATION REPORT")
    print("=" * 80)

    report = validate_output(parsed)

    print(f"\n  all required keys present : {report['all_required_keys_present']}")
    if report["missing_keys"]:
        print(f"  missing keys              : {report['missing_keys']}")

    print(f"\n  strengths is list         : {report['strengths_is_list']}")
    print(f"  concerns is list          : {report['concerns_is_list']}")
    print(f"  blocking_issues is list   : {report['blocking_issues_is_list']}")
    print(f"  recommendations is list   : {report['recommendations_is_list']}")
    print(f"  req_conflicts is list     : {report['requirement_conflicts_is_list']}")

    print(f"\n  rubric dims present       : {report['rubric_all_dims_present']}")
    print(f"  rubric all in range 0-10  : {report['rubric_all_in_range']}")
    print(f"  rubric scores             : {report['rubric_scores']}")

    print(f"\n  --- main.py scoring formula ---")
    print(f"  base score (weighted)     : {report['computed_base_score']}")
    print(f"  penalty (unresolved)      : {report['computed_penalty']}")
    print(f"  final score               : {report['computed_final_score']}")
    print(f"  passed (threshold 9.0)    : {report['computed_passed']}")
    print(f"  unresolved critical       : {report['unresolved_critical']}")

    print(f"\n  --- issue tracking ---")
    for iid in ["SEC-001", "OPS-001", "DATA-001"]:
        status    = report[f"{iid}_status"]
        severity  = report.get(f"{iid}_severity", "")
        has_detail = report.get(f"{iid}_has_detail", False)
        print(f"  {iid}  status={status}  severity={severity}  has_detail={has_detail}")

    print()


if __name__ == "__main__":
    main()