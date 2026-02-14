# detection_logging.py - Structured event logging for metrics
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional


def _emit(event: str, **payload):
    """
    Emit a structured event to detection log.

    Events are logged as JSON Lines for easy parsing/analysis.
    """
    logger = logging.getLogger("detection")

    event_data = {"event": event, "timestamp": datetime.now().isoformat(), **payload}

    logger.info(f"event:{event}", extra={"extra_payload": event_data})


# ============================================================================
# SESSION EVENTS
# ============================================================================


def log_run_summary(run_id: str, total_patterns: int, detected_patterns: int, **kwargs):
    """Log overall run summary."""
    _emit(
        "run_summary",
        run_id=run_id,
        total_patterns=total_patterns,
        detected_patterns=detected_patterns,
        detection_rate=detected_patterns / total_patterns if total_patterns > 0 else 0.0,
        **kwargs,
    )


def log_session_start(run_id: str, config: Dict[str, Any]):
    """Log session start with configuration."""
    _emit("session_start", run_id=run_id, configuration=config)


def log_session_end(run_id: str, duration: float, success: bool):
    """Log session end."""
    _emit("session_end", run_id=run_id, duration_seconds=duration, success=success)


# ============================================================================
# PATTERN ANALYSIS EVENTS
# ============================================================================


def log_pattern_start(pattern: str, candidate_count: int):
    """Log start of pattern analysis."""
    _emit("pattern_analysis_start", pattern=pattern, candidate_files=candidate_count)


def log_pattern_end(pattern: str, duration: float, evidence_count: int, detected: bool):
    """Log end of pattern analysis."""
    _emit(
        "pattern_analysis_end",
        pattern=pattern,
        duration_seconds=duration,
        evidence_count=evidence_count,
        detected=detected,
    )


# ============================================================================
# FILE SCORING EVENTS
# ============================================================================


def log_file_scored(pattern: str, file: str, score_data: Dict[str, Any]):
    """
    Log file priority scoring.

    Args:
        pattern: Pattern name
        file: File path
        score_data: Dict containing:
            - score: Overall priority score
            - keyword_score: Keyword component
            - embedding_score: Embedding similarity
            - graph_score: Graph centrality
            - llm_score: LLM confidence hint
            - anti_keywords: Count of anti-keywords found
    """
    _emit(
        "file_scored",
        pattern=pattern,
        file=file,
        priority_score=score_data.get("score", 0.0),
        keyword_score=score_data.get("keyword_score", 0.0),
        embedding_score=score_data.get("embedding_score", 0.0),
        graph_score=score_data.get("graph_score", 0.0),
        llm_score=score_data.get("llm_score", 0.0),
        anti_keywords_count=len(score_data.get("anti_keywords", [])),
    )


def log_prioritization_complete(pattern: str, total_scored: int, distribution: Dict[str, int]):
    """Log completion of file prioritization."""
    _emit(
        "prioritization_complete",
        pattern=pattern,
        total_files=total_scored,
        high_priority=distribution.get("high", 0),
        medium_priority=distribution.get("medium", 0),
        low_priority=distribution.get("low", 0),
    )


# ============================================================================
# INVESTIGATION EVENTS
# ============================================================================


def log_investigation_result(pattern: str, verdict: Dict[str, Any]):
    """
    Log file investigation result.

    Args:
        pattern: Pattern name
        verdict: Dict containing:
            - file_path: File analyzed
            - is_evidence: Boolean result
            - confidence: Confidence score
            - decision_reasoning: Explanation
            - snippet: Code snippet
    """
    _emit(
        "file_investigated",
        pattern=pattern,
        file=verdict.get("file_path", "unknown"),
        is_evidence=verdict.get("is_evidence", False),
        confidence=verdict.get("confidence", 0.0),
        reasoning=verdict.get("decision_reasoning", "")[:200],  # Truncate
        snippet=verdict.get("snippet", "")[:160],
    )


def log_evidence(pattern: str, file: str, confidence: float, **kwargs):
    """Log acceptance of evidence file."""
    _emit("evidence_accepted", pattern=pattern, file=file, confidence=confidence, **kwargs)


def log_investigation_phase_complete(
    pattern: str, pass_label: str, files_analyzed: int, evidence_found: int, duration: float
):
    """Log completion of an investigation phase."""
    _emit(
        "investigation_phase_complete",
        pattern=pattern,
        phase=pass_label,
        files_analyzed=files_analyzed,
        evidence_found=evidence_found,
        duration_seconds=duration,
    )


# ============================================================================
# DELIBERATION & VERDICT EVENTS
# ============================================================================


def log_deliberation_start(pattern: str, evidence_count: int):
    """Log start of deliberation."""
    _emit("deliberation_start", pattern=pattern, evidence_count=evidence_count)


def log_verdict(
    pattern: str,
    confidence: int,
    detected: bool,
    evidence_count: int,
    risk: Optional[str] = None,
    **kwargs,
):
    """
    Log final pattern verdict.

    Args:
        pattern: Pattern name
        confidence: Confidence score (0-10)
        detected: Whether pattern was detected
        evidence_count: Number of evidence files
        risk: False positive risk level
        **kwargs: Additional verdict details
    """
    _emit(
        "pattern_verdict",
        pattern=pattern,
        detected=detected,
        confidence_score=confidence,
        evidence_files=evidence_count,
        false_positive_risk=risk,
        **kwargs,
    )


# ============================================================================
# ERROR EVENTS
# ============================================================================


def log_error(context: str, error_type: str, error_message: str, **kwargs):
    """Log error event."""
    _emit("error", context=context, error_type=error_type, error_message=error_message, **kwargs)


def log_warning(context: str, warning_message: str, **kwargs):
    """Log warning event."""
    _emit("warning", context=context, warning_message=warning_message, **kwargs)


# ============================================================================
# PERFORMANCE METRICS
# ============================================================================


def log_performance_metric(operation: str, duration: float, **kwargs):
    """Log performance metric."""
    _emit("performance_metric", operation=operation, duration_seconds=duration, **kwargs)


def log_llm_call(
    run_id: str,
    provider: str,
    model: str,
    operation: str,
    success: bool,
    duration: float,
    tokens: Optional[Dict[str, int]] = None,
):
    """Log LLM API call metrics."""
    _emit(
        "llm_call",
        run_id=run_id,
        provider=provider,
        model=model,
        operation=operation,
        success=success,
        duration_seconds=duration,
        tokens=tokens or {},
    )


# ============================================================================
# GRAPH EVENTS
# ============================================================================


def log_graph_built(nodes: int, edges: int, duration: float):
    """Log graph construction completion."""
    _emit("graph_built", nodes=nodes, edges=edges, duration_seconds=duration)


def log_graph_stats(node_types: Dict[str, int], edge_types: Dict[str, int]):
    """Log graph statistics."""
    _emit("graph_stats", node_types=node_types, edge_types=edge_types)





def log_negative_evidence(pattern: str, file: str, reason: str, priority_score: float):
    """Log rejection of candidate file."""
    _emit(
        "negative_evidence",
        pattern=pattern,
        file=file,
        rejection_reason=reason[:200],  # Truncate
        priority_score=priority_score,
    )
