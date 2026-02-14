# ui_output.py - Sleek, informative UI with progress tracking
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# ui_output.py - ADD these new color constants to the Colors class


class Colors:
    """ANSI color codes for terminal output."""

    # Basic colors
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    MAGENTA = "\033[95m"
    WHITE = "\033[97m"

    # Style
    BOLD = "\033[1m"
    DIM = "\033[2m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"
    GRAY = "\033[90m"

    # Phase-specific colors (NEW)
    PHASE_DISCOVERY = "\033[96m"  # Cyan - for repository/file discovery
    PHASE_GRAPH = "\033[94m"  # Blue - for graph construction
    PHASE_ANALYSIS = "\033[95m"  # Magenta - for pattern analysis
    PHASE_REPORT = "\033[92m"  # Green - for report generation

    # Background colors
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_RED = "\033[41m"
    BG_MAGENTA = "\033[45m"

    PHASE_DISCOVERY = "\033[96m"  # Cyan - for repository/file discovery
    PHASE_GRAPH = "\033[94m"  # Blue - for graph construction
    PHASE_ANALYSIS = "\033[95m"  # Magenta - for pattern analysis
    PHASE_REPORT = "\033[92m"  # Green - for report generation


def _bar(width=80, char="─"):
    """Create a horizontal line."""
    return char * width


def _box_top(width=80):
    """Create box top border."""
    return f"╭{'─' * (width-2)}╮"


def _box_bottom(width=80):
    """Create box bottom border."""
    return f"╰{'─' * (width-2)}╯"


def _box_line(text: str, width=80):
    """Create a line inside a box."""
    padding = width - len(text) - 4
    return f"│ {text}{' ' * padding} │"


# ============================================================================
# BANNER & SECTIONS
# ============================================================================


def print_banner():
    """Print application banner."""
    width = 80
    print(f"\n{Colors.CYAN}{_box_top(width)}{Colors.END}")
    print(f"{Colors.CYAN}{_box_line('', width)}{Colors.END}")
    print(
        f"{Colors.CYAN}│{Colors.END} {Colors.BOLD}{Colors.CYAN}{'Microservices Architecture Pattern Scanner':^76}{Colors.END} {Colors.CYAN}│{Colors.END}"
    )
    print(
        f"{Colors.CYAN}{_box_line('Deterministic AI-Powered Pattern Detection', width)}{Colors.END}"
    )
    print(f"{Colors.CYAN}{_box_line('', width)}{Colors.END}")
    print(f"{Colors.CYAN}{_box_bottom(width)}{Colors.END}\n")


def print_section(title: str, subtitle: str = None, phase_color: str = Colors.BLUE):
    """Print a major section header with phase-specific color."""
    print(f"\n{Colors.BOLD}{phase_color}{'━' * 80}{Colors.END}")
    print(f"{Colors.BOLD}{phase_color}▶ {title.upper()}{Colors.END}")
    if subtitle:
        print(f"{Colors.DIM}{phase_color}  {subtitle}{Colors.END}")
    print(f"{phase_color}{'━' * 80}{Colors.END}\n")


def print_step(step_num: int, total_steps: int, description: str, details: str = None):
    """Print a numbered step with optional details."""
    step_label = f"[{step_num}/{total_steps}]"
    print(f"\n{Colors.BOLD}{Colors.CYAN}{step_label} {description}{Colors.END}")
    if details:
        print(f"{Colors.DIM}      {details}{Colors.END}")
    print(f"{Colors.GRAY}{'─' * 80}{Colors.END}")


# ============================================================================
# STATUS MESSAGES
# ============================================================================


def print_info(msg: str, indent=0, icon="•"):
    """Print informational message."""
    prefix = "  " * indent
    print(f"{prefix}{Colors.BLUE}{icon}{Colors.END} {msg}")


def print_success(msg: str, indent=0):
    """Print success message."""
    prefix = "  " * indent
    print(f"{prefix}{Colors.GREEN}✓{Colors.END} {msg}")


def print_warning(msg: str, indent=0):
    """Print warning message."""
    prefix = "  " * indent
    print(f"{prefix}{Colors.YELLOW}⚠{Colors.END} {msg}")


def print_error(msg: str, indent=0):
    """Print error message."""
    prefix = "  " * indent
    print(f"{prefix}{Colors.RED}✗{Colors.END} {msg}")


def print_dim(msg: str, indent=0):
    """Print dimmed/secondary information."""
    prefix = "  " * indent
    print(f"{prefix}{Colors.DIM}{msg}{Colors.END}")


