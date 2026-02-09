import dspy
from dspy.teleprompt import BootstrapFewShot
import os
import json
import yaml
import glob
import logging
import argparse
import shutil
import re
from typing import List, Dict, Union, Any

# Google GenAI SDK
from google import genai
from google.genai import types

# ==============================================================================
# 1. YAML BEAUTIFIER
# ==============================================================================
def setup_yaml():
    """Configures YAML to print long strings as blocks (|) for readability."""
    def str_presenter(dumper, data):
        if len(data.splitlines()) > 1 or "\n" in data:
            return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
        return dumper.represent_scalar('tag:yaml.org,2002:str', data)
    yaml.add_representer(str, str_presenter)

setup_yaml()

# ==============================================================================
# 2. CONFIG & UTILS
# ==============================================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("VeriFlow")

def strip_markdown(text: str) -> str:
    if not isinstance(text, str): return str(text)
    pattern = r"```(?:json)?\s*(.*?)\s*```"
    match = re.search(pattern, text, re.DOTALL)
    if match: return match.group(1).strip()
    return text.strip()

# ==============================================================================
# 3. MULTIMODAL ADAPTER
# ==============================================================================
class PDFArtifact:
    _registry = {} 
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.filename = os.path.basename(file_path)
        if not os.path.exists(file_path): raise FileNotFoundError(f"PDF not found: {file_path}")
        with open(file_path, "rb") as f: self.bytes = f.read()
        self.tag = f"<<<PDF_ARTIFACT:{self.filename}>>>"
        PDFArtifact._registry[self.tag] = self.bytes

    @classmethod
    def get_bytes(cls, tag: str): return cls._registry.get(tag)
    def __str__(self): return self.tag
    def __repr__(self): return self.tag

