"""Phases and contract metadata — same as new.py."""

# =========================================================
# Phases / Constants
# =========================================================

PHASE_REQUIREMENTS = "REQUIREMENTS"
PHASE_PLANNING = "PLANNING"
PHASE_APPROVED = "APPROVED"
PHASE_DEVELOPMENT = "DEVELOPMENT"

FIELD_PROMPTS = {
    "project_goal": "What exactly should the software do at a high level?",
    "target_users": "Who will use this system most often?",
    "project_class": "What is the main project type? Use one label such as web_app, fullstack_app, mobile_app, desktop_app, api_service, static_website, cli_tool, library_sdk, automation_tool, data_pipeline, ai_system, research_prototype, or infrastructure_project.",
    "capabilities": "Which capabilities are needed? Use comma-separated labels such as frontend, backend, data, auth, ai_llm, integrations, analytics, realtime, payments, admin_panel, public_api, batch_jobs, or devops.",
    "complexity_level": "Use one label such as simple, moderate, advanced, or high_scale.",
    "risk_level": "Use one label such as low, medium, or high.",
    "data_sensitivity": "Use one label such as none, internal, personal, financial, health, or confidential.",
    "external_exposure": "Use one label such as local_only, internal_only, private_authenticated, partner_facing, or public_internet.",
    "access_model": "Should it be public, anonymous, account-based, subscription-based, or something else?",
    "feature_scope": "What major features should be included?",
    "frontend_stack": "What frontend stack should be used?",
    "backend_stack": "What backend stack should be used?",
    "data_platform": "What database and storage approach should be used?",
    "hosting_target": "Where should it be deployed or hosted?",
    "security_baseline": "What basic security and abuse-prevention controls are required?",
    "privacy_retention_policy": "How should logs, stored data, and retention be handled?",
    "mvp_scope": "What should the first shippable version include?",
    "future_scope": "What can be phased after MVP?",
    "constraints": "What practical constraints exist?",
    "observability_baseline": "What logging, metrics, tracing, and alerting should exist?",
    "execution_preference": "How should execution trade-offs be handled?",
    "llm_integration": "What model integration strategy should be used?",
    "compliance_context": "What compliance or privacy posture is expected?",
}

CORE_REQUIRED_FIELDS = [
    "project_goal", "target_users", "project_class", "capabilities",
    "access_model", "feature_scope", "risk_level",
    "data_sensitivity", "external_exposure", "security_baseline",
]

INTERNAL_PLANNING_FIELDS = [
    "future_scope", "constraints", "observability_baseline",
    "execution_preference", "llm_integration", "compliance_context",
]

PROJECT_CLASS_DEFAULT_CAPABILITIES = {
    "static_website": ["frontend"],
    "landing_page": ["frontend"],
    "dashboard": ["frontend", "backend", "data"],
    "web_app": ["frontend", "backend", "data", "devops"],
    "fullstack_app": ["frontend", "backend", "data", "devops"],
    "mobile_app": ["frontend", "backend", "data", "devops"],
    "desktop_app": ["frontend", "backend", "data"],
    "api_service": ["backend", "data", "devops"],
    "cli_tool": [],
    "library_sdk": [],
    "automation_tool": ["backend", "batch_jobs"],
    "data_pipeline": ["backend", "data", "batch_jobs", "devops"],
    "ai_system": ["backend", "data", "ai_llm", "devops"],
    "research_prototype": [],
    "infrastructure_project": ["devops"],
}

SPECIALISTS = [
    "RequirementCoordinator", "ProjectScopeAgent", "BackendAgent",
    "FrontendAgent", "SecurityAgent", "DataAgent", "DevOpsAgent",
]
REASONERS = [
    "ProductReasoner", "ArchitectReasoner", "SecurityReasoner",
    "ConstraintReasoner", "CriticReasoner", "ContextCompactor",
]
POST_APPROVAL_AGENTS = [
    "ExecutionPlannerAgent", "TutorAgent", "QAEngineerAgent", "NarrativeWriterAgent",
    "DeepSectionWriterAgent", "DiagramAgent",
]
ALL_AGENTS = (
    ["GreeterAgent"]
    + SPECIALISTS
    + REASONERS
    + ["ArchitectAgent", "AuditorAgent"]
    + POST_APPROVAL_AGENTS
)

CONTRACT_TO_NOTE_PATH = {
    "project_goal": "project.goal",
    "target_users": "project.target_users",
    "project_class": "project.project_class",
    "capabilities": "project.capabilities",
    "complexity_level": "constraints.complexity_level",
    "risk_level": "security.risk_level",
    "data_sensitivity": "data.sensitivity",
    "external_exposure": "security.external_exposure",
    "access_model": "security.access_model",
    "feature_scope": "project.feature_scope",
    "frontend_stack": "frontend.stack",
    "backend_stack": "backend.stack",
    "data_platform": "data.platform",
    "hosting_target": "devops.hosting_target",
    "security_baseline": "security.baseline",
    "privacy_retention_policy": "data.privacy_retention_policy",
    "mvp_scope": "project.mvp_scope",
    "future_scope": "project.future_scope",
    "constraints": "constraints.general",
    "observability_baseline": "devops.observability_baseline",
    "execution_preference": "constraints.execution_preference",
    "llm_integration": "backend.llm_integration",
    "compliance_context": "security.compliance_context",
}