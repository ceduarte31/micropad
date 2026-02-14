# llm_helper.py - Robust LLM categorization helpers (ID + path modes)

import json
import logging
import re  # Also add this if not present
from typing import Any, Dict, List, Optional

from micropad.config import settings as config

# ---------- Generic Utilities ----------

# llm_helper.py - IMPROVED JSON extraction


def _extract_json_block(text: str) -> Optional[str]:
    """
    Robust JSON extraction with multiple strategies.
    """
    if not text:
        return None

    text = text.strip()

    # Remove role markers
    if text.lower().startswith("assistant:"):
        text = text.split(":", 1)[1].strip()

    # Strategy 1: Look for ```json fenced block
    if "```json" in text.lower():
        try:
            start = text.lower().find("```json") + 7
            end = text.find("```", start)
            if end != -1:
                candidate = text[start:end].strip()
                if candidate.startswith("{"):
                    return candidate
        except Exception:
            pass

    # Strategy 2: Generic fenced block
    if "```" in text:
        try:
            parts = text.split("```")
            for part in parts[1::2]:  # Every other part (inside fences)
                part = part.strip()
                if part.startswith("json"):
                    part = part[4:].strip()
                if part.startswith("{") and part.endswith("}"):
                    return part
        except Exception:
            pass

    # Strategy 3: Find first JSON object
    try:
        import re

        # Find outermost braces
        match = re.search(r"\{(?:[^{}]|(?:\{[^{}]*\}))*\}", text, re.DOTALL)
        if match:
            return match.group(0)
    except Exception:
        pass

    # Strategy 4: If whole text looks like JSON
    if text.startswith("{") and text.endswith("}"):
        return text

    # Strategy 5: Try to find JSON after common prefixes
    for prefix in ["Here is", "Here's", "The JSON", "Output:"]:
        if prefix in text:
            after = text.split(prefix, 1)[1].strip()
            if after.startswith("{"):
                # Find matching closing brace
                brace_count = 0
                for i, char in enumerate(after):
                    if char == "{":
                        brace_count += 1
                    elif char == "}":
                        brace_count -= 1
                        if brace_count == 0:
                            return after[: i + 1]

    return None


def _safe_json_load(raw: Optional[str]) -> Dict[str, Any]:
    """Load JSON with better error handling."""
    if raw is None:
        return {}

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        # Try to fix common issues
        try:
            # Remove trailing commas (common LLM mistake)
            fixed = re.sub(r",\s*}", "}", raw)
            fixed = re.sub(r",\s*]", "]", fixed)
            return json.loads(fixed)
        except:
            pass

        # Try to extract valid JSON substring
        try:
            # Find first { and last }
            start = raw.find("{")
            end = raw.rfind("}")
            if start != -1 and end != -1 and end > start:
                return json.loads(raw[start : end + 1])
        except:
            pass

        logging.getLogger("events").error(f"JSON parse failed: {str(e)[:100]}")
        return {}


# ---------- Core LLM Call (Single Entry Point) ----------


# llm_helper.py - UPDATE to use config function
def _call_llm_categorizer(prompt: str) -> str:
    model = config.PLANNER_MODEL

    if config.AI_PROVIDER == "openai":
        from openai import OpenAI

        client = OpenAI(api_key=config.OPENAI_API_KEY, base_url=config.OPENAI_BASE_URL)

        kwargs = {"model": model, "messages": [{"role": "user", "content": prompt}]}

        # ✅ USE CONFIG FUNCTION (don't duplicate logic)
        if config.SEND_TEMPERATURE(model):
            kwargs["temperature"] = config.TEMPERATURE

        try:
            resp = client.chat.completions.create(**kwargs)
            return resp.choices[0].message.content or ""
        except Exception as e:
            # Retry without temperature if needed
            if config.SEND_TEMPERATURE(model) and "temperature" in str(e).lower():
                del kwargs["temperature"]
                resp = client.chat.completions.create(**kwargs)
                return resp.choices[0].message.content or ""
            raise
    else:
        import ollama

        response = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            options={"num_ctx": config.MAX_CONTEXT_LENGTH, "cache_prompt": True},
        )
        return response["message"]["content"]


# ---------- Public Categorization Functions ----------

def _split_into_batches(file_list: List[str], batch_size: int) -> List[List[str]]:
    """Split file list into batches of specified size."""
    batches = []
    for i in range(0, len(file_list), batch_size):
        batches.append(file_list[i:i + batch_size])
    return batches


