import streamlit as st
import json
import csv
import os
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

st.set_page_config(page_title="Human Evaluation App", layout="wide")

# ----------------------------
# Paths
# ----------------------------
DATA_DIR = Path("data")
RESPONSES_DIR = Path("responses")
RESPONSES_DIR.mkdir(parents=True, exist_ok=True)

# ----------------------------
# Helpers
# ----------------------------
def safe_get(d: Any, path: List[str], default=None):
    cur = d
    for p in path:
        if not isinstance(cur, dict) or p not in cur:
            return default
        cur = cur[p]
    return cur

def first_nonempty(d: Dict[str, Any], keys: List[str], default=None):
    for k in keys:
        if k in d and d[k] not in [None, "", [], {}]:
            return d[k]
    return default

def normalize_text_field(d: Dict[str, Any], canonical: str, aliases: List[str]):
    value = first_nonempty(d, [canonical] + aliases)
    if value is not None:
        d[canonical] = value
    return d

def normalize_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        return [value] if value.strip() else []
    return [str(value)]

def normalize_dict(value):
    return value if isinstance(value, dict) else {}

def parse_json_maybe(raw: Any) -> Dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except Exception:
            return {}
    return {}

def prettify_json(obj: Any) -> str:
    try:
        return json.dumps(obj, indent=2, ensure_ascii=False)
    except Exception:
        return str(obj)

def infer_role(sample: Dict[str, Any]) -> str:
    sid = str(sample.get("sample_id", ""))
    if sid.startswith("AUD-"):
        return "auditor"
    if sid.startswith("ARC-"):
        return "architect"
    payload = sample.get("input_payload", {})
    if "plan" in payload:
        return "auditor"
    if "previous_plan" in payload or "best_plan" in payload:
        return "architect"
    return "unknown"

def normalize_section_object(obj: Dict[str, Any], role: str) -> Dict[str, Any]:
    if not isinstance(obj, dict):
        obj = {}

    alias_map = {
        "thinking_summary": ["thinkingsummary"],
        "fix_report": ["fixreport"],
        "executive_summary": ["executivesummary"],
        "architecture_overview": ["architectureoverview"],
        "technology_stack": ["technologystack"],
        "functional_feature_map": ["functionalfeaturemap"],
        "system_components": ["systemcomponents"],
        "api_design": ["apidesign"],
        "security_and_compliance": ["securityandcompliance"],
        "deployment_and_operations": ["deploymentandoperations"],
        "cost_and_scaling": ["costandscaling"],
        "phased_implementation": ["phasedimplementation"],
        "development_guidelines": ["developmentguidelines"],
        "risks_and_tradeoffs": ["risksandtradeoffs"],
        "open_questions_resolved": ["openquestionsresolved"],
        "issue_updates": ["issueupdates"],
        "requirement_conflicts": ["requirementconflicts"],
        "rubric_scores": ["rubricscores"],
    }

    for canonical, aliases in alias_map.items():
        normalize_text_field(obj, canonical, aliases)

    obj["strengths"] = normalize_list(first_nonempty(obj, ["strengths"]))
    obj["concerns"] = normalize_list(first_nonempty(obj, ["concerns"]))
    obj["blocking_issues"] = normalize_list(first_nonempty(obj, ["blocking_issues"]))
    obj["recommendations"] = normalize_list(first_nonempty(obj, ["recommendations"]))
    obj["issue_updates"] = normalize_list(first_nonempty(obj, ["issue_updates"]))
    obj["requirement_conflicts"] = normalize_list(first_nonempty(obj, ["requirement_conflicts"]))
    obj["fix_report"] = normalize_list(first_nonempty(obj, ["fix_report"]))
    obj["rubric_scores"] = normalize_dict(first_nonempty(obj, ["rubric_scores"], {}))

    return obj

