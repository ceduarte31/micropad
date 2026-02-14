# config.py - OPTIMIZED FOR PRECISION, RECALL & ACCURACY
import os
import warnings
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

warnings.filterwarnings("ignore", message=".*CUDA.*")
warnings.filterwarnings("ignore", message=".*weights.*were not initialized.*")
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# ============================================================================
# PATHS
# ============================================================================
TARGET_REPO_PATH = Path(
    os.getenv("TARGET_REPO", "./target_repo")
)
PATTERNS_DIR_PATH = Path(
    os.getenv("PATTERNS_DIR", "./config/patterns")
)
DB_PATH = Path(os.getenv("VECTOR_DB_PATH", "./.generated/micropad/vectordb"))

# ============================================================================
# REPRODUCIBILITY
# ============================================================================
RANDOM_SEED = 20251020033400  # Set at runtime in scanner.py


# ============================================================================
# EXPERIMENT CONFIGURATION
# ============================================================================
# These settings control experiment metadata and output organization

RUN_NUMBER = int(os.getenv("RUN_NUMBER", "1"))
# For variation analysis: 1, 2, or 3


# Determine weight scheme name from current weights
def _get_weight_scheme_name():
    """Infer weight scheme name from current weight values."""
    weights = (
        PRIORITY_KEYWORD_WEIGHT,
        PRIORITY_EMBEDDING_WEIGHT,
        PRIORITY_GRAPH_WEIGHT,
        PRIORITY_LLM_WEIGHT,
    )

    # Check against known schemes
    if abs(PRIORITY_LLM_WEIGHT - 0.70) < 0.01:
        return "llm_dominant"
    elif abs(PRIORITY_LLM_WEIGHT - 0.90) < 0.01:
        return "llm_extreme"
    elif abs(PRIORITY_LLM_WEIGHT - 0.30) < 0.01:
        return "balanced"
    else:
        return "custom"


# Output directory structure
RESULTS_BASE_DIR = Path(os.getenv("RESULTS_BASE_DIR", "./.generated/micropad/detection_results"))
RESULTS_OUTPUT_DIR = RESULTS_BASE_DIR


# ============================================================================
# AI PROVIDER CONFIGURATION
# ============================================================================
AI_PROVIDER = os.getenv("AI_PROVIDER", "openai")  # 'openai' | 'ollama'

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")  # MUST be set via environment
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

if AI_PROVIDER == "openai" and not OPENAI_API_KEY:
    raise RuntimeError(
        "OPENAI_API_KEY environment variable is required but not set.\n"
        "Set it with: export OPENAI_API_KEY='sk-...'"
    )

# ============================================================================
# MODEL SELECTION (Provider-specific)
# ============================================================================

# --- OLLAMA MODELS ---
OLLAMA_PLANNER_MODEL = os.getenv("OLLAMA_PLANNER_MODEL", "llama3.1:70b")
OLLAMA_INVESTIGATOR_MODEL = os.getenv("OLLAMA_INVESTIGATOR_MODEL", "llama3.1:70b")
OLLAMA_JUDGE_MODEL = os.getenv("OLLAMA_JUDGE_MODEL", "llama3.1:70b")

# Fallback models (if primary not available)
OLLAMA_PLANNER_MODEL_FALLBACK = os.getenv("OLLAMA_PLANNER_MODEL_FALLBACK", "llama3.1:8b")
OLLAMA_INVESTIGATOR_MODEL_FALLBACK = os.getenv("OLLAMA_INVESTIGATOR_MODEL_FALLBACK", "llama3.1:8b")
OLLAMA_JUDGE_MODEL_FALLBACK = os.getenv("OLLAMA_JUDGE_MODEL_FALLBACK", "llama3.1:8b")

# --- OPENAI MODELS (RECOMMENDED FOR HIGHEST ACCURACY) ---
OPENAI_PLANNER_MODEL = os.getenv("OPENAI_PLANNER_MODEL", "gpt-5-nano-2025-08-07")
OPENAI_INVESTIGATOR_MODEL = os.getenv("OPENAI_INVESTIGATOR_MODEL", "gpt-5-nano-2025-08-07")
OPENAI_JUDGE_MODEL = os.getenv("OPENAI_JUDGE_MODEL", "gpt-5-nano-2025-08-07")

