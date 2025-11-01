from config import load_context, MASTER_PROMPT_TEMPLATE, PROMPT_LIBRARY, ARCHITECT_TAGS_INPUT, SCENARIO_CONFIG
import os   

# PARAMETERIZED CONFIGURATION
STAGE2_CONFIG = {
    "FINAL_PROMPT_PREFIX": 'final_copilot_prompt_',
    "PROMPT_INSTRUCTION": "Please provide Scoping, Test Scenarios, and Edge Cases based on the above context."
}

def get_master_prompt(risk_profile):
    """Fills the Master Prompt Template with the current risk profile."""
    return MASTER_PROMPT_TEMPLATE.format(risk_profile=risk_profile)

def save_final_prompt_custom(prompt_content, filename):
    """Saves the final compiled prompt to a file for audit/reproducibility with custom naming."""
    try:
        with open(filename, 'w') as f:
            f.write(prompt_content)
        print(f"\n[AUDIT LOG]: Final compiled prompt saved to '{filename}'.")
    except IOError as e:
        print(f"\n[ERROR]: Could not save prompt file: {e}")

def generate_edge_cases_output(config):
    """Generates the formatted string for the Edge Case section using config data."""
    output = "--- 🔪 EDGE CASE DISCOVERY (Driven by TAG: EDGE_DATES) ---\n"
    output += "Based on the component's reliance on date fields, the following edge cases should be included:\n"
    
    for i, case in enumerate(config["EDGE_CASES"], 1):
        output += f"{i}. **{case['name']}**: Use `{case['value']}`. Rationale: {case['description']}\n"
        
    return output

def compile_and_generate_test():
    """
    STAGE 2: Compiles the full prompt for EACH primary risk, simulates generation, 
    and saves the prompt.
    """
    print("--- STAGE 2: INTERACTIVE TEST CASE CREATION (MULTIPLE PROMPT GENERATION) ---")
    
    current_context = load_context()
    primary_risks_list = current_context["PRIMARY_RISKS"]
    risk_profile_summary = current_context["RISK_PROFILE_SUMMARY"]
    primary_score = current_context["CRITICAL_RISK_SCORE"]
    
    if not primary_risks_list:
        print("Error: No primary risks found in context to generate tests.")
        return

    # 1. Compile base user instructions once
    user_instructions = "\n".join([PROMPT_LIBRARY.get(tag, f"ERROR: Unknown tag {tag}") for tag in ARCHITECT_TAGS_INPUT])
    
    # Check if context is updated (sanity check)
    if primary_score == 1:
        print("\n🚨 WARNING: Context score is still 1. Run 1_analyzer_feedback.py with Score 5 issues first to see targeted prompts.🚨\n")


    for i, risk_item in enumerate(primary_risks_list):
        risk_key_finding = risk_item["KEY_FINDING"]
        risk_id = risk_item["ID"]

        print(f"\n\n=======================================================")
        print(f"GENERATING PROMPT {i+1} OF {len(primary_risks_list)}: TARGETING {risk_id}")
        print(f"=======================================================")

        # 2. Build the LLM's system context
        master_context = get_master_prompt(risk_profile_summary)

        # 3. Assemble the final, complete prompt, explicitly focusing on the current risk item
        final_prompt = (
            f"{master_context}\n"
            "=================================================================\n"
            f"## CURRENT PRIMARY FOCUS: {risk_id} - {risk_key_finding}\n"
            "## USER SCENARIO INSTRUCTIONS:\n"
            f"{user_instructions}\n"
            f"{STAGE2_CONFIG['PROMPT_INSTRUCTION']}"
        )

        # 4. Save the compiled prompt to a unique file
        final_prompt_filename = f'{STAGE2_CONFIG["FINAL_PROMPT_PREFIX"]}{risk_id}.txt'
        save_final_prompt_custom(final_prompt, final_prompt_filename)
        
        # 5. Simulate the LLM's value-added generation (Adapted to the current risk)
        simulated_output = f"""
✅ LLM GENERATED ARTIFACTS: SCENARIOS & RECOMMENDATIONS (Targeted for {risk_id})
**Primary Focus:** {risk_key_finding} (Score {primary_score}/5)

--- SCOPING RECOMMENDATION ---
This test is SCOPED to **exclusively validate the critical risk path for {risk_id}**, ensuring this core functional failure is mitigated first.

--- 🔎 GENERATED TEST SCENARIOS ---
1. **Critical Scenario ({risk_id} / Score {primary_score}):**
    - **Goal:** {SCENARIO_CONFIG['CRITICAL_ASSERTION_GOAL']} (Contextually adapted to {risk_id})
    - **Assertion:** {SCENARIO_CONFIG['CRITICAL_ASSERTION_DETAIL']}
    - **Tag Source:** `TAG: HIGH_RISK_PEP` + Feedback Loop.

2. **Secondary Scenario:** (Focus on the broader risk profile)
    - **Goal:** {SCENARIO_CONFIG['SECONDARY_ASSERTION_GOAL']}
    - **Assertion:** {SCENARIO_CONFIG['SECONDARY_ASSERTION_DETAIL']}

{generate_edge_cases_output(SCENARIO_CONFIG)}
"""
        print(simulated_output)

if __name__ == "__main__":
    compile_and_generate_test()