def print_highlight(msg: str, indent=0):
    """Print highlighted message."""
    prefix = "  " * indent
    print(f"{prefix}{Colors.BOLD}{Colors.CYAN}► {msg}{Colors.END}")


# ============================================================================
# CONFIGURATION DISPLAY
# ============================================================================


def print_config_summary(config_dict: dict):
    """Print formatted configuration summary."""
    print(f"\n{Colors.BOLD}Configuration:{Colors.END}")
    print(f"{Colors.DIM}{'─' * 80}{Colors.END}")

    # Repository
    print(f"  {Colors.CYAN}Repository:{Colors.END}")
    print(f"    • Target: {Colors.BOLD}{config_dict.get('repo_path', 'Unknown')}{Colors.END}")
    print(f"    • Patterns: {config_dict.get('patterns_dir', 'Unknown')}")

    # Analysis parameters
    print(f"\n  {Colors.CYAN}Analysis Parameters:{Colors.END}")
    print(
        f"    • Random seed: {Colors.BOLD}{config_dict.get('random_seed', 'Not set')}{Colors.END} (deterministic)"
    )
    print(f"    • Max files/pattern: {config_dict.get('max_files_per_pattern', 'N/A')}")
    print(f"    • Judge threshold: {config_dict.get('judge_threshold', 'N/A')}/10")

    # Graph settings
    if "graph_enabled" in config_dict:
        status = (
            f"{Colors.GREEN}Enabled{Colors.END}"
            if config_dict["graph_enabled"]
            else f"{Colors.GRAY}Disabled{Colors.END}"
        )
        print(f"    • Graph analysis: {status}")

    print(f"{Colors.DIM}{'─' * 80}{Colors.END}\n")


# ============================================================================
# PATTERN ANALYSIS PROGRESS
# ============================================================================


def print_pattern_analysis_start(name: str, idx: int, total: int):
    """Print pattern analysis start - uses new separator."""
    print_pattern_separator(name, idx, total)


def print_pattern_phase(phase_name: str, details: str = None):
    """Print pattern analysis phase."""
    print(f"  {Colors.BOLD}⚙ {phase_name}{Colors.END}")
    if details:
        print(f"    {Colors.DIM}{details}{Colors.END}")


# ============================================================================
# FILE ANALYSIS PROGRESS
# ============================================================================


def print_file_analysis(current: int, total: int, filename: str, score: float = None):
    """Print file analysis progress with smooth updates."""
    # Truncate filename if too long
    max_len = 45
    if len(filename) > max_len:
        filename = "..." + filename[-(max_len - 3) :]

    # Calculate progress
    percent = (current / total) * 100 if total > 0 else 0

    # Progress bar
    bar_width = 20
    filled = int(bar_width * current / total) if total > 0 else 0
    bar = "█" * filled + "░" * (bar_width - filled)

    # Build output
    score_str = f" | score: {score:.3f}" if score is not None else ""
    output = f"\r  [{current:3d}/{total:3d}] {bar} {percent:5.1f}% │ {filename:<45}{score_str}"

    # Print without newline
    print(output, end="", flush=True)


def clear_line():
    """Clear current line."""
    print("\r" + " " * 120 + "\r", end="", flush=True)


def print_file_result(kind: str, filename: str, confidence: float = None, reasoning: str = None):
    """Print file analysis result."""
    clear_line()

    # Truncate filename
    max_len = 50
    if len(filename) > max_len:
        filename = "..." + filename[-(max_len - 3) :]

    if kind == "evidence":
        conf_str = (
            f" (confidence: {Colors.BOLD}{confidence:.2f}{Colors.END})"
            if confidence is not None
            else ""
        )
        print(f"    {Colors.GREEN}✓ Evidence{Colors.END}: {filename}{conf_str}")
        if reasoning and len(reasoning) < 100:
            print(f"      {Colors.DIM}└─ {reasoning[:80]}...{Colors.END}")
    elif kind == "no_evidence":
        print(f"    {Colors.GRAY}· Rejected{Colors.END}: {filename}")
    else:
        print(f"    {Colors.YELLOW}? Unknown{Colors.END}: {filename}")


# ============================================================================
# ANALYSIS SUMMARIES
# ============================================================================