# Active model selection based on provider
if AI_PROVIDER == "openai":
    PLANNER_MODEL = OPENAI_PLANNER_MODEL
    INVESTIGATOR_MODEL = OPENAI_INVESTIGATOR_MODEL
    JUDGE_MODEL = OPENAI_JUDGE_MODEL
    PLANNER_MODEL_FALLBACK = OPENAI_PLANNER_MODEL
    INVESTIGATOR_MODEL_FALLBACK = OPENAI_INVESTIGATOR_MODEL
    JUDGE_MODEL_FALLBACK = OPENAI_JUDGE_MODEL
else:
    PLANNER_MODEL = OLLAMA_PLANNER_MODEL
    INVESTIGATOR_MODEL = OLLAMA_INVESTIGATOR_MODEL
    JUDGE_MODEL = OLLAMA_JUDGE_MODEL
    PLANNER_MODEL_FALLBACK = OLLAMA_PLANNER_MODEL_FALLBACK
    INVESTIGATOR_MODEL_FALLBACK = OLLAMA_INVESTIGATOR_MODEL_FALLBACK
    JUDGE_MODEL_FALLBACK = OLLAMA_JUDGE_MODEL_FALLBACK

# ============================================================================
# EMBEDDING MODEL
# ============================================================================
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "jinaai/jina-embeddings-v2-base-code")

# ============================================================================
# PRIORITIZATION WEIGHTS (LLM-CENTRIC DESIGN)
# ============================================================================
# Our approach prioritizes LLM-based semantic analysis as the primary signal,
# with keywords, embeddings, and graph providing complementary hints for file selection.
# These weights reflect the architectural design: LLM offers the most reliable
# understanding of microservice patterns, while other signals help prioritize
# which files to investigate.

PRIORITY_KEYWORD_WEIGHT = float(os.getenv("PRIORITY_KEYWORD_WEIGHT", "0.20"))
PRIORITY_EMBEDDING_WEIGHT = float(
    os.getenv("PRIORITY_EMBEDDING_WEIGHT", "0.10")
)
PRIORITY_GRAPH_WEIGHT = float(os.getenv("PRIORITY_GRAPH_WEIGHT", "0"))
PRIORITY_LLM_WEIGHT = float(
    os.getenv("PRIORITY_LLM_WEIGHT", "0.70")
)

# Parser signal weights (internal to graph/parser score - should sum to 1.0)
# These distribute the PRIORITY_GRAPH_WEIGHT equally across all parser-extracted signals
PARSER_CENTRALITY_WEIGHT = float(os.getenv("PARSER_CENTRALITY_WEIGHT", "0.25"))
PARSER_DECORATOR_WEIGHT = float(os.getenv("PARSER_DECORATOR_WEIGHT", "0.25"))
PARSER_STRING_WEIGHT = float(os.getenv("PARSER_STRING_WEIGHT", "0.25"))
PARSER_CLASS_WEIGHT = float(os.getenv("PARSER_CLASS_WEIGHT", "0.25"))

WEIGHT_SCHEME = os.getenv("WEIGHT_SCHEME", _get_weight_scheme_name())

# ============================================================================
# THRESHOLDS (PRECISION VS RECALL TUNING)
# ============================================================================
HIGH_PRIORITY_THRESHOLD = float(os.getenv("HIGH_PRIORITY_THRESHOLD", "0.50"))
MEDIUM_PRIORITY_THRESHOLD = float(os.getenv("MEDIUM_PRIORITY_THRESHOLD", "0.30"))
MIN_PRIORITY_SCORE = float(os.getenv("MIN_PRIORITY_SCORE", "0.10"))

JUDGE_CONFIDENCE_THRESHOLD = int(os.getenv("JUDGE_CONFIDENCE_THRESHOLD", "5"))