class GeminiMultimodal(dspy.LM):
    def __init__(self, model="gemini-3-pro-preview", api_key=None, **kwargs):
        super().__init__(model="openai/dummy") 
        self.target_model = model 
        self.provider = "google"
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key: raise ValueError("GEMINI_API_KEY is required.")
        self.client = genai.Client(api_key=self.api_key)
        self.generation_config = types.GenerateContentConfig(
            temperature=kwargs.get("temperature", 0.0),
            max_output_tokens=kwargs.get("max_output_tokens", 8192),
            tools=[], tool_config=None 
        )
        self.history = []

    def __call__(self, prompt=None, messages=None, **kwargs):
        actual_prompt = prompt if prompt else kwargs.get("prompt")
        if not actual_prompt and messages:
            actual_prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        if not actual_prompt: return [""]

        # Parse tags
        tag_pattern = r"(<<<PDF_ARTIFACT:.*?>>>)"
        parts = re.split(tag_pattern, actual_prompt)
        contents_parts = []
        for part in parts:
            if not part: continue
            pdf_bytes = PDFArtifact.get_bytes(part)
            if pdf_bytes:
                contents_parts.append(types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"))
            else:
                contents_parts.append(types.Part.from_text(text=part))

        # Call Gemini
        response_text = ""
        try:
            response = self.client.models.generate_content(
                model=self.target_model, contents=[types.Content(parts=contents_parts)],
                config=self.generation_config
            )
            if response.text: response_text = response.text
        except Exception as e:
            logger.error(f"Gemini API Error: {e}")

        self.history.append({"prompt": actual_prompt, "response": {"choices": [{"text": response_text}]}, "kwargs": kwargs})
        return [response_text]

# ==============================================================================
# 4. EXPERT SIGNATURES (FIXED FOR EMBEDDED CODE)
# ==============================================================================

class ScholarExtraction(dspy.Signature):
    """
    You are an expert Scientific Data Curator.
    Analyze the PDF and extract the experimental design into ISA JSON format.
    
    CRITICAL:
    - Identify if steps require 'File' inputs or 'Directory' inputs based on the context (e.g. "iterating over a folder" implies Directory).
    """
    pdf_file = dspy.InputField(desc="The full scientific manuscript (PDF Artifact)")
    study_design_json = dspy.OutputField(desc="The ISA-compliant JSON object")

class EngineerGeneration(dspy.Signature):
    """
    You are a Principal DevOps Engineer. 
    Map the Theoretical ISA Design to EXECUTABLE, SELF-CONTAINED CWL Code.
    
    CRITICAL REQUIREMENTS:
    1. **Self-Contained Scripts**: You MUST use `InitialWorkDirRequirement` to embed the Python script content directly into the CWL tool. 
       - DO NOT assume the .py file exists externally. 
       - Paste the script content into the `listing` section of `InitialWorkDirRequirement`.
    2. **Docker**: Include a `DockerRequirement` (e.g., python:3.9-slim).
    3. **Completeness**: Generate X Tool CWLs + 1 Workflow CWL + 1 Dockerfile.
    4. **Type Safety**: Ensure Workflow step outputs match the inputs of the next step (File vs Directory).
    """
    isa_json = dspy.InputField(desc="The theoretical study design requirements")
    repo_context = dspy.InputField(desc="The list of available executable scripts (Ground Truth)")
    infrastructure_code = dspy.OutputField(desc="A JSON dictionary mapping filenames to code content")

# ==============================================================================
# 5. METRICS (STRICTER CHECKS)
# ==============================================================================

def scholar_metric(gold, pred, trace=None):
    clean_text = strip_markdown(pred.study_design_json)
    try:
        pred_json = json.loads(clean_text)
        if "studyDesign" in pred_json: return 1
        return 0 
    except: return 0

def engineer_metric(gold, pred, trace=None):
    clean_text = strip_markdown(pred.infrastructure_code)
    try: 
        pred_dict = json.loads(clean_text)
        gold_dict = json.loads(gold.infrastructure_code)
    except: 
        return 0 

    # 1. Hallucination Check
    repo_context = gold.repo_context
    known_snippets = []
    for line in repo_context.split('\n'):
        if "def " in line:
            func_name = line.split("def ")[1].split("(")[0].strip()
            known_snippets.append(func_name)
    
    hallucinations = 0
    missing_embedding = 0 # NEW PENALTY TRACKER

    for fname, content in pred_dict.items():
        if isinstance(content, str) and "python" in content:
            # Check for hallucinated logic
            found = any(s in content for s in known_snippets)
            if not found and fname != "workflow.cwl" and len(known_snippets) > 0:
                hallucinations += 1
            
            # CRITICAL CHECK: Does it embed the script?
            # We look for "InitialWorkDirRequirement" if it's a CWL file running python
            if fname.endswith(".cwl") and "InitialWorkDirRequirement" not in content:
                missing_embedding += 1
    
    if hallucinations > 0: return 0
    
    # Penalize if scripts are not embedded (0.5 score max if missing embedding)
    embedding_penalty = 0.5 if missing_embedding > 0 else 0

    # 2. Recall Check (Did we generate all files?)
    gold_keys = set(gold_dict.keys())
    pred_keys = set(pred_dict.keys())
    
    intersection = len(gold_keys.intersection(pred_keys))
    union = len(gold_keys.union(pred_keys))
    jaccard = intersection / union if union > 0 else 0
    
    final_score = max(0, jaccard - embedding_penalty)
    return final_score

# ==============================================================================
# 6. DATA LOADING
# ==============================================================================
def extract_python_from_cwl(cwl_content):
    try:
        cwl_obj = yaml.safe_load(cwl_content)
        extracted_scripts = []
        def find_reqs(obj):
            reqs = obj.get("requirements", {})
            if isinstance(reqs, list):
                for r in reqs:
                    if "InitialWorkDirRequirement" in r.get("class", ""): return r
            elif isinstance(reqs, dict):
                 if "InitialWorkDirRequirement" in reqs: return reqs["InitialWorkDirRequirement"]
            return None

        init_work = find_reqs(cwl_obj)
        if init_work:
            listing = init_work.get("listing", [])
            for item in listing:
                if "entry" in item and ".py" in item.get("entryname", ""):
                    extracted_scripts.append(f"--- File: {item['entryname']} (Embedded) ---\n{item['entry']}")
        return "\n".join(extracted_scripts)
    except: return ""

def load_data(step1_dir, step2_dir):
    # Step 1
    pdf_files = glob.glob(os.path.join(step1_dir, "*.pdf"))
    json_files = glob.glob(os.path.join(step1_dir, "*.json"))
    if not pdf_files or not json_files: raise FileNotFoundError("Missing Step1 files")
    
    pdf_artifact = PDFArtifact(pdf_files[0])
    with open(json_files[0], 'r', encoding='utf-8') as f: scholar_gt = json.load(f)
        
    # Step 2
    cwl_files = glob.glob(os.path.join(step2_dir, "*.cwl"))
    py_files = glob.glob(os.path.join(step2_dir, "*.py"))
    
    repo_context_parts = []
    engineer_gt_code = {} 

    for py in py_files:
        with open(py, 'r') as f: repo_context_parts.append(f"--- File: {os.path.basename(py)} ---\n{f.read()}\n")

    for cwl in cwl_files:
        with open(cwl, 'r') as f:
            content = f.read()
            engineer_gt_code[os.path.basename(cwl)] = content
            embedded_py = extract_python_from_cwl(content)
            if embedded_py: repo_context_parts.append(embedded_py)

    repo_context = "\n".join(repo_context_parts)
    if not repo_context.strip(): raise ValueError(f"No Python code found in {step2_dir}")

    return {
        "scholar": [dspy.Example(
            pdf_file=str(pdf_artifact), 
            study_design_json=json.dumps(scholar_gt, indent=2)
        ).with_inputs('pdf_file')],
        
        "engineer": [dspy.Example(
            isa_json=json.dumps(scholar_gt, indent=2),
            repo_context=repo_context,
            infrastructure_code=json.dumps(engineer_gt_code, indent=2) 
        ).with_inputs('isa_json', 'repo_context')],
        
        "raw_context": repo_context
    }

# ==============================================================================
# 7. MAIN
# ==============================================================================
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--api_key", default=os.getenv("GEMINI_API_KEY"))
    parser.add_argument("--step1_dir", default="Step1")
    parser.add_argument("--step2_dir", default="Step2")
    args = parser.parse_args()

    lm = GeminiMultimodal(model="gemini-2.0-flash", api_key=args.api_key)
    dspy.settings.configure(lm=lm)
    logger.info("DSPy Configured")

    try:
        data = load_data(args.step1_dir, args.step2_dir)
        logger.info("Data loaded.")
    except Exception as e:
        logger.error(f"Data Load Failed: {e}")
        return

    # Optimize
    logger.info("--- Optimizing Scholar ---")
    scholar_opt = BootstrapFewShot(metric=scholar_metric, max_bootstrapped_demos=1, max_labeled_demos=1)
    scholar_prog = scholar_opt.compile(dspy.ChainOfThought(ScholarExtraction), trainset=data['scholar'])
    
    logger.info("--- Optimizing Engineer ---")
    engineer_opt = BootstrapFewShot(metric=engineer_metric, max_bootstrapped_demos=1, max_labeled_demos=1)
    engineer_prog = engineer_opt.compile(dspy.ChainOfThought(EngineerGeneration), trainset=data['engineer'])

    # --- HELPER: ESCAPING BRACES FOR PYTHON .FORMAT() ---
    def format_dspy_demos_as_text(demos):
        output = []
        for i, d in enumerate(demos):
            d_dict = d.toDict()
            output.append(f"--- EXAMPLE {i+1} ---")
            for k, v in d_dict.items():
                if k == "augmented": continue
                
                # CRITICAL FIX: Double escape braces for Python string formatting
                # { becomes {{ and } becomes }}
                val_str = str(v).replace("{", "{{").replace("}", "}}")
                
                output.append(f"{k.upper()}:\n{val_str}\n")
        return "\n".join(output)

    def get_instructions(prog):
        try:
            pred = prog.predictors()[0]
            sig = getattr(pred, "extended_signature", pred.signature)
            return sig.instructions
        except: return ""

    # Construct Final YAML
    logger.info("Formatting prompts for nodes.py compatibility...")
    
    # We also need to escape instructions if they contain examples with braces
    scholar_instr = get_instructions(scholar_prog).replace("{", "{{").replace("}", "}}")
    engineer_instr = get_instructions(engineer_prog).replace("{", "{{").replace("}", "}}")

    prompts_output = {
        "scholar_system": {"v1_standard": scholar_instr},
        "scholar_extraction": {
            "v1_standard": f"Here are examples:\n\n{format_dspy_demos_as_text(scholar_prog.predictors()[0].demos)}\n\nNOW ANALYZE THE ATTACHED FILE."
        },
        "engineer_cwl_gen": {
            "v1_standard": (
                f"{engineer_instr}\n\n"
                f"--- FEW SHOT EXAMPLES ---\n{format_dspy_demos_as_text(engineer_prog.predictors()[0].demos)}\n\n"
                f"--- CURRENT TASK ---\n"
                # These variables MUST remain single braces because they are REAL placeholders
                f"ISA Design:\n{{isa_json}}\n\n"
                f"Repository Context:\n{{repo_context}}\n\n"
                f"Previous Errors:\n{{previous_errors}}\n\n"
                f"Generate the CWL infrastructure code now."
            )
        },
        "reviewer_critique": {
            "v1_standard": (
                "You are a Senior Systems Architect.\n"
                "Review the following code against the design.\n\n"
                "Design:\n{isa_json}\n\n"
                "Code:\n{generated_code}\n\n"
                "Validation Errors:\n{validation_errors}\n\n"
                "If valid, end with APPROVED. If not, list issues and end with REJECTED."
            )
        }
    }
    
    with open("optimized_prompts.yaml", "w") as f:
        yaml.dump(prompts_output, f, sort_keys=False)
    logger.info("Prompts saved to optimized_prompts.yaml")

    # Validation (No changes needed here as we use direct DSPy execution, not string format)
    logger.info("--- Running Validation Inference ---")
    scholar_res = scholar_prog(pdf_file=data['scholar'][0].pdf_file)
    engineer_res = engineer_prog(
        isa_json=scholar_res.study_design_json,
        repo_context=data['raw_context']
    )
    
    output_dir = "FinalResults"
    if os.path.exists(output_dir): shutil.rmtree(output_dir)
    os.makedirs(output_dir)
    
    try:
        clean_code = strip_markdown(engineer_res.infrastructure_code)
        files = json.loads(clean_code)
        for fname, content in files.items():
            path = os.path.join(output_dir, fname)
            
            final_content = content
            if isinstance(content, (dict, list)):
                final_content = json.dumps(content, indent=2)
            
            with open(path, "w", encoding='utf-8') as f: 
                f.write(str(final_content))
                
        logger.info(f"Success! Generated {len(files)} files in /{output_dir}")
    except Exception as e:
        logger.error(f"Final Output parsing failed: {e}")
        with open(os.path.join(output_dir, "error_raw.txt"), "w") as f:
            f.write(str(engineer_res.infrastructure_code))

if __name__ == "__main__":
    main()