def print_prioritization_summary(scored_files: list):
    """Print file prioritization summary with distribution."""
    if not scored_files:
        print_warning("No files scored above minimum threshold", indent=1)
        return

    # Calculate distribution
    from config import HIGH_PRIORITY_THRESHOLD, MEDIUM_PRIORITY_THRESHOLD

    high = sum(1 for f in scored_files if f["score"] >= HIGH_PRIORITY_THRESHOLD)
    medium = sum(
        1 for f in scored_files if MEDIUM_PRIORITY_THRESHOLD <= f["score"] < HIGH_PRIORITY_THRESHOLD
    )
    low = len(scored_files) - high - medium

    print(f"  {Colors.CYAN}Priority Distribution:{Colors.END}")
    print(
        f"    {Colors.GREEN}●{Colors.END} High priority:   {high:3d} files  (≥{HIGH_PRIORITY_THRESHOLD:.2f})"
    )
    print(
        f"    {Colors.YELLOW}●{Colors.END} Medium priority: {medium:3d} files  (≥{MEDIUM_PRIORITY_THRESHOLD:.2f})"
    )
    print(f"    {Colors.GRAY}●{Colors.END} Low priority:    {low:3d} files")
    print(
        f"    {Colors.BLUE}Σ{Colors.END} Total:          {Colors.BOLD}{len(scored_files):3d}{Colors.END} files"
    )


def print_pass_summary(files_analyzed: int, evidence_count: int, pass_label: str):
    """Print analysis pass summary."""
    clear_line()

    if evidence_count > 0:
        print(
            f"\n  {Colors.GREEN}✓{Colors.END} {Colors.BOLD}{pass_label.capitalize()} pass complete:{Colors.END} "
            f"{Colors.BOLD}{evidence_count}{Colors.END} evidence found in {files_analyzed} files analyzed"
        )
    else:
        print(
            f"\n  {Colors.GRAY}○{Colors.END} {pass_label.capitalize()} pass complete: "
            f"No evidence found ({files_analyzed} files analyzed)"
        )


# ============================================================================
# DELIBERATION & VERDICT
# ============================================================================


def print_deliberation_start(evidence_count: int):
    """Print deliberation start."""
    print(f"\n  {Colors.BOLD}{Colors.CYAN}⚖  Final Deliberation{Colors.END}")
    print(f"     {Colors.DIM}Synthesizing evidence from {evidence_count} files...{Colors.END}")


def print_pattern_detected(
    pattern: str, confidence: int, evidence_count: int, risk: str = None, ci: dict = None
):
    """Print pattern detected verdict with confidence interval."""
    # Confidence bar
    conf_bar_width = 10
    filled = int(conf_bar_width * confidence / 10)
    conf_bar = "█" * filled + "░" * (conf_bar_width - filled)

    # Risk indicator
    risk_color = Colors.GREEN
    if risk and risk.lower() == "high":
        risk_color = Colors.RED
    elif risk and risk.lower() == "medium":
        risk_color = Colors.YELLOW

    print(f"\n  {Colors.GREEN}{Colors.BOLD}✓ PATTERN DETECTED{Colors.END}")
    print(f"    Pattern: {Colors.BOLD}{Colors.CYAN}{pattern}{Colors.END}")
    print(f"    Confidence: [{conf_bar}] {Colors.BOLD}{confidence}/10{Colors.END}")

    # ✅ NEW: Show confidence interval
    if ci:
        ci_width = ci.get("interval_width", 0)

        # Visual indicator for interval width (narrower = more certain)
        if ci_width < 0.15:
            ci_quality = f"{Colors.GREEN}●{Colors.END} Narrow"
        elif ci_width < 0.30:
            ci_quality = f"{Colors.YELLOW}●{Colors.END} Moderate"
        else:
            ci_quality = f"{Colors.RED}●{Colors.END} Wide"

        print(f"    CI 95%: [{ci['lower_bound']:.2f}, {ci['upper_bound']:.2f}] {ci_quality}")

    print(f"    Evidence: {evidence_count} files")
    if risk:
        print(f"    False positive risk: {risk_color}{risk.upper()}{Colors.END}")


def print_pattern_not_detected(pattern: str, reason: str = None, evidence_count: int = 0):
    """Print pattern not detected verdict."""
    print(f"\n  {Colors.GRAY}○ Pattern not detected{Colors.END}")
    print(f"    Pattern: {Colors.DIM}{pattern}{Colors.END}")
    if reason:
        print(f"    Reason: {Colors.DIM}{reason}{Colors.END}")
    if evidence_count > 0:
        print(
            f"    {Colors.DIM}({evidence_count} files examined but insufficient confidence){Colors.END}"
        )


