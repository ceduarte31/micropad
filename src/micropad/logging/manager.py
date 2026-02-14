# logging_manager.py - Purpose-driven comprehensive logging
import json
import logging
import traceback
import uuid
from datetime import datetime
from pathlib import Path


def generate_run_id() -> str:
    """Generate unique run identifier."""
    return str(uuid.uuid4())[:8]


# ============================================================================
# CUSTOM FORMATTERS
# ============================================================================


class JSONLineFormatter(logging.Formatter):
    """
    Formats records as single-line JSON for machine parsing.
    Used by: detection.log
    """

    def format(self, record):
        base = {
            "timestamp": self.formatTime(record, datefmt="%Y-%m-%d %H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Merge structured payloads
        if hasattr(record, "extra_payload") and isinstance(record.extra_payload, dict):
            base.update(record.extra_payload)

        # Add exception info if present
        if record.exc_info:
            base["exception"] = self.formatException(record.exc_info)

        return json.dumps(base, ensure_ascii=False)


class ConversationFormatter(logging.Formatter):
    """
    Pretty multi-line JSON for LLM interactions.
    Used by: conversations.log
    """

    def format(self, record):
        timestamp = self.formatTime(record, datefmt="%Y-%m-%d %H:%M:%S")

        if hasattr(record, "conversation_data"):
            # Format as pretty JSON
            data = json.dumps(record.conversation_data, indent=2, ensure_ascii=False)
            header = f"{'='*80}\n{timestamp} - {record.levelname} - LLM Interaction\n{'='*80}"
            return f"{header}\n{data}\n"

        # Fallback to standard formatting
        return f"{timestamp} - {record.levelname} - {record.getMessage()}"


class OperationsFormatter(logging.Formatter):
    """
    Human-readable format with context.
    Used by: operations.log
    """

    def format(self, record):
        timestamp = self.formatTime(record, datefmt="%Y-%m-%d %H:%M:%S.%f")[
            :-3
        ]  # Include milliseconds
        level = f"[{record.levelname:8s}]"

        # Add function/module context
        location = f"{record.filename}:{record.lineno}"

        message = record.getMessage()

        # Format: timestamp [LEVEL] location - message
        formatted = f"{timestamp} {level} {location:30s} - {message}"

        # Add exception if present
        if record.exc_info:
            formatted += f"\n{self.formatException(record.exc_info)}"

        return formatted


# ============================================================================
# LOGGER SETUP
# ============================================================================


def setup_loggers():
    """
    Configure comprehensive logging system with three specialized logs:

    1. operations.log    - Human-readable audit trail (for developers)
    2. conversations.log - LLM interactions (for debugging/analysis)
    3. detection.log     - Structured events (for metrics/post-analysis)
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create log directories
    logs_dir = Path("./.generated/micropad/logs")
    logs_dir.mkdir(exist_ok=True)

    conv_dir = Path("./.generated/micropad/conversations")
    conv_dir.mkdir(exist_ok=True)

    # Clear root logger handlers
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture everything, filter at handler level
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # ========================================================================
    # CONSOLE HANDLER (minimal, user-facing)
    # ========================================================================
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)  # Only warnings/errors to console
    console_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    root_logger.addHandler(console_handler)

    # ========================================================================
    # OPERATIONS LOG - Human-readable audit trail
    # ========================================================================
    # Purpose: Track all major operations, state changes, decisions
    # Audience: Developers debugging issues or auditing runs
    # Format: Timestamped, contextualized, human-readable

    operations_logger = logging.getLogger("events")  # Keep name for compatibility
    operations_logger.setLevel(logging.DEBUG)
    operations_logger.propagate = False  # Don't pass to root

    ops_file = logs_dir / f"operations_{timestamp}.log"
    ops_handler = logging.FileHandler(ops_file, mode="w", encoding="utf-8")
    ops_handler.setLevel(logging.DEBUG)
    ops_handler.setFormatter(OperationsFormatter())
    operations_logger.addHandler(ops_handler)

    # Log session start
    operations_logger.info(f"{'='*80}")
    operations_logger.info(f"Logging session started - Run ID: {timestamp}")
    operations_logger.info(f"Operations log: {ops_file.resolve()}")
    operations_logger.info(f"{'='*80}")

    # ========================================================================
    # CONVERSATIONS LOG - LLM interaction transcript
    # ========================================================================
    # Purpose: Complete record of all LLM requests/responses
    # Audience: Developers analyzing prompt quality, debugging LLM issues
    # Format: Pretty JSON with full context

    conversations_logger = logging.getLogger("conversations")
    conversations_logger.setLevel(logging.DEBUG)
    conversations_logger.propagate = False

    conv_file = conv_dir / f"conversations_{timestamp}.log"
    conv_handler = logging.FileHandler(conv_file, mode="w", encoding="utf-8")
    conv_handler.setLevel(logging.DEBUG)
    conv_handler.setFormatter(ConversationFormatter())
    conversations_logger.addHandler(conv_handler)

    conversations_logger.info(
        "LLM conversation logging started",
        extra={
            "conversation_data": {"session_id": timestamp, "start_time": datetime.now().isoformat()}
        },
    )

    # ========================================================================
    # DETECTION LOG - Structured event stream
    # ========================================================================
    # Purpose: Machine-readable events for metrics, analysis, evaluation
    # Audience: Automated tools, metrics dashboards, research analysis
    # Format: JSON Lines (one JSON object per line)

    detection_logger = logging.getLogger("detection")
    detection_logger.setLevel(logging.INFO)
    detection_logger.propagate = False

    detect_file = logs_dir / f"detection_{timestamp}.log"
    detect_handler = logging.FileHandler(detect_file, mode="w", encoding="utf-8")
    detect_handler.setLevel(logging.INFO)
    detect_handler.setFormatter(JSONLineFormatter())
    detection_logger.addHandler(detect_handler)

    # Log session metadata
    detection_logger.info(
        "session_start",
        extra={
            "extra_payload": {
                "event": "session_start",
                "session_id": timestamp,
                "start_time": datetime.now().isoformat(),
            }
        },
    )

    # ========================================================================
    # SILENCE NOISY LIBRARIES
    # ========================================================================
    for noisy in ("httpx", "ollama", "sentence_transformers", "urllib3", "chromadb"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    # ========================================================================
    # PRINT SUMMARY
    # ========================================================================
    from micropad.logging.ui import Colors, print_dim, print_info

    print(f"\n{Colors.BOLD}Logging Configuration:{Colors.END}")
    print(f"{Colors.DIM}{'─' * 80}{Colors.END}")
    print(f"  {Colors.GREEN}✓{Colors.END} Operations:    {ops_file.resolve()}")
    print(f"    {Colors.DIM}Purpose: Human-readable audit trail{Colors.END}")
    print(f"  {Colors.GREEN}✓{Colors.END} Conversations: {conv_file.resolve()}")
    print(f"    {Colors.DIM}Purpose: LLM interaction transcript{Colors.END}")
    print(f"  {Colors.GREEN}✓{Colors.END} Detection:     {detect_file.resolve()}")
    print(f"    {Colors.DIM}Purpose: Structured event stream (JSON Lines){Colors.END}")
    print(f"{Colors.DIM}{'─' * 80}{Colors.END}\n")


# ============================================================================
# HELPER FUNCTIONS FOR STRUCTURED LOGGING
# ============================================================================


def log_operation(logger: logging.Logger, operation: str, **kwargs):
    """Log a structured operation event."""
    logger.info(f"Operation: {operation}", extra={"extra_payload": kwargs})


def log_llm_request(
    logger: logging.Logger,
    run_id: str,
    provider: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    **kwargs,
):
    """Log LLM request with full context."""
    logger.info(
        "LLM Request",
        extra={
            "conversation_data": {
                "run_id": run_id,
                "provider": provider,
                "model": model,
                "system_prompt": system_prompt,
                "user_prompt": user_prompt[:2000],  # Truncate for readability
                **kwargs,
            }
        },
    )


def log_llm_response(
    logger: logging.Logger,
    run_id: str,
    provider: str,
    model: str,
    response: str,
    success: bool = True,
    **kwargs,
):
    """Log LLM response."""
    logger.info(
        "LLM Response",
        extra={
            "conversation_data": {
                "run_id": run_id,
                "provider": provider,
                "model": model,
                "response": response[:2000] if isinstance(response, str) else str(response)[:2000],
                "success": success,
                **kwargs,
            }
        },
    )


def log_llm_error(logger: logging.Logger, run_id: str, provider: str, model: str, error: Exception):
    """Log LLM error with full traceback."""
    logger.error(
        "LLM Error",
        extra={
            "conversation_data": {
                "run_id": run_id,
                "provider": provider,
                "model": model,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "traceback": traceback.format_exc(),
            }
        },
    )