# ============================================================================
# ANALYSIS BUDGET (DEPTH VS SPEED)
# ============================================================================
MAX_FILES_PER_PATTERN = int(os.getenv("MAX_FILES_PER_PATTERN", "20"))
FILES_PER_BATCH = int(os.getenv("FILES_PER_BATCH", "20"))
MAX_FILE_SIZE_MB = float(os.getenv("MAX_FILE_SIZE_MB", "5.0"))

# ============================================================================
# GRAPH ANALYSIS (CRITICAL FOR ACCURACY)
# ============================================================================
GRAPH_ENABLED = os.getenv("GRAPH_ENABLED", "false").lower() == "true"
GRAPH_MAX_FILES = int(os.getenv("GRAPH_MAX_FILES", "5000"))

GRAPH_LAZY_LOADING = os.getenv("GRAPH_LAZY_LOADING", "false").lower() == "true"  # Disabled for better prioritization
GRAPH_MIN_CANDIDATES = int(os.getenv("GRAPH_MIN_CANDIDATES", "10"))

# ============================================================================
# CONTEXT LENGTH (LLM QUALITY)
# ============================================================================
MAX_CONTEXT_LENGTH = int(os.getenv("MAX_CONTEXT_LENGTH", "131072"))  # 128k for large repo categorization
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "8192"))  # Max tokens for LLM completion

# ============================================================================
# LLM CATEGORIZATION BATCHING
# ============================================================================
# Files threshold above which to use batched categorization
LLM_CATEGORIZATION_BATCH_THRESHOLD = int(os.getenv("LLM_CATEGORIZATION_BATCH_THRESHOLD", "800"))

# Number of files per batch during categorization phase
LLM_CATEGORIZATION_BATCH_SIZE = int(os.getenv("LLM_CATEGORIZATION_BATCH_SIZE", "600"))

# Maximum files for LLM categorization (skip LLM if repo exceeds this, use YAML-only fallback)
LLM_CATEGORIZATION_MAX_FILES = int(os.getenv("LLM_CATEGORIZATION_MAX_FILES", "5000"))

# ============================================================================
# LLM SETTINGS (QUALITY CONTROL)
# ============================================================================
TEMPERATURE = None  # Deterministic (no randomness)

NO_TEMPERATURE_MODELS = {"gpt-5-nano-2025-08-07", "gpt-5-mini", "gpt-5"}


def SEND_TEMPERATURE(model_name: str) -> bool:
    """Determine if model supports temperature parameter."""
    if TEMPERATURE is None:
        return False
    return not any(model_name.startswith(banned) for banned in NO_TEMPERATURE_MODELS)


FEW_SHOT_EXAMPLES = int(os.getenv("FEW_SHOT_EXAMPLES", "3"))
MAX_TOOL_CALLS = int(os.getenv("MAX_TOOL_CALLS", "5"))
TOOL_CONTEXT_MESSAGES = int(os.getenv("TOOL_CONTEXT_MESSAGES", "5"))

# ============================================================================
# STATISTICAL ANALYSIS (UNCERTAINTY QUANTIFICATION)
# ============================================================================
MIN_EVIDENCE_FOR_CI = int(os.getenv("MIN_EVIDENCE_FOR_CI", "3"))
BOOTSTRAP_SAMPLES = int(os.getenv("BOOTSTRAP_SAMPLES", "1500"))
CONFIDENCE_INTERVAL_LEVEL = float(os.getenv("CONFIDENCE_INTERVAL_LEVEL", "0.95"))

# ============================================================================
# VECTOR DATABASE (SEMANTIC SEARCH QUALITY)
# ============================================================================
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "microservice_patterns_classifier")
CHUNK_SIZE_CHARS = int(os.getenv("CHUNK_SIZE_CHARS", "2000"))
MAX_EMBEDDING_CACHE_SIZE = int(os.getenv("MAX_EMBEDDING_CACHE_SIZE", "3000"))
# Embedding batch size for 8GB VRAM GPU
EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "6"))
MAX_FILE_CONTENT_CHARS = int(os.getenv("MAX_FILE_CONTENT_CHARS", "50000"))  # ~1,250 lines - send whole files