# ============================================================================
# FINAL SUMMARY
# ============================================================================


def print_final_summary(detected: Dict, total_patterns: int, duration: float):
    """Print comprehensive final summary."""
    print_section("SCAN COMPLETE", f"Finished in {duration:.1f}s")

    # Statistics box
    detection_rate = (len(detected) / total_patterns * 100) if total_patterns > 0 else 0

    print(f"{Colors.BOLD}Summary:{Colors.END}")
    print(f"  • Patterns analyzed: {Colors.BOLD}{total_patterns}{Colors.END}")
    print(
        f"  • Patterns detected: {Colors.BOLD}{Colors.GREEN}{len(detected)}{Colors.END} ({detection_rate:.0f}%)"
    )
    print(f"  • Duration: {Colors.BOLD}{duration:.1f}s{Colors.END}")
    print(f"  • Avg time/pattern: {Colors.DIM}{duration/total_patterns:.1f}s{Colors.END}")

    if detected:
        print(f"\n{Colors.BOLD}Detected Patterns:{Colors.END}")
        print(f"{Colors.DIM}{'─' * 80}{Colors.END}")

        for i, (pattern_name, data) in enumerate(sorted(detected.items()), start=1):
            synthesis = data.get("synthesis", {})
            confidence = synthesis.get("confidence_score", 0)
            evidence_files = len(data.get("evidence_files", []))
            risk = synthesis.get("false_positive_risk", "unknown")

            # Confidence indicator
            if confidence >= 8:
                conf_icon = f"{Colors.GREEN}●{Colors.END}"
            elif confidence >= 6:
                conf_icon = f"{Colors.YELLOW}●{Colors.END}"
            else:
                conf_icon = f"{Colors.RED}●{Colors.END}"

            print(f"  {i:2d}. {conf_icon} {Colors.BOLD}{pattern_name}{Colors.END}")
            print(
                f"       Confidence: {confidence}/10 │ Evidence: {evidence_files} files │ Risk: {risk}"
            )

            # Show top evidence file
            if evidence_files > 0:
                top_evidence = data["evidence_files"][0]
                top_file = Path(top_evidence.get("file_path", "")).name
                print(f"       {Colors.DIM}Top evidence: {top_file}{Colors.END}")

        print(f"{Colors.DIM}{'─' * 80}{Colors.END}")
    else:
        print(f"\n{Colors.YELLOW}No patterns detected in this repository.{Colors.END}")
        print(f"{Colors.DIM}This may indicate:{Colors.END}")
        print(f"{Colors.DIM}  • Repository doesn't implement these patterns{Colors.END}")
        print(f"{Colors.DIM}  • Pattern definitions need refinement{Colors.END}")
        print(f"{Colors.DIM}  • Detection thresholds are too strict{Colors.END}")


def print_reproducibility_info(metadata: dict):
    """Print reproducibility information."""
    print(f"\n{Colors.BOLD}Reproducibility:{Colors.END}")
    print(f"{Colors.DIM}{'─' * 80}{Colors.END}")

    print(f"  • Random seed: {Colors.BOLD}{metadata.get('random_seed', 'N/A')}{Colors.END}")
    print(
        f"  • Repository fingerprint: {Colors.DIM}{metadata.get('repository', {}).get('fingerprint', 'N/A')}{Colors.END}"
    )
    print(f"  • Graph analysis: {metadata.get('graph', {}).get('enabled', False)}")
    print(
        f"  • Environment: Python {metadata.get('environment', {}).get('python_version', 'unknown').split()[0]}"
    )

    model_versions = metadata.get("model_versions", {})
    if model_versions:
        print(f"  • Models captured: {len(model_versions)} versions")

    print(f"\n  {Colors.CYAN}To reproduce this scan:{Colors.END}")
    print(
        f"    {Colors.DIM}1. Use same repository state (fingerprint: {metadata.get('repository', {}).get('fingerprint', 'N/A')[:12]}...){Colors.END}"
    )
    print(f"    {Colors.DIM}2. Set RANDOM_SEED={metadata.get('random_seed', 'N/A')}{Colors.END}")
    print(f"    {Colors.DIM}3. Use same model versions (see report metadata){Colors.END}")
    print(f"    {Colors.DIM}4. Run: python scanner.py{Colors.END}")


# ============================================================================
# PROGRESS SPINNERS & INDICATORS
# ============================================================================