def _batch_review_prompt(
    pattern_name: str,
    pattern_description: str,
    high_hints_text: str,
    low_hints_text: str,
    keywords_text: str,
    anti_keywords_text: str,
    batch_files: str,
    batch_num: int,
    total_batches: int,
) -> str:
    """Generate prompt for batch review phase."""
    return f"""You are reviewing batch {batch_num}/{total_batches} of a repository to identify CANDIDATE files for the "{pattern_name}" architectural pattern.

PATTERN DESCRIPTION:
{pattern_description or 'N/A'}

GUIDANCE PATTERNS (use as INSPIRATION):

HIGH-PRIORITY PATTERNS (files like these are LIKELY relevant):
{high_hints_text}

OTHER PATTERNS (files like these MAY be relevant):
{low_hints_text}

KEYWORDS (indicative terms):
{keywords_text}

ANTI-KEYWORDS (caution flags):
{anti_keywords_text}

FILES IN THIS BATCH (batch {batch_num}/{total_batches}):
{batch_files}

YOUR TASK FOR THIS BATCH:
Identify CANDIDATE files that might be relevant to "{pattern_name}". Don't finalize categorization yet - just flag potential matches.

Be INCLUSIVE - it's better to include questionable files now than miss important ones. You'll make final decisions after reviewing all batches.

Return ONLY valid JSON (no markdown, no explanations):
{{
    "candidates": ["path1.py", "path2.js", ...],
    "reasoning": "Brief note on what patterns you noticed in this batch"
}}
"""


def _final_synthesis_prompt(
    pattern_name: str,
    pattern_description: str,
    high_hints_text: str,
    keywords_text: str,
    all_candidates: List[str],
    total_files_reviewed: int,
    total_batches: int,
) -> str:
    """Generate prompt for final synthesis phase."""
    candidates_text = "\n".join(all_candidates)

    return f"""You reviewed {total_files_reviewed} files across {total_batches} batches for the "{pattern_name}" architectural pattern.

PATTERN DESCRIPTION:
{pattern_description or 'N/A'}

HIGH-PRIORITY PATTERNS:
{high_hints_text}

KEYWORDS:
{keywords_text}

CANDIDATES IDENTIFIED ACROSS ALL BATCHES ({len(all_candidates)} files):
{candidates_text}

YOUR FINAL TASK:
Now categorize these candidates into confidence tiers:

1. HIGH CONFIDENCE - Files that very likely implement or directly support this pattern
   - Strong pattern matches (e.g., *gateway*.py for API Gateway pattern)
   - Multiple relevant keywords in meaningful positions
   - Core architectural components

2. MEDIUM CONFIDENCE - Files that might be relevant or provide supporting context
   - Partial pattern matches
   - Some relevant keywords
   - Related configuration/infrastructure

3. LOW CONFIDENCE - Files with possible tangential relevance
   - Weak signals, helper utilities, or tests

Return ONLY valid JSON (no markdown, no explanations):
{{
    "high_confidence": ["exact/path1.py", ...],
    "medium_confidence": ["exact/path2.js", ...],
    "low_confidence": ["exact/path3.go", ...]
}}
"""


