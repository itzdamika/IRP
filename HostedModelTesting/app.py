import requests
import json

url = "http://93.91.156.86:46948/v1/completions"

headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer EMPTY"
}

input_payload = {
    "round": 2,
    "frozenrequirementcontract": {
        "projectgoal": {"value": "Mobile Wallet"},
        "targetusers": {"value": "Consumers"},
        "projectclass": {"value": "mobileapp"},
        "capabilities": {"value": "frontend, backend, auth"},
        "complexitylevel": {"value": "advanced"},
        "risklevel": {"value": "high"},
        "datasensitivity": {"value": "financial"},
        "externalexposure": {"value": "publicinternet"},
        "accessmodel": {"value": "Biometric Auth"},
        "featurescope": {"value": "Payments"},
        "mvpscope": {"value": "Send money"},
        "securitybaseline": {"value": "SSL Pinning"},
        "frontendstack": {"value": "Swift"},
        "backendstack": {"value": "Java Spring"},
        "dataplatform": {"value": "PostgreSQL"},
        "hostingtarget": {"value": "AWS EKS"},
        "privacyretentionpolicy": {"value": "7 years"},
        "futurescope": {"value": "Crypto"},
        "constraints": {"value": "Sub 1s API response"},
        "observabilitybaseline": {"value": "Datadog"},
        "executionpreference": {"value": "Agile"},
        "compliancecontext": {"value": "PCI-DSS"}
    },
    "requirements": {
        "project": {"goal": "Wallet"},
        "frontend": {"fw": "Swift"},
        "backend": {"rt": "Java"},
        "security": {"ssl": "pinning"},
        "data": {"db": "PostgreSQL"},
        "devops": {"ci": "Bitrise"},
        "constraints": {"ux": "fast"},
        "openquestions": {"q1": "Android?"},
        "confirmeddecisions": {"d1": "iOS First"}
    },
    "issueledger": {
        "SEC-030": {
            "id": "SEC-030",
            "title": "Missing Biometric Auth",
            "severity": "high",
            "status": "unresolved",
            "detail": "Prior audit found standard password auth."
        }
    },
    "revisionmemory": {
        "round_1": "Used standard passwords.",
        "changes_for_round_2": "Added FaceID but dropped SSL Pinning setup."
    },
    "previousaudits": [
        {
            "auditdate": "2026-03-10T00:00:00Z",
            "summary": "Missing biometrics"
        }
    ],
    "reasonerreviews": {
        "product": "iOS Native Wallet.",
        "security": "Needs both Biometric and SSL Pinning."
    },
    "specialistsubplans": {
        "frontend": "Swift Native app.",
        "security": "FaceID enabled."
    },
    "plan": {
        "thinkingsummary": "Added FaceID but removed SSL Pinning.",
        "title": "Mobile Wallet Arch",
        "executivesummary": "Native iOS wallet.",
        "architectureoverview": "Swift frontend to Java Spring APIs on EKS.",
        "technologystack": "Swift, Java Spring Boot, PostgreSQL.",
        "securityandcompliance": "Local FaceID authentication. Standard HTTPS for API calls."
    }
}

AUDITOR_SYSTEM_PROMPT = """You are the strict architecture auditor.

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

prompt = f"""<start_of_turn>user
{AUDITOR_SYSTEM_PROMPT}

---

{json.dumps(input_payload, indent=1)}<end_of_turn>
<start_of_turn>model
"""

data = {
    "model": "my-custom-model", 
    "prompt": prompt,      
    "max_tokens": 5000,    
    "temperature": 0.0
}

data = {
    "model": "my-custom-model", 
    "prompt": prompt,
    "max_tokens": 5000,
    "temperature": 0.0
}

# Send request
response = requests.post(url, headers=headers, json=data)

# Debug full response
print("STATUS:", response.status_code)
print("RAW:", response.text)

# Extract content safely
# Extract content safely
try:
    # Notice it is ['text'], NOT ['message']['content']!
    content = response.json()['choices'][0]['text'].strip()
    print("\n✅ MODEL OUTPUT:\n")
    print(content)
    print("\n🔍 PARSED JSON:\n", json.dumps(json.loads(content), indent=2))

except Exception as e:
    print("\n⚠️ Parsing failed:", e)