# ============================================================================
# OUTPUT / DEBUG
# ============================================================================
VERBOSE_MODE = os.getenv("VERBOSE_MODE", "true").lower() == "true"
DEBUG_SHOW_PROGRESS = os.getenv("DEBUG_SHOW_PROGRESS", "true").lower() == "true"

# ============================================================================
# FILE CONTENT CACHE (PERFORMANCE OPTIMIZATION)
# ============================================================================
FILE_CACHE_ENABLED = os.getenv("FILE_CACHE_ENABLED", "true").lower() == "true"
FILE_CACHE_SIZE_MB = int(os.getenv("FILE_CACHE_SIZE_MB", "2000"))
FILE_CACHE_CLEAR_PER_PATTERN = os.getenv("FILE_CACHE_CLEAR_PER_PATTERN", "false").lower() == "true"

# ============================================================================
# FILE EXCLUSION PATTERNS
# ============================================================================
EXCLUDED_PATHS = [
    # Version control
    "**/.git/**",
    "**/.svn/**",
    "**/.hg/**",
    # IDE/Editor
    "**/.vscode/**",
    "**/.idea/**",
    "**/.project/**",
    "**/.settings/**",
    "**/*.code-workspace",
    # Dependencies
    "**/node_modules/**",
    "**/bower_components/**",
    "**/vendor/**",
    # Build outputs
    "**/dist/**",
    "**/build/**",
    "**/target/**",
    "**/bin/**",
    "**/obj/**",
    "**/__pycache__/**",
    "**/*.egg-info/**",
    # Logs and temp files
    "**/*.log",
    "**/logs/**",
    "**/*.tmp",
    "**/*.swp",
    "**/*.swo",
    # Media files
    "**/*.png",
    "**/*.jpg",
    "**/*.jpeg",
    "**/*.gif",
    "**/*.svg",
    "**/*.ico",
    "**/*.webp",
    # Documents
    "**/*.pdf",
    "**/*.doc",
    "**/*.docx",
    "**/*.xls",
    "**/*.xlsx",
    "**/*.ppt",
    "**/*.pptx",
    # Archives
    "**/*.zip",
    "**/*.tar",
    "**/*.gz",
    "**/*.rar",
    "**/*.7z",
    "**/*.jar",
    "**/*.war",
    "**/*.ear",
    # Video/Audio
    "**/*.mp3",
    "**/*.mp4",
    "**/*.avi",
    "**/*.mov",
    "**/*.flv",
    "**/*.wmv",
    # Fonts
    "**/*.eot",
    "**/*.ttf",
    "**/*.woff",
    "**/*.woff2",
    # Binaries
    "**/*.dll",
    "**/*.exe",
    "**/*.so",
    # Hidden files
    "**/.*",
    # Lock files
    "**/package-lock.json",
    "**/yarn.lock",
    "**/composer.lock",
    "**/Gemfile.lock",
    "**/Pipfile.lock",
    "**/poetry.lock",
    # Minified/generated
    "**/*.min.js",
    "**/*.min.css",
    "**/*.map",
    "**/*.bundle.js",
    "**/*.chunk.js",
    "**/*-lock.json",
    "**/*.generated.*",
    "**/*.pb.go",
    "**/*_pb2.py",
    "**/*.d.ts",
]

# ============================================================================
# ADVANCED FEATURES (EXPERIMENTAL)
# ============================================================================

# Negative Evidence Tracking (reduce false positives)
TRACK_NEGATIVE_EVIDENCE = os.getenv("TRACK_NEGATIVE_EVIDENCE", "true").lower() == "true"
MAX_NEGATIVE_EVIDENCE_SAMPLES = int(os.getenv("MAX_NEGATIVE_EVIDENCE_SAMPLES", "10"))

# ============================================================================
# VALIDATION
# ============================================================================


