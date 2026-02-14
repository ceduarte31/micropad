# prompt_builder.py - COMPLETE FILE with SHA256 hashing

import hashlib
import json
from datetime import datetime
from typing import Any, Dict, Tuple

from micropad.config import settings as config

# ✅ VERSION: Update this whenever prompts change
PROMPT_VERSION = "v1.0_2025-01-16"


def get_prompt_hash(prompt_text: str) -> str:
    """
    Generate SHA256 hash of prompt for reproducibility tracking.

    Args:
        prompt_text: The prompt string to hash

    Returns:
        First 16 characters of SHA256 hash (sufficient for uniqueness)
    """
    return hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()[:16]


class PromptBuilder:
    """
    Centralized prompt construction with version tracking and SHA256 hashing.

    All prompts are hashed to enable reproducibility verification:
    - Detects prompt drift between runs
    - Enables prompt versioning in reports
    - Allows verification that prompts haven't changed mid-experiment
    """

    @staticmethod
    def build_investigation_prompt(
        pattern_name: str,
        pattern_def: str,
        evidence: dict,
        enrich: dict,
        repo_summary: str,
        plan: dict,
        examples: list,
    ) -> Tuple[str, str, Dict[str, Any]]:
        """
        Build system + user prompts for file investigation.

        Args:
            pattern_name: Name of the pattern being analyzed
            pattern_def: Authoritative pattern definition
            evidence: Dict containing file evidence (path, content, keywords, etc.)
            enrich: Dict with enrichment data (functions, windows, related files)
            repo_summary: Repository structural summary
            plan: Planner output with conceptual characteristics
            examples: List of positive examples for context

        Returns:
            Tuple of (system_prompt, user_prompt, metadata_dict)
            metadata_dict contains: version, system_hash, user_hash, timestamp
        """

        system_prompt = (
            "You are an expert software architect analyzing code for architectural patterns. "
            "Focus on the ARCHITECTURAL PURPOSE and INTENT, not specific technologies or frameworks. "
            "Treat the pattern definition as authoritative."
        )

        # Build example snippet if available
        ex_text = ""
        if examples:
            ex_text = f"\n\nREFERENCE EXAMPLE (for context only):\n```\n{examples[0][:300]}...\n```"

        user_prompt = f"""
PATTERN: {pattern_name}

AUTHORITATIVE DEFINITION:
{pattern_def}

CONFIDENCE CALIBRATION GUIDE:
• 0.9-1.0: Crystal clear implementation with multiple strong signals
• 0.7-0.8: Strong evidence but missing 1-2 expected characteristics
• 0.5-0.6: Partial implementation OR novel approach with clear purpose alignment
• 0.3-0.4: Weak signals that could be coincidental
• 0.0-0.2: No clear evidence or purpose mismatch

REPOSITORY CONTEXT:
{repo_summary.strip() if repo_summary else '(not available)'}

PLANNER INSIGHTS (guidance, not requirements):
{json.dumps(plan.get('conceptual_characteristics', []), indent=2)}

FILE UNDER ANALYSIS: {evidence.get('file_path')}
PRIORITY SCORE: {evidence.get('priority_score', 0):.3f}
KEYWORDS FOUND: {evidence.get('keywords_found', [])}
ANTI-KEYWORDS: {evidence.get('anti_keywords', [])}

EXTRACTED FUNCTIONS:
{enrich['functions_text']}

RELATED FILES (from graph):
{enrich['related_text']}

KEYWORD CONTEXT WINDOWS:
{enrich['windows_text']}

FILE CONTENT:
{evidence.get('full_file', '')[:config.MAX_FILE_CONTENT_CHARS]}
{ex_text}

YOUR TASK:
1. Determine the PRIMARY architectural purpose this file serves
2. Decide if it constitutes EVIDENCE of the '{pattern_name}' pattern
3. Use the calibration guide above to set your confidence realistically
4. If NOT evidence, explain concisely what's missing or mismatched

IMPORTANT:
- Focus on PURPOSE, not implementation details
- Novel implementations count if they serve the core purpose
- Explain WHAT characteristics match or are missing
- Calibrate confidence using the guide above

Return ONLY valid JSON:
{{
  "is_evidence": true/false,
  "confidence": 0.0-1.0,
  "decision_reasoning": "What characteristics match? What's missing? Why this confidence?",
  "snippet": "≤200 chars of strongest supporting code or key rationale",
  "matches_typical_characteristics": true/false,
  "is_novel_implementation": true/false,
  "architectural_purpose": "concise phrase describing what this file does architecturally",
  "missing_characteristics": ["characteristic from definition that's absent", "..."]
}}
""".strip()

        # ✅ NEW: Hash prompts and create metadata
        metadata = {
            "version": PROMPT_VERSION,
            "system_hash": get_prompt_hash(system_prompt),
            "user_hash": get_prompt_hash(user_prompt),
            "timestamp": datetime.now().isoformat(),
            "prompt_type": "investigation",
        }

        return system_prompt, user_prompt, metadata

    @staticmethod
    def build_deliberation_prompt(
        pattern_name: str,
        definition: str,
        reports: list,
        repo_summary: str,
        plan: dict,
        positive_examples: list,
        negative_examples: list,
    ) -> Tuple[str, str, Dict[str, Any]]:
        """
        Build prompts for final deliberation (Judge phase).

        Args:
            pattern_name: Pattern being judged
            definition: Authoritative pattern definition
            reports: List of investigation verdicts
            repo_summary: Repository structural summary
            plan: Planner output
            positive_examples: List of positive code examples
            negative_examples: List of negative/anti-pattern examples

        Returns:
            Tuple of (system_prompt, user_prompt, metadata_dict)
        """

        # Sort reports by confidence (highest first) to combat "lost in the middle"
        sorted_reports = sorted(reports, key=lambda r: r.get('confidence', 0), reverse=True)

        # Build evidence summary
        evidence_summary = "\n\n".join(
            [
                f"{i+1}. {r.get('file_path')} (confidence={r.get('confidence', 0):.2f})\n"
                f"   Purpose: {r.get('architectural_purpose', 'N/A')}\n"
                f"   Reasoning: {r.get('decision_reasoning', '')[:220]}\n"
                f"   Missing: {', '.join(r.get('missing_characteristics', [])) or 'None noted'}"
                for i, r in enumerate(sorted_reports)
            ]
        )

        # Extract negative evidence if present
        negative_evidence = []
        if reports and "_negative_evidence" in reports[0]:
            negative_evidence = reports[0]["_negative_evidence"]

        # Build negative evidence summary
        negative_summary = ""
        if negative_evidence:
            from pathlib import Path

            negative_summary = "\n\nREJECTED FILES (What this pattern is NOT):\n"
            negative_summary += "\n".join(
                [
                    f"• {Path(n['file_path']).name} (score={n['priority_score']:.2f}): {n['rejection_reason'][:150]}"
                    for n in negative_evidence[:5]
                ]
            )
            negative_summary += f"\n\n({len(negative_evidence)} total rejections - these files had keywords/signals but lacked the core pattern purpose)"

        # Build example texts
        pos_text = ""
        if positive_examples:
            pos_text = f"\n\nPOSITIVE REFERENCE (what it should look like):\n```\n{positive_examples[0][:250]}...\n```"

        neg_text = ""
        if negative_examples:
            neg_text = f"\n\nNEGATIVE REFERENCE (misleading anti-pattern):\n```\n{negative_examples[0][:250]}...\n```"

        system_prompt = (
            "You are a strict architectural pattern judge making final determinations. "
            "Your job is to calibrate confidence realistically based on evidence strength. "
            "Be explicit about what's present vs. what's missing."
        )

        user_prompt = f"""
PATTERN: {pattern_name}

AUTHORITATIVE DEFINITION:
{definition}

REPOSITORY CONTEXT:
{repo_summary.strip()}

PLANNER INSIGHTS:
{json.dumps(plan.get('conceptual_characteristics', []), indent=2)}

EVIDENCE FILES ({len(reports)} files analyzed):
{evidence_summary}
{negative_summary}
{pos_text}
{neg_text}

CALIBRATION REQUIREMENTS (confidence scale 0-10):
• 9-10: ALL core characteristics clearly present, no significant ambiguity
• 7-8: Core characteristics present, minor gaps are acceptable
• 5-6: Partial implementation OR novel approach with clear purpose
• 3-4: Weak signals, substantial missing characteristics
• 0-2: Little to no credible evidence

MANDATORY ANALYSIS:
1. Are ALL core characteristics from the definition present in the evidence?
2. If not, which are missing and why does that matter (or not matter)?
3. Do the REJECTED files show false positive patterns to avoid? (Check negative evidence above)
4. Are there anti-patterns or false signals that weaken confidence?
5. Would an expert architect agree with your confidence level?

YOUR TASK:
Synthesize the evidence and provide a calibrated verdict.

Return ONLY valid JSON:
{{
  "confidence_score": 0-10,
  "synthesis": "One clear paragraph: Does this implementation match the definition? Why/why not?",
  "key_evidence": [
    "file.py: specific characteristic shown",
    "..."
  ],
  "missing_characteristics": [
    "Expected characteristic that's absent or weak",
    "..."
  ],
  "false_positive_risk": "low|medium|high - with brief justification",
  "calibration_note": "Why this specific score? What would raise/lower it?",
  "matches_expected_implementation": true/false,
  "is_novel_approach": true/false
}}
""".strip()

        # ✅ NEW: Hash prompts and create metadata
        metadata = {
            "version": PROMPT_VERSION,
            "system_hash": get_prompt_hash(system_prompt),
            "user_hash": get_prompt_hash(user_prompt),
            "timestamp": datetime.now().isoformat(),
            "prompt_type": "deliberation",
        }

        return system_prompt, user_prompt, metadata

    @staticmethod
    def build_planner_prompt(
        pattern_name: str, description: str, examples: list = None
    ) -> Tuple[str, str, Dict[str, Any]]:
        """
        Build prompts for planner phase.

        Args:
            pattern_name: Pattern to plan for
            description: Pattern description
            examples: Optional list of examples for few-shot learning

        Returns:
            Tuple of (system_prompt, user_prompt, metadata_dict)
        """

        system_prompt = (
            "You are an expert microservices architect. "
            "Produce conceptual (purpose-level) investigative characteristics for an architectural pattern."
        )

        user_prompt = f"""
PATTERN NAME: {pattern_name}
DESCRIPTION:
{description}

TASK:
1. List 4-6 conceptual characteristics (PURPOSE-level, not technology buzzwords).
2. Provide an investigator_prompt focusing on how to recognize PURPOSE in code.
3. Provide a judge_prompt for final synthesis (again, purpose not tech specificity).

Return ONLY JSON:
{{
  "conceptual_characteristics": ["...", "..."],
  "investigator_prompt": "...",
  "judge_prompt": "..."
}}
""".strip()

        # ✅ NEW: Hash prompts and create metadata
        metadata = {
            "version": PROMPT_VERSION,
            "system_hash": get_prompt_hash(system_prompt),
            "user_hash": get_prompt_hash(user_prompt),
            "timestamp": datetime.now().isoformat(),
            "prompt_type": "planner",
        }

        return system_prompt, user_prompt, metadata