class ProgressSpinner:
    """Animated spinner for long-running operations."""

    def __init__(self, message: str):
        self.message = message
        self.frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.current_frame = 0
        self.running = False

    def start(self):
        """Start spinner animation."""
        self.running = True
        self._print_frame()

    def stop(self, final_message: str = None):
        """Stop spinner and print final message."""
        self.running = False
        clear_line()
        if final_message:
            print(final_message)

    def _print_frame(self):
        """Print current frame."""
        if self.running:
            frame = self.frames[self.current_frame % len(self.frames)]
            print(f"\r  {Colors.CYAN}{frame}{Colors.END} {self.message}...", end="", flush=True)
            self.current_frame += 1


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins}m {secs}s"
    else:
        hours = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        return f"{hours}h {mins}m"


def format_file_size(bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ["B", "KB", "MB", "GB"]:
        if bytes < 1024:
            return f"{bytes:.1f}{unit}"
        bytes /= 1024
    return f"{bytes:.1f}TB"


def check_gpu_vram():
    """Check and display GPU/VRAM availability."""
    try:
        import torch

        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            total_vram = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            allocated = torch.cuda.memory_allocated(0) / (1024**3)
            cached = torch.cuda.memory_reserved(0) / (1024**3)

            print_success(f"GPU detected: {gpu_name}")
            print_dim(f"  • Total VRAM: {total_vram:.1f}GB", indent=1)
            print_dim(f"  • Allocated: {allocated:.2f}GB | Cached: {cached:.2f}GB", indent=1)
        else:
            print_warning("No GPU detected - using CPU (slower)")
            print_dim("  • Consider using a GPU for faster embeddings", indent=1)

    except ImportError:
        print_warning("PyTorch not installed - cannot check GPU")
    except Exception as e:
        print_dim(f"  • GPU check failed: {e}", indent=1)


def print_phase_banner(phase_num: int, title: str, color: str, icon: str = "▶"):
    """Print large phase banner with color coding."""
    width = 80
    print(f"\n{color}{'█' * width}{Colors.END}")
    print(
        f"{color}█{Colors.END} {Colors.BOLD}{color}{icon} PHASE {phase_num}: {title.upper()}{Colors.END}"
    )
    print(f"{color}{'█' * width}{Colors.END}\n")


def print_pattern_separator(pattern_name: str, idx: int, total: int):
    """Print prominent pattern separator with progress."""
    width = 80
    percent = (idx / total) * 100

    # Progress bar
    bar_width = 50
    filled = int(bar_width * idx / total)
    bar = "█" * filled + "░" * (bar_width - filled)

    print(f"\n{Colors.MAGENTA}{'─' * width}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.MAGENTA}◆ PATTERN {idx}/{total}: {pattern_name}{Colors.END}")
    print(f"{Colors.DIM}[{bar}] {percent:.0f}% complete{Colors.END}")
    print(f"{Colors.MAGENTA}{'─' * width}{Colors.END}\n")


def print_pattern_complete(
    pattern_name: str,
    detected: bool,
    confidence: int = None,
    evidence_count: int = 0,
    duration: float = 0,
):
    """Print pattern completion summary."""
    if detected:
        icon = f"{Colors.GREEN}✓{Colors.END}"
        status = f"{Colors.GREEN}{Colors.BOLD}DETECTED{Colors.END}"
        details = f"Confidence: {confidence}/10 | Evidence: {evidence_count} files | Time: {duration:.1f}s"
    else:
        icon = f"{Colors.GRAY}○{Colors.END}"
        status = f"{Colors.GRAY}Not detected{Colors.END}"
        details = f"Time: {duration:.1f}s"

    print(f"\n{icon} {Colors.BOLD}{pattern_name}{Colors.END}: {status}")
    print(f"{Colors.DIM}  {details}{Colors.END}")
    print(f"{Colors.MAGENTA}{'─' * 80}{Colors.END}\n")


def print_phase_summary(phase_name: str, duration: float, stats: dict, phase_color: str):
    """Print phase completion summary."""
    print(f"\n{phase_color}{'▬' * 80}{Colors.END}")
    print(f"{Colors.BOLD}{phase_color}✓ {phase_name} Complete ({duration:.1f}s){Colors.END}")

    for key, value in stats.items():
        print(f"{Colors.DIM}  • {key}: {Colors.BOLD}{value}{Colors.END}")

    print(f"{phase_color}{'▬' * 80}{Colors.END}\n")