def _validate_weight_sum() -> list:
    """Validate priority weights sum to ~1.0."""
    errors = []

    # Validate main priority weights
    priority_sum = (
        PRIORITY_KEYWORD_WEIGHT
        + PRIORITY_EMBEDDING_WEIGHT
        + PRIORITY_GRAPH_WEIGHT
        + PRIORITY_LLM_WEIGHT
    )
    if not (0.98 <= priority_sum <= 1.02):
        errors.append(f"Priority weights sum to {priority_sum:.3f}, should be ~1.0")

    # Validate parser weights (internal distribution)
    parser_sum = (
        PARSER_CENTRALITY_WEIGHT
        + PARSER_DECORATOR_WEIGHT
        + PARSER_STRING_WEIGHT
        + PARSER_CLASS_WEIGHT
    )
    if not (0.98 <= parser_sum <= 1.02):
        errors.append(f"Parser weights sum to {parser_sum:.3f}, should be ~1.0")

    return errors


def _validate_thresholds() -> list:
    """Validate threshold ordering."""
    errors = []
    if not (HIGH_PRIORITY_THRESHOLD > MEDIUM_PRIORITY_THRESHOLD > MIN_PRIORITY_SCORE):
        errors.append("Threshold ordering invalid: HIGH > MEDIUM > MIN required")
    return errors


def _validate_paths() -> list:
    """Validate required paths exist."""
    errors = []
    if not TARGET_REPO_PATH.exists():
        errors.append(f"TARGET_REPO_PATH does not exist: {TARGET_REPO_PATH}")
    if not PATTERNS_DIR_PATH.exists():
        errors.append(f"PATTERNS_DIR_PATH does not exist: {PATTERNS_DIR_PATH}")
    return errors


def _validate_judge_threshold() -> list:
    """Validate judge confidence threshold."""
    errors = []
    if not (0 <= JUDGE_CONFIDENCE_THRESHOLD <= 10):
        errors.append("JUDGE_CONFIDENCE_THRESHOLD must be 0-10")
    return errors


def validate_configuration():
    """Validate configuration values at startup."""
    errors = []
    errors.extend(_validate_weight_sum())
    errors.extend(_validate_thresholds())
    errors.extend(_validate_paths())
    errors.extend(_validate_judge_threshold())

    if errors:
        print("\n❌ CONFIGURATION ERRORS:")
        for error in errors:
            print(f"  • {error}")
        raise ValueError("Invalid configuration - see errors above")


# Auto-validate on import (can be disabled with env var)
if os.getenv("SKIP_CONFIG_VALIDATION", "").lower() != "true":
    try:
        validate_configuration()
    except ValueError:
        raise

# ============================================================================
# CONFIGURATION SUMMARY (for logging)
# ============================================================================


def get_config_summary():
    """Get configuration summary for logging/reproducibility."""
    return {
        "ai_provider": AI_PROVIDER,
        "weight_scheme": WEIGHT_SCHEME,
        "experiment": {
            "run_number": RUN_NUMBER,
        },
        "models": {
            "planner": PLANNER_MODEL,
            "investigator": INVESTIGATOR_MODEL,
            "judge": JUDGE_MODEL,
            "embedding": EMBEDDING_MODEL,
        },
        "priority_weights": {
            "keyword": PRIORITY_KEYWORD_WEIGHT,
            "embedding": PRIORITY_EMBEDDING_WEIGHT,
            "graph": PRIORITY_GRAPH_WEIGHT,
            "llm": PRIORITY_LLM_WEIGHT,
        },
        "parser_weights": {
            "centrality": PARSER_CENTRALITY_WEIGHT,
            "decorator": PARSER_DECORATOR_WEIGHT,
            "string": PARSER_STRING_WEIGHT,
            "class": PARSER_CLASS_WEIGHT,
        },
        "thresholds": {
            "high_priority": HIGH_PRIORITY_THRESHOLD,
            "medium_priority": MEDIUM_PRIORITY_THRESHOLD,
            "min_priority_score": MIN_PRIORITY_SCORE,
            "judge_confidence": JUDGE_CONFIDENCE_THRESHOLD,
        },
        "analysis_budget": {
            "max_files_per_pattern": MAX_FILES_PER_PATTERN,
            "files_per_batch": FILES_PER_BATCH,
            "max_file_size_mb": MAX_FILE_SIZE_MB,
        },
        "graph": {"enabled": GRAPH_ENABLED, "max_files": GRAPH_MAX_FILES},
        "reproducibility": {"random_seed": RANDOM_SEED, "temperature": TEMPERATURE},
    }