def normalize_plan_object(plan: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(plan, dict):
        return {}
    alias_map = {
        "thinking_summary": ["thinkingsummary"],
        "fix_report": ["fixreport"],
        "executive_summary": ["executivesummary"],
        "architecture_overview": ["architectureoverview"],
        "technology_stack": ["technologystack"],
        "functional_feature_map": ["functionalfeaturemap"],
        "system_components": ["systemcomponents"],
        "api_design": ["apidesign"],
        "security_and_compliance": ["securityandcompliance"],
        "deployment_and_operations": ["deploymentandoperations"],
        "cost_and_scaling": ["costandscaling"],
        "phased_implementation": ["phasedimplementation"],
        "development_guidelines": ["developmentguidelines"],
        "risks_and_tradeoffs": ["risksandtradeoffs"],
        "open_questions_resolved": ["openquestionsresolved"],
        "generated_at": ["generatedat"],
    }
    for canonical, aliases in alias_map.items():
        normalize_text_field(plan, canonical, aliases)

    plan["fix_report"] = normalize_list(first_nonempty(plan, ["fix_report"]))
    return plan

def normalize_sample(raw: Dict[str, Any]) -> Dict[str, Any]:
    sample = dict(raw)
    sample["role"] = infer_role(sample)

    sample["sample_id"] = sample.get("sample_id", "")
    sample["case_type"] = sample.get("case_type")
    sample["input_payload"] = sample.get("input_payload", {}) or {}
    sample["predicted_raw_text"] = sample.get("predicted_raw_text", "")
    sample["predicted_parsed"] = normalize_section_object(parse_json_maybe(sample.get("predicted_parsed")), sample["role"])
    sample["actual_output"] = normalize_section_object(parse_json_maybe(sample.get("actual_output")), sample["role"])
    sample["json_valid"] = sample.get("json_valid", False)
    sample["model_name"] = sample.get("model_name", "")
    sample["adapter_path"] = sample.get("adapter_path", "")
    sample["seed"] = sample.get("seed", None)

    if sample["role"] == "auditor":
        plan = safe_get(sample, ["input_payload", "plan"], {})
        sample["normalized_plan"] = normalize_plan_object(plan)
    else:
        sample["normalized_plan"] = {}

    return sample

def load_jsonl(uploaded_file) -> List[Dict[str, Any]]:
    rows = []
    for line in uploaded_file.getvalue().decode("utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(normalize_sample(json.loads(line)))
        except Exception:
            pass
    return rows

def list_to_bullets(items: List[Any]) -> str:
    if not items:
        return "—"
    cleaned = []
    for item in items:
        if isinstance(item, dict):
            cleaned.append(prettify_json(item))
        else:
            cleaned.append(str(item))
    return "\n".join([f"- {x}" for x in cleaned])

def get_role_rubric(role: str) -> List[str]:
    if role == "auditor":
        return [
            "requirements_alignment",
            "architecture_quality",
            "security",
            "operability",
            "internal_consistency",
        ]
    if role == "architect":
        return [
            "contract_alignment",
            "fix_report_accuracy",
            "architecture_quality",
            "security_coverage",
            "plan_completeness",
        ]
    return [
        "quality",
        "correctness",
        "completeness",
        "clarity",
        "usefulness",
    ]

def default_human_scores(role: str) -> Dict[str, int]:
    return {k: 5 for k in get_role_rubric(role)}

def build_sample_hash(sample: Dict[str, Any]) -> str:
    base = f"{sample.get('sample_id','')}|{sample.get('model_name','')}|{sample.get('seed','')}"
    return hashlib.md5(base.encode()).hexdigest()

def response_csv_path(rater_id: str) -> Path:
    return RESPONSES_DIR / f"{rater_id}_responses.csv"

def response_jsonl_path(rater_id: str) -> Path:
    return RESPONSES_DIR / f"{rater_id}_responses.jsonl"

def save_response(record: Dict[str, Any], rater_id: str):
    csv_path = response_csv_path(rater_id)
    jsonl_path = response_jsonl_path(rater_id)

    flat = dict(record)
    for key, value in list(flat.items()):
        if isinstance(value, (dict, list)):
            flat[key] = json.dumps(value, ensure_ascii=False)

    write_header = not csv_path.exists()
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(flat.keys()))
        if write_header:
            writer.writeheader()
        writer.writerow(flat)

    with open(jsonl_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

def load_completed_ids(rater_id: str) -> set:
    csv_path = response_csv_path(rater_id)
    completed = set()
    if not csv_path.exists():
        return completed
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                completed.add(row.get("sample_hash"))
    except Exception:
        pass
    return completed

# ----------------------------
# UI
# ----------------------------
st.title("Human Evaluation App")

with st.sidebar:
    st.header("Setup")
    rater_id = st.text_input("Rater ID", placeholder="e.g. friend_1")
    uploaded = st.file_uploader("Upload JSONL file", type=["jsonl"])
    reveal_actual_first = st.checkbox("Reveal actual output immediately", value=False)
    show_raw_json = st.checkbox("Show raw JSON", value=False)

if not rater_id:
    st.info("Enter a Rater ID to begin.")
    st.stop()

if not uploaded:
    st.info("Upload a JSONL sample file.")
    st.stop()

samples = load_jsonl(uploaded)
if not samples:
    st.error("No valid JSONL rows were loaded.")
    st.stop()

completed_ids = load_completed_ids(rater_id)

pending_samples = [s for s in samples if build_sample_hash(s) not in completed_ids]
all_count = len(samples)
done_count = len(completed_ids.intersection({build_sample_hash(s) for s in samples}))
progress = 0 if all_count == 0 else done_count / all_count

st.progress(progress)
st.caption(f"Completed: {done_count}/{all_count}")

if not pending_samples:
    st.success("All samples completed for this rater.")
    st.stop()

sample_ids = [s["sample_id"] for s in pending_samples]
selected_id = st.selectbox("Choose sample", sample_ids, index=0)
sample = next(s for s in pending_samples if s["sample_id"] == selected_id)

sample_hash = build_sample_hash(sample)
role = sample["role"]
pred = sample["predicted_parsed"]
actual = sample["actual_output"]
input_payload = sample["input_payload"]
plan = sample["normalized_plan"]

st.subheader(f"Sample: {sample['sample_id']}")
meta_cols = st.columns(4)
meta_cols[0].metric("Role", role.title())
meta_cols[1].metric("Model", sample.get("model_name", ""))
meta_cols[2].metric("Seed", str(sample.get("seed", "")))
meta_cols[3].metric("JSON Valid", str(sample.get("json_valid", False)))

# ----------------------------
# Input section
# ----------------------------
with st.expander("Input Payload", expanded=True):
    if role == "auditor":
        left, right = st.columns(2)

        with left:
            st.markdown("### Requirements")
            st.json(input_payload.get("requirements", {}))

            st.markdown("### Plan Summary")
            st.write(plan.get("title", "—"))
            st.write(plan.get("thinking_summary", "—"))
            st.write(plan.get("executive_summary", "—"))

        with right:
            st.markdown("### Plan Sections")
            section_view = {
                "architecture_overview": plan.get("architecture_overview"),
                "technology_stack": plan.get("technology_stack"),
                "functional_feature_map": plan.get("functional_feature_map"),
                "system_components": plan.get("system_components"),
                "workflows": plan.get("workflows"),
                "data_model": first_nonempty(plan, ["data_model", "datamodel"]),
                "api_design": plan.get("api_design"),
                "security_and_compliance": plan.get("security_and_compliance"),
                "deployment_and_operations": plan.get("deployment_and_operations"),
                "observability": plan.get("observability"),
                "cost_and_scaling": plan.get("cost_and_scaling"),
                "phased_implementation": plan.get("phased_implementation"),
                "development_guidelines": plan.get("development_guidelines"),
                "risks_and_tradeoffs": plan.get("risks_and_tradeoffs"),
                "open_questions_resolved": plan.get("open_questions_resolved"),
            }
            st.json(section_view)

    else:
        left, right = st.columns(2)

        with left:
            st.markdown("### Requirements")
            st.json(input_payload.get("requirements", {}))

            st.markdown("### Context")
            context_view = {
                "round": input_payload.get("round"),
                "focus_issues": input_payload.get("focus_issues", []),
                "issue_ledger": input_payload.get("issue_ledger", []),
                "revision_memory": input_payload.get("revision_memory", []),
                "accepted_exceptions": input_payload.get("accepted_exceptions", []),
                "confirmed_decisions": safe_get(input_payload, ["requirements", "confirmed_decisions"], {}),
            }
            st.json(context_view)

        with right:
            st.markdown("### Previous Plan / Best Plan")
            previous_plan = input_payload.get("previous_plan", {})
            best_plan = input_payload.get("best_plan", {})
            st.write("Previous Plan present:", bool(previous_plan))
            st.write("Best Plan present:", bool(best_plan))
            if previous_plan:
                st.json(previous_plan)
            if best_plan:
                st.json(best_plan)

# ----------------------------
# Prediction and actual
# ----------------------------
col1, col2 = st.columns(2)

with col1:
    st.markdown("## Model Predicted Output")
    st.write("### Summary")
    st.write(pred.get("thinking_summary", "—"))
    st.write(pred.get("summary", "—"))

    st.write("### Strengths")
    st.text(list_to_bullets(pred.get("strengths", [])))

    st.write("### Concerns")
    st.text(list_to_bullets(pred.get("concerns", [])))

    st.write("### Blocking Issues")
    st.text(list_to_bullets(pred.get("blocking_issues", [])))

    st.write("### Recommendations")
    st.text(list_to_bullets(pred.get("recommendations", [])))

    if role == "auditor":
        st.write("### Issue Updates")
        st.text(list_to_bullets(pred.get("issue_updates", [])))
        st.write("### Requirement Conflicts")
        st.text(list_to_bullets(pred.get("requirement_conflicts", [])))
    else:
        st.write("### Fix Report")
        st.text(list_to_bullets(pred.get("fix_report", [])))

    st.write("### Rubric Scores")
    st.json(pred.get("rubric_scores", {}))

with col2:
    st.markdown("## Actual Output")
    if reveal_actual_first:
        show_actual = True
    else:
        show_actual = st.checkbox("Reveal actual output for comparison", value=False)

    if show_actual:
        st.write("### Summary")
        st.write(actual.get("thinking_summary", "—"))
        st.write(actual.get("summary", "—"))

        st.write("### Strengths")
        st.text(list_to_bullets(actual.get("strengths", [])))

        st.write("### Concerns")
        st.text(list_to_bullets(actual.get("concerns", [])))

        st.write("### Blocking Issues")
        st.text(list_to_bullets(actual.get("blocking_issues", [])))

        st.write("### Recommendations")
        st.text(list_to_bullets(actual.get("recommendations", [])))

        if role == "auditor":
            st.write("### Issue Updates")
            st.text(list_to_bullets(actual.get("issue_updates", [])))
            st.write("### Requirement Conflicts")
            st.text(list_to_bullets(actual.get("requirement_conflicts", [])))
        else:
            st.write("### Fix Report")
            st.text(list_to_bullets(actual.get("fix_report", [])))

        st.write("### Rubric Scores")
        st.json(actual.get("rubric_scores", {}))
    else:
        st.info("Keep hidden for unbiased first scoring.")

if show_raw_json:
    with st.expander("Raw JSON", expanded=False):
        st.markdown("### predicted_raw_text")
        st.code(sample.get("predicted_raw_text", ""), language="json")
        st.markdown("### predicted_parsed")
        st.code(prettify_json(sample.get("predicted_parsed", {})), language="json")
        st.markdown("### actual_output")
        st.code(prettify_json(sample.get("actual_output", {})), language="json")

# ----------------------------
# Evaluation form
# ----------------------------
st.markdown("## Evaluation Form")

with st.form(key=f"eval_form_{sample_hash}"):
    rubric_names = get_role_rubric(role)
    st.markdown("### Independent scoring")

    score_cols = st.columns(len(rubric_names))
    human_scores = {}
    for i, rubric in enumerate(rubric_names):
        with score_cols[i]:
            human_scores[rubric] = st.slider(
                rubric.replace("_", " ").title(),
                min_value=0,
                max_value=10,
                value=5,
                step=1,
            )

    final_decision = st.selectbox(
        "Final decision",
        ["pass", "partial_pass", "fail"] if role == "architect" else ["approve", "borderline", "block"]
    )

    confidence = st.slider("Confidence", 1, 5, 3)

    st.markdown("### Comparison after reviewing actual output")
    reference_alignment = st.selectbox(
        "Predicted output vs actual output",
        [
            "aligned",
            "partially_aligned",
            "not_aligned",
            "predicted_better_than_actual",
            "actual_better_than_predicted",
        ]
    )

    key_misses = st.text_area("Key misses or differences")
    qualitative_feedback = st.text_area("Overall evaluator feedback")

    submitted = st.form_submit_button("Save evaluation")

if submitted:
    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "rater_id": rater_id,
        "sample_hash": sample_hash,
        "sample_id": sample.get("sample_id"),
        "role": role,
        "case_type": sample.get("case_type"),
        "model_name": sample.get("model_name"),
        "adapter_path": sample.get("adapter_path"),
        "seed": sample.get("seed"),
        "json_valid": sample.get("json_valid"),
        "decision": final_decision,
        "confidence": confidence,
        "reference_alignment": reference_alignment,
        "human_scores": human_scores,
        "key_misses": key_misses,
        "qualitative_feedback": qualitative_feedback,
        "predicted_rubric_scores": pred.get("rubric_scores", {}),
        "actual_rubric_scores": actual.get("rubric_scores", {}),
        "predicted_summary": pred.get("summary", ""),
        "actual_summary": actual.get("summary", ""),
    }

    save_response(record, rater_id)
    st.success("Saved. Refresh or choose the next sample.")

# ----------------------------
# Footer info
# ----------------------------
with st.expander("Detected schema summary", expanded=False):
    schema_summary = {
        "sample_id": sample.get("sample_id"),
        "role": role,
        "top_level_keys": list(sample.keys()),
        "predicted_keys_normalized": list(pred.keys()),
        "actual_keys_normalized": list(actual.keys()),
    }
    st.json(schema_summary)