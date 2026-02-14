import json
import logging
import re
import time  # ✅ Should already be there
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional

import networkx as nx
from sentence_transformers import SentenceTransformer

from micropad.config import settings as config
from micropad.llm.client import LLMClient
from micropad.llm.prompts import PromptBuilder
from micropad.logging.detection import log_investigation_result, log_verdict
from micropad.logging.manager import generate_run_id
from micropad.data.utils import calculate_confidence_interval
from micropad.logging.ui import (  # ✅ ADD THIS LINE
    print_dim,
    print_info,
    print_success,
    print_warning,
)

try:
    from openai import OpenAI
except Exception:
    OpenAI = None  # Only needed if provider=openai


def extract_json_from_response(text: str) -> Optional[dict]:
    """Leniently extract the first JSON object from an LLM response."""
    if not text:
        return None
    # Strip markdown fences
    text = re.sub(r"```json\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"```", "", text)
    # Find first {...}
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


class AIAgent:
    def __init__(self, repo_graph: nx.DiGraph = None, patterns_data: dict = None):
        self.repo_graph = repo_graph
        self.patterns_data = patterns_data or {}
        self.events_log = logging.getLogger("events")
        self.conv_log = logging.getLogger("conversations")

        self.llm_client = LLMClient()

        # ✅ NEW: Track prompt hashes for reproducibility
        self.prompt_hashes = {"planner": [], "investigation": [], "deliberation": []}

    def run_planner(self, pattern_name: str, pattern_data: dict) -> dict:
        """Generate plan with prompt hash tracking and model metadata."""
        print_info(f"Generating analysis plan for '{pattern_name}'...", indent=1)

        start_time = time.time()

        # ✅ UPDATED: Use PromptBuilder with metadata
        from micropad.llm.prompts import PromptBuilder

        description = pattern_data.get("description", "No description provided.")
        system_prompt, user_prompt, prompt_metadata = PromptBuilder.build_planner_prompt(
            pattern_name, description
        )

        # ✅ NEW: Log prompt hash
        self.events_log.debug(
            f"[{pattern_name}] Planner prompt hash: {prompt_metadata['user_hash']} "
            f"(version: {prompt_metadata['version']})"
        )

        # Store for reproducibility report
        self.prompt_hashes["planner"].append({"pattern": pattern_name, **prompt_metadata})

        # ✅ UPDATED: Call LLM and get metadata
        response_text, llm_metadata = self._call_llm(
            config.PLANNER_MODEL, system_prompt, user_prompt, operation=f"planner_{pattern_name}"
        )

        elapsed = time.time() - start_time

        plan = extract_json_from_response(response_text) or {}

        if not plan or "conceptual_characteristics" not in plan:
            print_warning(f"Plan generation failed - using fallback ({elapsed:.1f}s)", indent=2)
            return self._fallback_plan(pattern_name)

        # ✅ NEW: Add metadata to plan
        plan["_llm_metadata"] = llm_metadata
        plan["_prompt_metadata"] = prompt_metadata

        print_success(f"Plan generated ({elapsed:.1f}s)", indent=2)
        print_dim(f"Characteristics: {len(plan.get('conceptual_characteristics', []))}", indent=3)
        print_dim(f"Model: {llm_metadata['model']}", indent=3)

        return plan

    def _fallback_plan(self, pattern_name: str) -> dict:
        """Default plan structure when planner fails."""
        return {
            "conceptual_characteristics": [
                f"Serves the architectural purpose of {pattern_name}",
                "Core conceptual role",
                "Implementation form may vary",
            ],
            "investigator_prompt": f"Determine if code serves {pattern_name} purpose.",
            "judge_prompt": f"Judge if evidence shows {pattern_name} purpose.",
        }

    def call_llm(self, system_prompt: str, user_prompt: str, operation: str) -> dict:
        """
        Call configured LLM provider.

        Returns:
            dict with keys: 'content' (str), 'metadata' (dict)
        """
        return self.llm_client.call_llm(system_prompt, user_prompt, operation)

    def _call_llm(self, model: str, system_prompt: str, user_prompt: str, operation: str) -> tuple:
        """
        Internal wrapper to call LLM client and extract metadata.

        Args:
            model: Model name (currently ignored, determined by operation in client)
            system_prompt: System prompt
            user_prompt: User prompt
            operation: Operation type (planning, investigation, deliberation)

        Returns:
            tuple: (content: str, metadata: dict)
        """
        try:
            # Call the LLM client
            result = self.llm_client.call_llm(system_prompt, user_prompt, operation)

            # Extract metadata and content
            metadata = result["metadata"]
            content = result["content"]

            # Log model info
            self.events_log.info(
                f"[{operation}] {metadata['provider']}/{metadata['model']} | "
                f"Tokens: {metadata['tokens']['total']} | "
                f"Run: {metadata['run_id']}"
            )

            return content, metadata

        except Exception as e:
            self.events_log.error(f"LLM call failed for {operation}: {e}")
            raise

    # --- Example Selection (Static by default) ---
    def _get_relevant_examples_static(
        self, pattern_name: str, example_type: str, n: int
    ) -> List[str]:
        """Static: Just return first n examples."""
        pattern_data = self.patterns_data.get(pattern_name, {})
        examples = pattern_data.get(f"{example_type}_examples", [])
        return examples[:n] if examples else []

    # --- DETERMINISTIC INVESTIGATION ---

    # ai_agent.py - SIMPLIFIED investigation with graceful fallback

    def _prepare_context_enrichments(self, evidence: dict, pattern_name: str) -> dict:
        """Lightweight contextual enrichment (graceful fallback)."""
        try:
            full_content = evidence.get("full_file", "")[:config.MAX_FILE_CONTENT_CHARS]
        except Exception:
            full_content = ""
        lines = full_content.splitlines()

        # Keyword windows
        keywords = evidence.get("keywords_found", []) or []
        windows = []
        if keywords and lines:
            lowered_kw = [k.lower() for k in keywords]
            for idx, line in enumerate(lines):
                if any(k in line.lower() for k in lowered_kw):
                    start = max(0, idx - 2)
                    end = min(len(lines), idx + 3)
                    snippet = "\n".join(lines[start:end]).strip()
                    if snippet and snippet not in windows:
                        windows.append(snippet)
                    if len(windows) >= 5:
                        break
        windows_text = "\n\n---\n".join(windows) if windows else "None"

        # Functions from graph
        functions_text = "(graph unavailable)"
        if (
            self.repo_graph
            and evidence.get("file_path")
            and self.repo_graph.has_node(evidence["file_path"])
        ):
            funcs = []
            for _, succ, data in self.repo_graph.out_edges(evidence["file_path"], data=True):
                if data.get("type") == "defines":
                    node_data = self.repo_graph.nodes.get(succ, {})
                    if node_data.get("type") == "function":
                        name = node_data.get("name")
                        if name:
                            funcs.append(name)
            unique_funcs = sorted(set(funcs))[:10]
            functions_text = "\n".join(unique_funcs) if unique_funcs else "(none)"

        # Related files
        related = []
        if (
            self.repo_graph
            and evidence.get("file_path")
            and self.repo_graph.has_node(evidence["file_path"])
        ):
            for neigh in list(self.repo_graph.neighbors(evidence["file_path"])):
                node_data = self.repo_graph.nodes.get(neigh, {})
                if node_data.get("type") == "file":
                    from pathlib import Path as _P

                    related.append(_P(neigh).name)
                    if len(related) >= 5:
                        break
        related_text = ", ".join(related) if related else "None"

        return {
            "windows_text": windows_text,
            "functions_text": functions_text,
            "related_text": related_text,
        }

    def run_investigation(
        self, evidence: dict, plan: dict, pattern_name: str, repo_summary: str
    ) -> Optional[dict]:
        """Wrapper with graceful enrichment fallback."""
        pattern_data = self.patterns_data.get(pattern_name, {})

        # ✅ GRACEFUL FALLBACK: Don't fail if enrichment breaks
        try:
            enrich = self._prepare_context_enrichments(evidence, pattern_name)
        except Exception as e:
            self.events_log.warning(
                f"Context enrichment failed for {evidence.get('file_path')}: {e}. "
                "Proceeding with minimal context."
            )
            enrich = {
                "windows_text": "(enrichment unavailable)",
                "functions_text": "(enrichment unavailable)",
                "related_text": "(enrichment unavailable)",
            }

        return self._investigate_file(
            evidence, plan, pattern_name, pattern_data, repo_summary, enrich
        )

    def _investigate_file(
        self,
        evidence: dict,
        plan: dict,
        pattern_name: str,
        pattern_data: dict,
        repo_summary: str,
        enrich: dict,
    ) -> Optional[dict]:
        """File investigation with prompt hash tracking and model metadata."""

        # Get pattern definition and examples
        pattern_def = pattern_data.get("description", "No definition provided.")
        examples = pattern_data.get("positive_examples", [])[:1]

        # ✅ UPDATED: Use PromptBuilder with metadata
        from micropad.llm.prompts import PromptBuilder

        system_prompt, user_prompt, prompt_metadata = PromptBuilder.build_investigation_prompt(
            pattern_name, pattern_def, evidence, enrich, repo_summary, plan, examples
        )

        # ✅ NEW: Log prompt hash (only first time per pattern to avoid spam)
        if len(self.prompt_hashes["investigation"]) == 0 or not any(
            p["pattern"] == pattern_name for p in self.prompt_hashes["investigation"]
        ):
            self.events_log.debug(
                f"[{pattern_name}] Investigation prompt hash: {prompt_metadata['user_hash']} "
                f"(version: {prompt_metadata['version']})"
            )

            # Store for reproducibility report
            self.prompt_hashes["investigation"].append({"pattern": pattern_name, **prompt_metadata})

        # Call LLM with error handling
        try:
            # ✅ UPDATED: Get both response and metadata
            response_text, llm_metadata = self._call_llm(
                config.INVESTIGATOR_MODEL,
                system_prompt,
                user_prompt.strip(),
                operation=f"investigate_{pattern_name}",
            )
            verdict = extract_json_from_response(response_text)
        except Exception as e:
            self.events_log.error(f"LLM call failed for {evidence.get('file_path')}: {e}")
            return None

        # ✅ FIXED: Proper null check
        if not verdict:
            self.events_log.warning(
                f"Investigation JSON parse failed for {evidence.get('file_path')}"
            )
            return None

        # ✅ FIXED: Ensure confidence is float in range [0.0, 1.0]
        try:
            confidence = float(verdict.get("confidence", 0.0))
            verdict["confidence"] = max(0.0, min(1.0, confidence))
        except (ValueError, TypeError):
            self.events_log.warning(
                f"Invalid confidence value for {evidence.get('file_path')}, defaulting to 0.0"
            )
            verdict["confidence"] = 0.0

        # ✅ FIXED: Always add file path to verdict
        verdict["file_path"] = evidence.get("file_path", "unknown")

        # ✅ NEW: Add metadata to verdict
        verdict["_llm_metadata"] = llm_metadata
        verdict["_prompt_metadata"] = prompt_metadata

        return verdict



        # ---------- Deliberation ---------- #

    def _analyze_file_relationships(self, reports: list) -> str:
        """Analyze how evidence files relate using the graph."""
        if not self.repo_graph:
            return ""

        relationships = []
        files = [r.get("file_path") for r in reports]

        # Check pairwise relationships
        for i, file1 in enumerate(files):
            for file2 in files[i + 1 :]:
                # Check if files have edges between them
                if self.repo_graph.has_edge(file1, file2):
                    edge_data = self.repo_graph.edges[file1, file2]
                    rel_type = edge_data.get("type", "unknown")
                    relationships.append(f"• {Path(file1).name} {rel_type} {Path(file2).name}")
                elif self.repo_graph.has_edge(file2, file1):
                    edge_data = self.repo_graph.edges[file2, file1]
                    rel_type = edge_data.get("type", "unknown")
                    relationships.append(f"• {Path(file2).name} {rel_type} {Path(file1).name}")

        if not relationships:
            return "No direct relationships found between evidence files."

        return "\n".join(relationships[:10])  # Limit to 10 relationships

    def run_deliberation(
        self, pattern_name: str, reports: list, plan: dict, repo_summary: str = ""
    ) -> dict | None:
        """Enhanced final synthesis with prompt hash tracking, model metadata, and confidence interval calculation."""

        pattern_data = self.patterns_data.get(pattern_name, {})
        definition = pattern_data.get("description", "No definition provided.")

        # Get examples
        positive_examples = pattern_data.get("positive_examples", [])[:1]
        negative_examples = pattern_data.get("negative_examples", [])[:1]

        # ✅ UPDATED: Use PromptBuilder with metadata
        from micropad.llm.prompts import PromptBuilder

        system_prompt, user_prompt, prompt_metadata = PromptBuilder.build_deliberation_prompt(
            pattern_name,
            definition,
            reports,
            repo_summary,
            plan,
            positive_examples,
            negative_examples,
        )

        # ✅ NEW: Log prompt hash
        self.events_log.debug(
            f"[{pattern_name}] Deliberation prompt hash: {prompt_metadata['user_hash']} "
            f"(version: {prompt_metadata['version']})"
        )

        # Store for reproducibility report
        self.prompt_hashes["deliberation"].append({"pattern": pattern_name, **prompt_metadata})

        # Call LLM
        # ✅ UPDATED: Get both response and metadata
        response_text, llm_metadata = self._call_llm(
            config.JUDGE_MODEL,
            system_prompt,
            user_prompt.strip(),
            operation=f"judge_{pattern_name}",
        )
        parsed = extract_json_from_response(response_text)

        if not parsed:
            self.events_log.warning(f"Deliberation JSON parse failed for {pattern_name}")
            return None

        # Ensure confidence_score is int
        try:
            parsed["confidence_score"] = int(parsed.get("confidence_score", 0))
        except:
            parsed["confidence_score"] = 0

        # ✅ NEW: Add metadata to verdict
        parsed["_llm_metadata"] = llm_metadata
        parsed["_prompt_metadata"] = prompt_metadata

        # ✅ NEW: Calculate confidence interval from evidence
        if len(reports) >= config.MIN_EVIDENCE_FOR_CI:

            confidences = [r.get("confidence", 0.0) for r in reports]
            mean_conf, lower_ci, upper_ci = calculate_confidence_interval(confidences)

            # Add to verdict
            parsed["confidence_interval"] = {
                "mean": float(mean_conf),
                "lower_bound": float(lower_ci),
                "upper_bound": float(upper_ci),
                "interval_width": float(upper_ci - lower_ci),
                "sample_size": len(confidences),
            }

            # Log confidence interval
            self.events_log.info(
                f"[{pattern_name}] Confidence interval: "
                f"{mean_conf:.3f} [{lower_ci:.3f}, {upper_ci:.3f}] "
                f"(width={upper_ci - lower_ci:.3f}, n={len(confidences)})"
            )

            # Add calibration warning if interval is too wide
            if upper_ci - lower_ci > 0.3:  # 30% interval width = high uncertainty
                parsed["high_uncertainty"] = True
                parsed["uncertainty_warning"] = (
                    f"Wide confidence interval ({upper_ci - lower_ci:.2f}) "
                    f"suggests evidence quality is inconsistent"
                )
                self.events_log.warning(
                    f"[{pattern_name}] High uncertainty detected - "
                    f"interval width {upper_ci - lower_ci:.3f} > 0.3 threshold"
                )
        else:
            # Not enough evidence for confidence interval
            parsed["confidence_interval"] = None
            parsed["insufficient_evidence_for_ci"] = True
            self.events_log.warning(
                f"[{pattern_name}] Insufficient evidence for confidence interval "
                f"({len(reports)} < {config.MIN_EVIDENCE_FOR_CI})"
            )

        return parsed

    def get_prompt_hash_summary(self) -> dict:
        """
        Get summary of all prompt hashes used during analysis.

        Returns:
            Dict with unique hashes per prompt type
        """
        return {
            "planner": list({p["user_hash"] for p in self.prompt_hashes["planner"]}),
            "investigation": list({p["user_hash"] for p in self.prompt_hashes["investigation"]}),
            "deliberation": list({p["user_hash"] for p in self.prompt_hashes["deliberation"]}),
            "version": (
                self.prompt_hashes["planner"][0]["version"]
                if self.prompt_hashes["planner"]
                else "unknown"
            ),
        }
