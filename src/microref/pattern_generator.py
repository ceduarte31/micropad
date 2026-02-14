import os
import re
import csv
import yaml
import time
import json
import logging
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
import random

# --- 1. Configuration and Setup ---
load_dotenv()

try:
    client = OpenAI()
except Exception as e:
    print(f"FATAL: Error initializing OpenAI client: {e}")
    exit(1)

# --- Centralized Model Configuration ---
MODEL_CONFIG = {
    "default": {
        "max_output_tokens": 128_000,
        "supports_temperature": False,
        "tpm_limit": 500_000,
        "rpm_limit": 300,
        "token_param_name": "max_completion_tokens", # Specific parameter for this model
        "notes": "Advanced reasoning model with very high throughput."
    }
}

# --- Configuration from Environment Variables ---
LLM_MODEL = os.environ.get("PATTERN_GENERATOR_MODEL", "gpt-5")
SEED = int(os.environ.get("PATTERN_GENERATOR_SEED", 20250928))
INPUT_CSV_FILE = os.environ.get("PATTERN_GENERATOR_INPUT_CSV", "experiment_data/microref/pattern_input.csv")
OUTPUT_DIRECTORY = os.environ.get("PATTERN_GENERATOR_OUTPUT_DIR", ".generated/microref/generated_patterns")
EXAMPLE_YAML_FILE = os.environ.get("PATTERN_GENERATOR_EXAMPLE_YAML", "config/patterns/service_mesh.yaml")
LOG_FILE = os.environ.get("PATTERN_GENERATOR_LOG_FILE", ".generated/microref/logs/generation_log.jsonl")
API_TIMEOUT = int(os.environ.get("PATTERN_GENERATOR_API_TIMEOUT", 300))
BATCH_DELAY = float(os.environ.get("PATTERN_GENERATOR_BATCH_DELAY", 1.0))
MAX_RETRIES_RATE_LIMIT = int(os.environ.get("PATTERN_GENERATOR_MAX_RETRIES_RATE_LIMIT", 5))
RATE_LIMIT_WAIT = int(os.environ.get("PATTERN_GENERATOR_RATE_LIMIT_WAIT", 60))

# --- Setup Logging ---
LOG_DIRECTORY = os.path.dirname(LOG_FILE)
if LOG_DIRECTORY and not os.path.exists(LOG_DIRECTORY):
    os.makedirs(LOG_DIRECTORY)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.propagate = False
if logger.hasHandlers():
    logger.handlers.clear()
