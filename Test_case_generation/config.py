import json
import os

# The Master Prompt Template
MASTER_PROMPT_TEMPLATE = """
SYSTEM INSTRUCTION: You are an expert PEGA Test Architect. Your primary goal is to generate
Pytest functions and their required JSON input payloads for PEGA API testing.
1. Output MUST be Python and JSON code blocks ONLY.
2. The generated code MUST strictly address the primary risk profile: [RISK_PROFILE].
3. For Python, use 'pytest' and include assertions that validate the risk scenario.
4. For JSON, include 'case_id' and 'client_id' placeholders.

[RISK_PROFILE]: {risk_profile}
"""

# PARAMETRIZED BUSINESS RULES & ARCHITECT INPUTS

PROMPT_LIBRARY = {
    "TAG: HIGH_RISK_PEP": "Test a Policy Enforcement Point where a low-level user attempts a high-value transaction.",
    "TAG: EDGE_DATES": "Include edge case checks for all date fields, especially minimum and maximum valid dates.",
    "TAG: OUTPUT_FORMAT": "Generate both the Pytest function and the accompanying JSON payload.",
    "TAG: COMPONENT_NAME": "The PEGA component is 'CustomerEligibilityService'."
}

# The Architect's preferred input
ARCHITECT_TAGS_INPUT = [
    "TAG: HIGH_RISK_PEP",
    "TAG: EDGE_DATES",
    "TAG: OUTPUT_FORMAT",
    "TAG: COMPONENT_NAME"
]

# Business Logic for the LLM output simulation
SCENARIO_CONFIG = {
    # Assertion details for a high-risk role-mapping test
    "CRITICAL_ASSERTION_GOAL": "Verify that a `LOW_TIER_USER` attempting a `HIGH_VALUE_TRANSFER` transaction is correctly routed through the Policy Enforcement Point (PEP).",
    "CRITICAL_ASSERTION_DETAIL": "The API must explicitly return a **403 Forbidden** status, AND the internal logging must confirm the access group mapping was successfully checked *prior* to denial.",
    "CRITICAL_DEFECT_ID": "PEGA-DEFECT-103", # Placeholder ID
    
    # Secondary assertion details (generic default)
    "SECONDARY_ASSERTION_GOAL": "Verify system behavior under simulated load to ensure locks are acquired/released correctly.",
    "SECONDARY_ASSERTION_DETAIL": "Check for specific PEGA 'ConcurrencyLock' error codes.",
    
    # Edge case definitions
    "EDGE_CASES": [
        {"name": "Maximum Date Bound", "value": "9999-12-31", "description": "Test date field parsing limits."},
        {"name": "Minimum Date Bound", "value": "1900-01-01", "description": "Test historical eligibility calculation compatibility."},
        {"name": "Leap Year Check", "value": "2024-02-29", "description": "Check for previously observed off-by-one errors (PEGA-1002)."},
        {"name": "Invalid Format", "value": "01/01/2024", "description": "Confirm input sanitization is working."}
    ]
}


# DYNAMIC STATE: The learning component
CONTEXT_FILE = 'analysis_context.json'

# Initial, default state of the system
INITIAL_CONTEXT = {
    "HISTORICAL_DEFECTS": ["Off-by-one errors in eligibility date checks (PEGA-1002)."],
    "CRITICAL_RISK_SCORE": 1, # Neutral, lowest possible score
    # Neutral, generic starting focus for the system baseline
    "PRIMARY_RISKS": [
        {"KEY_FINDING": "API compliance and standard schema validation.", "ID": "SYSTEM-BASELINE-001"}
    ],
    # The summary consumed by the AI
    "RISK_PROFILE_SUMMARY": "Priority Score 1/5: Focus on API compliance and standard schema validation."
}

def load_context():
    """Load context from file or create the initial file."""
    if os.path.exists(CONTEXT_FILE):
        with open(CONTEXT_FILE, 'r') as f:
            return json.load(f)
    else:
        save_context(INITIAL_CONTEXT)
        return INITIAL_CONTEXT

def save_context(context):
    """Save the current analysis context to a file."""
    with open(CONTEXT_FILE, 'w') as f:
        json.dump(context, f, indent=4)

# Initialize the current context
ANALYSIS_CONTEXT = load_context()