'''
Code to make sure that the prompt.yaml file is in the correct format for the agents to call, handles issues with escape characters
'''
import yaml
import os
import re

# ==============================================================================
# CONFIGURATION
# ==============================================================================
INPUT_FILE = "prompts.yaml"  # The file crashing your app
OUTPUT_FILE = "fixed_prompts.yaml"     # The fixed file to use

# These are the variables your nodes.py actually uses. 
# We will ensure these remain as single braces {var}.
ALLOWED_PLACEHOLDERS = [
    "isa_json",
    "repo_context",
    "previous_errors",
    "generated_code",
    "validation_errors"
]

# ==============================================================================
# YAML BEAUTIFIER (Keep the output readable)
# ==============================================================================
def setup_yaml():
    """Configures YAML to print long strings as blocks (|)."""
    def str_presenter(dumper, data):
        if len(data.splitlines()) > 1 or "\n" in data:
            return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
        return dumper.represent_scalar('tag:yaml.org,2002:str', data)
    yaml.add_representer(str, str_presenter)

setup_yaml()

# ==============================================================================
# CORE LOGIC
# ==============================================================================

def fix_prompt_text(text):
    if not isinstance(text, str):
        return text

    # Step 1: Escape EVERYTHING. 
    # { -> {{ and } -> }}
    # This protects the JSON examples.
    fixed = text.replace("{", "{{").replace("}", "}}")

    # Step 2: Un-escape the valid placeholders.
    # We turn {{isa_json}} back into {isa_json}
    for var in ALLOWED_PLACEHOLDERS:
        # We look for the double-escaped version
        pattern = f"{{{{{var}}}}}"
        replacement = f"{{{var}}}"
        fixed = fixed.replace(pattern, replacement)
        
    return fixed

def recursive_fix(data):
    """Traverses the YAML dictionary and fixes every string value."""
    if isinstance(data, dict):
        return {k: recursive_fix(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [recursive_fix(i) for i in data]
    elif isinstance(data, str):
        return fix_prompt_text(data)
    else:
        return data

def main():
    print(f"Reading from: {INPUT_FILE}")
    
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found.")
        return

    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            
        if not data:
            print("YAML file is empty.")
            return

        # Run the fix
        fixed_data = recursive_fix(data)

        # Save
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            yaml.dump(fixed_data, f, sort_keys=False)
            
        print(f"Success! Fixed prompts saved to: {OUTPUT_FILE}")
        print("---------------------------------------------------")
        print("NEXT STEPS:")
        print(f"1. Rename '{OUTPUT_FILE}' to 'prompts.yaml'")
        print("2. Run your application again.")

    except Exception as e:
        print(f"Failed to process file: {e}")

if __name__ == "__main__":
    main()