handler = logging.FileHandler(LOG_FILE, mode='a')
formatter = logging.Formatter('%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# --- 2. Core Logic ---
def extract_yaml_block(text):
    """Extracts a YAML code block from a string, handling markdown fences."""
    pattern = re.compile(r"```yaml\s*\n(.*?)\n```|((?:^[a-zA-Z0-9_-]+:.*\n?)+)", re.DOTALL | re.MULTILINE)
    match = pattern.search(text.strip())
    if match:
        return match.group(1) or match.group(2)
    return None

SYSTEM_PROMPT = "You are an expert software architect. Your task is to generate a detailed YAML configuration file for a given software pattern. Your final output MUST be only the single, valid YAML block."

def get_user_prompt(pattern_name, pattern_description, pattern_url, example_yaml_str):
    """Constructs the detailed user prompt for the LLM."""
    return f"Generate a complete YAML file for: {pattern_name}\n\nINFO:\n- Description: {pattern_description}\n- Reference: {pattern_url}\n\nFollow the exact structure of this EXAMPLE:\n{example_yaml_str}"

def log_event(event_name, details):
    log_data = {"timestamp": datetime.utcnow().isoformat() + "Z", "event": event_name, "details": details}
    logger.info(json.dumps(log_data))
    for handler in logger.handlers:
        handler.flush()

def generate_pattern_yaml(pattern_name, description, url, example_yaml, model_config):
    """Interacts with the OpenAI API using centralized and dynamic model configuration."""
    log_event("generation_started", {'pattern_name': pattern_name, 'model': LLM_MODEL, 'seed': SEED})
    
    for attempt in range(MAX_RETRIES_RATE_LIMIT + 3):
        try:
            user_prompt = get_user_prompt(pattern_name, description, url, example_yaml)
            
            # Base payload
            request_payload = {
                "model": LLM_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                "seed": SEED,
            }
            
            # Dynamically add the correct token limit parameter
            token_param_name = model_config.get("token_param_name", "max_tokens")
            max_tokens_value = model_config.get("max_output_tokens", 4096)
            request_payload[token_param_name] = max_tokens_value
            
            if model_config.get("supports_temperature", False):
                request_payload["temperature"] = 0.1
            
            log_event("api_request_sent", {"pattern_name": pattern_name, "attempt": attempt + 1})
            
            print(f"\n📞 Calling OpenAI API for '{pattern_name}'...", end="", flush=True)
            start_api_time = time.time()
            
            completion = client.chat.completions.create(**request_payload, timeout=API_TIMEOUT)
            
            api_duration = time.time() - start_api_time
            print(f" ✅ ({api_duration:.2f}s)", flush=True)

            log_event("api_response_received", {"pattern_name": pattern_name, "duration": api_duration})
            
            generated_content = completion.choices[0].message.content
            return generated_content.strip(), "PASS"
            
        except Exception as e:
            error_type = type(e).__name__
            error_message = str(e)
            log_event("api_call_failed", {"pattern_name": pattern_name, "attempt": attempt + 1, "error": error_message})
            print(f" ❌ API Error: {error_type}", flush=True)
            
            if "rate" in error_message.lower():
                wait_time = RATE_LIMIT_WAIT * (attempt + 1)
                print(f"   ⏱️ Rate limit hit! Waiting {wait_time}s...", flush=True)
                time.sleep(wait_time)
                continue
            
            if "BadRequestError" in error_type:
                print(f"   Fatal request error. Check model parameters. Details: {error_message}")
                return None, "BAD_REQUEST"
            
            time.sleep(2 * (2 ** attempt)) # Exponential backoff for other errors
    
    return None, "FAIL"

def display_progress(current, total, pattern_name, status, start_time):
    """Display enhanced progress information."""
    elapsed = time.time() - start_time
    sec_per_item = elapsed / current if current > 0 else 0
    eta = (total - current) * sec_per_item
    eta_str = f"{int(eta // 60)}m{int(eta % 60)}s" if eta > 0 else "N/A"
    bar = '█' * int(30 * current / total) + '░' * (30 - int(30 * current / total))
    print(
        f"\r🔄 [{bar}] {current/total:.1%} | {current}/{total} | "
        f"{pattern_name[:25]:<25} ({status}) | "
        f"Speed: {sec_per_item:.1f}s/item | ETA: {eta_str}",
        end="", flush=True
    )

def main():
    """Main function to orchestrate the YAML generation process."""
    model_conf = MODEL_CONFIG.get(LLM_MODEL, MODEL_CONFIG["default"])
    
    print("🚀 Starting pattern generation process...")
    print(f"   - Model: {LLM_MODEL}, Seed: {SEED}")
    
    if not os.path.exists(OUTPUT_DIRECTORY):
        os.makedirs(OUTPUT_DIRECTORY)

    try:
        with open(EXAMPLE_YAML_FILE, 'r') as f: example_yaml_content = f.read()
        with open(INPUT_CSV_FILE, 'r') as f: patterns = list(csv.DictReader(f))
    except FileNotFoundError as e:
        print(f"❌ FATAL: Cannot find required file: {e.filename}")
        return

    total_patterns = len(patterns)
    print(f"📊 Processing {total_patterns} patterns...")
    start_time = time.time()
    successful_generations = 0
    failed_generations = 0
    
    for i, row in enumerate(patterns, 1):
        pattern_name = row.get('pattern_name', '').strip()
        status = "SKIP"

        if pattern_name:
            generated_content, status = generate_pattern_yaml(
                pattern_name, row.get('description', ''), row.get('url', ''), example_yaml_content, model_conf
            )
        
            if generated_content and status == "PASS":
                extracted_yaml = extract_yaml_block(generated_content)
                
                if not extracted_yaml:
                    status = "YAML_FAIL"
                    failed_generations += 1
                    error_path = os.path.join(OUTPUT_DIRECTORY, f"{pattern_name.replace(' ', '_').lower()}.error.txt")
                    with open(error_path, 'w') as f: f.write(generated_content)
                else:
                    output_path = os.path.join(OUTPUT_DIRECTORY, f"{pattern_name.replace(' ', '_').lower()}.yaml")
                    try:
                        yaml.safe_load(extracted_yaml)
                        with open(output_path, 'w') as f: f.write(extracted_yaml)
                        successful_generations += 1
                    except (yaml.YAMLError, IOError):
                        status = "SAVE_FAIL"
                        failed_generations += 1
                        error_path = output_path.replace('.yaml', '.yaml.error.txt')
                        with open(error_path, 'w') as f: f.write(extracted_yaml)
            else:
                failed_generations += 1
        else:
            failed_generations += 1

        display_progress(i, total_patterns, pattern_name or "Unnamed Pattern", status, start_time)
        if i < total_patterns: time.sleep(BATCH_DELAY)

    total_runtime = time.time() - start_time
    print("\n\n" + "="*70)
    print("✅ Generation Complete!")
    print(f"   - Total patterns:     {total_patterns}")
    print(f"   - Successful:         {successful_generations}")
    print(f"   - Failed/Skipped:     {failed_generations}")
    print(f"   - Total runtime:      {int(total_runtime // 60)}m {int(total_runtime % 60)}s")
    print(f"   - Output directory:   '{OUTPUT_DIRECTORY}'")
    print("="*70)

if __name__ == "__main__":
    main()