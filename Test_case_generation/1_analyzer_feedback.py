import json
import sys
from config import ANALYSIS_CONTEXT, save_context, MASTER_PROMPT_TEMPLATE, load_context, INITIAL_CONTEXT

# --- PARAMETERIZED CONFIGURATION ---
ANALYZER_CONFIG = {
    "PROMPT_HISTORY_FILE": 'master_prompt_history.txt',
    "DEFAULT_ISSUE_FILE": 'new_issue_data.json',
    "MAX_RISK_SCORE": 5,
    "SECONDARY_SCORE_DROP": 1, 
}

def load_issue_data(filename):
    """Reads issue data from the specified JSON array file."""
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
            if not isinstance(data, list):
                print(f"Error: JSON content in '{filename}' must be a list (array) of issues.")
                sys.exit(1)
            return data
    except FileNotFoundError:
        print(f"Error: Input file '{filename}' not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in '{filename}'.")
        sys.exit(1)

def get_master_prompt():
    """Build the current Master Prompt using the latest risk profile."""
    current_context = load_context()
    master_prompt = MASTER_PROMPT_TEMPLATE.format(
        risk_profile=current_context['RISK_PROFILE_SUMMARY']
    )
    return master_prompt

def save_prompt_history(before_prompt, after_prompt, before_risk_summary, after_risk_summary):
    """Saves the before and after state of the Master Prompt to a history file."""
    
    separator = "=" * 80
    
    content = f"""
{separator}
MASTER PROMPT HISTORY - FEEDBACK INTEGRATION

{separator}
STATE 1: BEFORE FEEDBACK
(Risk Profile: {before_risk_summary})
{separator}
{before_prompt}

{separator}
STATE 2: AFTER FEEDBACK
(Risk Profile: {after_risk_summary})
{separator}
{after_prompt}

"""
    with open(ANALYZER_CONFIG["PROMPT_HISTORY_FILE"], 'w') as f:
        f.write(content)
        
    print(f"\n[OUTPUT SAVED] Prompt history written to '{ANALYZER_CONFIG['PROMPT_HISTORY_FILE']}'.")


def integrate_feedback(issue_data):
    """
    Integrates a single issue, handling promotion and co-equal priority.
    """
    current_context = load_context()
    issue_score = issue_data["SCORE"]
    current_highest_score = current_context["CRITICAL_RISK_SCORE"]
    max_score = ANALYZER_CONFIG["MAX_RISK_SCORE"]
    
    # Store the old risk before potential overwrites for the secondary focus text
    old_primary_risks_list = current_context["PRIMARY_RISKS"].copy() 
    old_primary_risk_text = old_primary_risks_list[0]['KEY_FINDING'] if old_primary_risks_list else "No previous critical focus."

    # 1. Update the defect history (regardless of score)
    current_context["HISTORICAL_DEFECTS"].append(f"{issue_data['DESCRIPTION']} ({issue_data['ID']})")

    if issue_score > current_highest_score:
        # Case A: New issue is HIGHER priority (Wipe and replace list)
        current_context["CRITICAL_RISK_SCORE"] = issue_score
        current_context["PRIMARY_RISKS"] = [{
            "KEY_FINDING": issue_data["KEY_FINDING"],
            "ID": issue_data["ID"]
        }]
        secondary_focus = f"Secondary Focus: {old_primary_risk_text} (Score {issue_score - ANALYZER_CONFIG['SECONDARY_SCORE_DROP']}/{max_score})."
        print(f"[PROMOTED]: Issue {issue_data['ID']} (Score {issue_score}) is the NEW single Primary Focus.")

    elif issue_score == current_highest_score:
        # Case B: New issue is EQUAL priority (Append to the list)
        issue_entry = {"KEY_FINDING": issue_data["KEY_FINDING"], "ID": issue_data["ID"]}
        if not any(r['ID'] == issue_entry['ID'] for r in current_context["PRIMARY_RISKS"]):
            current_context["PRIMARY_RISKS"].append(issue_entry)
            print(f"[CO-EQUAL]: Issue {issue_data['ID']} (Score {issue_score}) ADDED as co-equal Primary Focus.")
        else:
            print(f"[SKIPPED]: Issue {issue_data['ID']} already present in primary risks.")
        
        # Secondary focus remains based on the previous structure
        secondary_focus = f"Secondary Focus: Standard robustness checks."

    else:
        # Case C: New issue is LOWER priority (No change to primary list)
        print(f"[LOGGED]: Issue {issue_data['ID']} (Score {issue_score}) is logged. Focus remains unchanged.")
        secondary_focus = f"Secondary Focus: Standard robustness checks."

    # 3. Construct the summary consumed by the AI
    primary_risks_text = " AND ".join([f"{r['ID']}: {r['KEY_FINDING']}" for r in current_context["PRIMARY_RISKS"]])
    
    current_context["RISK_PROFILE_SUMMARY"] = (
        f"Priority Score {current_context['CRITICAL_RISK_SCORE']}/{max_score}: CRITICAL UPDATE: Validate: {primary_risks_text}. "
        f"Tests MUST specifically address ALL listed critical updates. "
        f"{secondary_focus}"
    )

    save_context(current_context)
    return current_context


if __name__ == "__main__":
    
    # SIMULATE PARAMETER INPUT
    ISSUE_FILE_NAME = ANALYZER_CONFIG["DEFAULT_ISSUE_FILE"]
    if len(sys.argv) > 1:
        ISSUE_FILE_NAME = sys.argv[1]

    all_issues = load_issue_data(ISSUE_FILE_NAME)
    
    # Reset context to the clean initial state
    save_context(INITIAL_CONTEXT)
    
    before_prompt = get_master_prompt()
    before_risk_summary = load_context()["RISK_PROFILE_SUMMARY"]
    
    print("\n\n#######################################################")
    print(f"INITIAL SYSTEM STATE: {before_risk_summary}")
    print("#######################################################")
    
    # INTEGRATE ALL FEEDBACK SEQUENTIALLY
    print("\n--- STAGE 1: ANALYZE & FEEDBACK LOOP EXECUTION (Sequential) ---")
    
    for issue in all_issues:
        integrate_feedback(issue)
        
    # SHOW UPDATED CONTEXT
    
    after_prompt = get_master_prompt()
    after_risk_summary = load_context()["RISK_PROFILE_SUMMARY"]
    
    save_prompt_history(before_prompt, after_prompt, before_risk_summary, after_risk_summary)
    
    print("\n\n#######################################################")
    print("UPDATED SYSTEM STATE (VERIFICATION)")
    print("#######################################################")
    
    updated_context = load_context()
    print(f"[FINAL SCORE]: {updated_context['CRITICAL_RISK_SCORE']}/{ANALYZER_CONFIG['MAX_RISK_SCORE']}")
    print(f"[FINAL FOCUS LIST]: {updated_context['PRIMARY_RISKS']}")
    print(f"\n[Updated Master Prompt (AI Context)]:")
    print(after_prompt)