def call_llm_for_categorization(
    file_tree: str, pattern_name: str, pattern_description: str, yaml_hints: Dict[str, List[str]]
) -> dict:
    """
    Multi-turn batched categorization: Review batches → Synthesize final decision.
    Handles large repositories without token limit issues.
    Skips LLM categorization for repos exceeding MAX_FILES threshold.
    """
    logger = logging.getLogger("events")

    # Parse file list early to check threshold
    file_list = [f.strip() for f in file_tree.strip().split('\n') if f.strip()]
    total_files = len(file_list)

    # Check if repo is too large for LLM categorization
    if total_files > config.LLM_CATEGORIZATION_MAX_FILES:
        logger.info(
            f"[{pattern_name}] Repo has {total_files} files (limit: {config.LLM_CATEGORIZATION_MAX_FILES}) - "
            f"skipping LLM categorization, using YAML-only fallback"
        )
        raise ValueError(
            f"Repository exceeds LLM categorization limit ({total_files} > {config.LLM_CATEGORIZATION_MAX_FILES})"
        )

    # Format hints once (shared across all prompts)
    high_globs = yaml_hints.get("high_priority_globs", [])
    low_globs = yaml_hints.get("low_priority_globs", [])
    keywords = yaml_hints.get("keywords", [])
    anti_keywords = yaml_hints.get("anti_keywords", [])

    high_hints_text = (
        "\n".join(f"    • {g}" for g in high_globs)
        if high_globs
        else "    (No high-priority patterns)"
    )
    low_hints_text = (
        "\n".join(f"    • {g}" for g in low_globs[:10]) if low_globs else "    (No other patterns)"
    )
    keywords_text = ", ".join(keywords[:15]) if keywords else "(none)"
    anti_keywords_text = ", ".join(anti_keywords[:10]) if anti_keywords else "(none)"

    # Determine if batching is needed
    if total_files <= config.LLM_CATEGORIZATION_BATCH_THRESHOLD:
        # Small repo - use single-pass categorization
        logger.debug(f"[{pattern_name}] Small repo ({total_files} files) - using single-pass categorization")

        prompt = f"""You are analyzing a repository to identify files relevant to the "{pattern_name}" architectural pattern.

PATTERN DESCRIPTION:
{pattern_description or 'N/A'}

HIGH-PRIORITY PATTERNS:
{high_hints_text}

OTHER PATTERNS:
{low_hints_text}

KEYWORDS: {keywords_text}
ANTI-KEYWORDS: {anti_keywords_text}

REPOSITORY FILES ({total_files} files):
{file_tree}

Categorize files into high/medium/low confidence for "{pattern_name}".

Return ONLY valid JSON:
{{
    "high_confidence": ["path1.py", ...],
    "medium_confidence": ["path2.js", ...],
    "low_confidence": ["path3.go", ...]
}}
"""
        raw = _call_llm_categorizer(prompt)
        data = _safe_json_load(_extract_json_block(raw))

        def norm_paths(lst):
            return [p.strip() for p in lst if isinstance(p, str) and p.strip()]

        return {
            "high_confidence": norm_paths(data.get("high_confidence", [])),
            "medium_confidence": norm_paths(data.get("medium_confidence", [])),
            "low_confidence": norm_paths(data.get("low_confidence", [])),
        }

    # Large repo - use multi-turn batched approach
    logger.info(f"[{pattern_name}] Large repo ({total_files} files) - using batched categorization")

    # Phase 1: Batch Reviews
    batches = _split_into_batches(file_list, config.LLM_CATEGORIZATION_BATCH_SIZE)
    total_batches = len(batches)
    all_candidates = []

    logger.info(f"[{pattern_name}] Phase 1: Reviewing {total_batches} batches...")

    for i, batch in enumerate(batches, 1):
        batch_files_text = "\n".join(batch)

        prompt = _batch_review_prompt(
            pattern_name,
            pattern_description,
            high_hints_text,
            low_hints_text,
            keywords_text,
            anti_keywords_text,
            batch_files_text,
            i,
            total_batches,
        )

        try:
            raw = _call_llm_categorizer(prompt)
            data = _safe_json_load(_extract_json_block(raw))

            candidates = data.get("candidates", [])
            candidates = [c.strip() for c in candidates if isinstance(c, str) and c.strip()]
            all_candidates.extend(candidates)

            logger.debug(
                f"[{pattern_name}] Batch {i}/{total_batches}: {len(candidates)} candidates "
                f"(total so far: {len(all_candidates)})"
            )

        except Exception as e:
            logger.warning(f"[{pattern_name}] Batch {i} failed: {str(e)[:100]}")
            # Continue with remaining batches
            continue

    # Deduplicate candidates
    all_candidates = list(dict.fromkeys(all_candidates))

    logger.info(
        f"[{pattern_name}] Phase 1 complete: {len(all_candidates)} unique candidates "
        f"from {total_files} files ({len(all_candidates)/total_files*100:.1f}%)"
    )

    # Phase 2: Final Synthesis
    if not all_candidates:
        logger.warning(f"[{pattern_name}] No candidates found in any batch")
        return {"high_confidence": [], "medium_confidence": [], "low_confidence": []}

    logger.info(f"[{pattern_name}] Phase 2: Final synthesis of {len(all_candidates)} candidates...")

    prompt = _final_synthesis_prompt(
        pattern_name,
        pattern_description,
        high_hints_text,
        keywords_text,
        all_candidates,
        total_files,
        total_batches,
    )

    try:
        raw = _call_llm_categorizer(prompt)
        data = _safe_json_load(_extract_json_block(raw))

        def norm_paths(lst):
            return [p.strip() for p in lst if isinstance(p, str) and p.strip()]

        result = {
            "high_confidence": norm_paths(data.get("high_confidence", [])),
            "medium_confidence": norm_paths(data.get("medium_confidence", [])),
            "low_confidence": norm_paths(data.get("low_confidence", [])),
        }

        logger.info(
            f"[{pattern_name}] Categorization complete: "
            f"{len(result['high_confidence'])} high, "
            f"{len(result['medium_confidence'])} medium, "
            f"{len(result['low_confidence'])} low"
        )

        return result

    except Exception as e:
        logger.error(f"[{pattern_name}] Final synthesis failed: {str(e)[:100]}")
        # Fallback: treat all candidates as medium confidence
        return {
            "high_confidence": [],
            "medium_confidence": all_candidates,
            "low_confidence": [],
        }
