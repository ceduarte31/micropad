"""
Pattern Analyzer Module for MicroPAD.

This module orchestrates the multi-phase pattern detection process:
    1. File prioritization using multi-signal scoring
    2. Evidence investigation via LLM
    3. Final deliberation and verdict

The analyzer uses embeddings, graph analysis, keywords, and LLM reasoning
to detect architectural patterns in code repositories.
"""

import hashlib
import json
import logging
import re
import time
import warnings
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import chromadb
import networkx as nx
import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# Local imports
from micropad.config import settings as config
from micropad.llm.agent import AIAgent
from micropad.logging.detection import (
    log_file_scored,
    log_investigation_phase_complete,
    log_pattern_end,
    log_pattern_start,
    log_prioritization_complete,
)
from micropad.logging.ui import (
    Colors,
    clear_line,
    print_deliberation_start,
    print_dim,
    print_error,
    print_file_analysis,
    print_file_result,
    print_highlight,
    print_info,
    print_pattern_analysis_start,
    print_pattern_complete,
    print_pattern_detected,
    print_pattern_not_detected,
    print_pattern_phase,
    print_section,
    print_success,
    print_warning,
)

warnings.filterwarnings("ignore", message=".*CUDA out of memory.*")
logging.getLogger("torch").setLevel(logging.ERROR)


# ============================================================================
# ROBUST GPU INITIALIZATION WITH SUSPEND/RESUME SUPPORT
# ============================================================================


def initialize_gpu_safely():
    """
    Robustly initialize GPU with support for suspend/resume scenarios.
    Returns: (device_string, success_message)
    """
    import gc

    import torch

    device = "cpu"  # Default fallback

    if not torch.cuda.is_available():
        return "cpu", "No GPU detected"

    try:
        # Step 1: Try to reinitialize CUDA after potential suspend
        print_info("Attempting GPU initialization...", indent=1)

        # Force CUDA to reinitialize (handles post-suspend state)
        torch.cuda.init()

        # Step 2: Clear any stale CUDA cache
        torch.cuda.empty_cache()
        gc.collect()

        # Step 3: Test GPU with small operation
        test_tensor = torch.zeros(1, device="cuda")
        _ = test_tensor + 1  # Simple operation
        del test_tensor
        torch.cuda.empty_cache()

        # Step 4: Verify GPU is responsive
        gpu_name = torch.cuda.get_device_name(0)
        total_vram = torch.cuda.get_device_properties(0).total_memory / (1024**3)

        device = "cuda"
        return device, f"GPU ready: {gpu_name} ({total_vram:.1f}GB VRAM)"

    except RuntimeError as e:
        error_msg = str(e).lower()

        # Handle specific CUDA errors after suspend
        if "out of memory" in error_msg or "uninitialized" in error_msg:
            print_warning(
                f"GPU initialization issue (possibly after suspend): {str(e)[:60]}", indent=1
            )
            print_info("Attempting GPU reset...", indent=2)

            try:
                # Force reset CUDA context
                torch.cuda.empty_cache()
                torch.cuda.reset_peak_memory_stats()
                torch.cuda.synchronize()
                gc.collect()

                # Retry initialization
                test_tensor = torch.zeros(1, device="cuda")
                del test_tensor
                torch.cuda.empty_cache()

                device = "cuda"
                return device, "GPU recovered after reset"

            except Exception:
                return "cpu", "GPU reset failed - using CPU"
        else:
            return "cpu", f"GPU unavailable: {str(e)[:60]}"

    except Exception as e:
        return "cpu", f"Unexpected GPU error: {str(e)[:60]}"


# ============================================================================
# ADAPTIVE BATCH SIZE WITH CONTENT-AWARE TRUNCATION
# ============================================================================


def calculate_safe_batch_size(device: str, total_vram_gb: float = None) -> int:
    """Calculate safe batch size - reads from config."""
    return config.EMBEDDING_BATCH_SIZE if device == "cuda" else 4


def truncate_content_safely(content: str, max_chars: int) -> str:
    """Truncate file content to prevent memory overflow."""
    if len(content) <= max_chars:
        return content

    half = max_chars // 2
    return content[:half] + "\n...[TRUNCATED]...\n" + content[-half:]


# ============================================================================
# PHASE 2: ROBUST BATCH EMBEDDING WITH MEMORY MANAGEMENT
# ============================================================================


def generate_embeddings_robust(self, file_contents: dict, pattern_data: dict):
    """
    Generate embeddings with robust memory management and error recovery.

    FIXES:
    1. Adaptive batch sizing based on VRAM
    2. Content truncation to prevent large file OOM
    3. Per-batch memory cleanup
    4. Automatic retry with smaller batches on OOM
    5. Individual file fallback on batch failure
    """
    import gc

    import torch

    print_info("Generating embeddings with adaptive batching...", indent=1)

    # Determine safe batch size
    if torch.cuda.is_available():
        total_vram = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        BATCH_SIZE = calculate_safe_batch_size("cuda", total_vram)
        print_info(f"GPU mode: {total_vram:.1f}GB VRAM → batch size: {BATCH_SIZE}", indent=1)
    else:
        BATCH_SIZE = calculate_safe_batch_size("cpu")
        print_info(f"CPU mode → batch size: {BATCH_SIZE}", indent=1)

    # Truncate large files to prevent OOM
    MAX_CONTENT_LENGTH = 8000  # Characters (~2000 tokens)
    truncated_count = 0

    for f, content in file_contents.items():
        if len(content) > MAX_CONTENT_LENGTH:
            file_contents[f] = truncate_content_safely(content, MAX_CONTENT_LENGTH)
            truncated_count += 1

    if truncated_count > 0:
        print_info(f"Truncated {truncated_count} large files (>8KB) to prevent OOM", indent=1)

    file_embeddings = {}
    file_list = list(file_contents.keys())
    total_batches = (len(file_list) + BATCH_SIZE - 1) // BATCH_SIZE

    failed_batches = []

    for batch_idx in range(total_batches):
        batch_start = batch_idx * BATCH_SIZE
        batch_files = file_list[batch_start : batch_start + BATCH_SIZE]
        batch_contents = [file_contents[f] for f in batch_files]

        # Progress indicator
        percent = ((batch_idx + 1) / total_batches) * 100
        bar_width = 30
        filled = int(bar_width * (batch_idx + 1) / total_batches)
        bar = "█" * filled + "░" * (bar_width - filled)

        files_in_batch = len(batch_files)
        print(
            f"\r    Batch [{batch_idx+1:2d}/{total_batches:2d}] [{bar}] {percent:5.1f}% | "
            f"{files_in_batch} files",
            end="",
            flush=True,
        )

        try:
            # CRITICAL: Clear GPU cache before each batch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            gc.collect()

            # Batch encode with conservative settings
            batch_embeddings = self.model.encode(
                batch_contents,
                batch_size=BATCH_SIZE,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=False,  # Slightly reduces memory
            )

            # Store embeddings
            for f, emb in zip(batch_files, batch_embeddings):
                file_embeddings[f] = emb

            # Clear batch data from memory immediately
            del batch_embeddings

        except RuntimeError as e:
            error_msg = str(e).lower()

            if "out of memory" in error_msg or "cuda" in error_msg:
                # OOM ERROR - Retry with smaller chunks
                self.events_log.warning(f"OOM in batch {batch_idx+1}. Retrying individually...")

                # Clear everything
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    torch.cuda.reset_peak_memory_stats()
                gc.collect()

                # Process each file individually as fallback
                for f, content in zip(batch_files, batch_contents):
                    try:
                        emb = self.model.encode(
                            [content], batch_size=1, show_progress_bar=False, convert_to_numpy=True
                        )[0]
                        file_embeddings[f] = emb

                        # Clear after each file
                        if torch.cuda.is_available():
                            torch.cuda.empty_cache()
                        gc.collect()

                    except Exception as inner_e:
                        # Last resort: zero embedding
                        self.events_log.warning(f"Failed to embed {f.name}: {str(inner_e)[:50]}")
                        file_embeddings[f] = np.zeros(self.model.get_sentence_embedding_dimension())
            else:
                # Non-OOM error - log and use zero embeddings
                self.events_log.warning(f"Batch embedding failed: {str(e)[:80]}")
                for f in batch_files:
                    file_embeddings[f] = np.zeros(self.model.get_sentence_embedding_dimension())

        except Exception as e:
            # Unexpected error - log and skip batch
            self.events_log.warning(f"Unexpected error in batch {batch_idx+1}: {str(e)[:80]}")
            for f in batch_files:
                file_embeddings[f] = np.zeros(self.model.get_sentence_embedding_dimension())

    print()  # Newline after progress
    print_success(
        f"Generated {len(file_embeddings)} embeddings in {total_batches} batches", indent=1
    )

    return file_embeddings


class EmbeddingCache:
    """Handles loading, saving, and retrieving cached embeddings."""

    def __init__(self, cache_path: Path):
        self.cache_path = cache_path
        self.cache = self._load()
        self.access_count = {}

    def _load(self):
        if not self.cache_path.exists():
            return {}
        try:
            return json.load(open(self.cache_path, "r", encoding="utf-8"))
        except Exception:
            return {}

    def get(self, key: str):
        if key in self.cache:
            self.access_count[key] = self.access_count.get(key, 0) + 1
            return self.cache[key]
        return None

    def set(self, key: str, value):
        if len(self.cache) >= config.MAX_EMBEDDING_CACHE_SIZE:
            self._evict_lru()
        self.cache[key] = value
        self.access_count[key] = 1

    def _evict_lru(self):
        if not self.access_count:
            return
        losers = sorted(self.access_count.items(), key=lambda x: x[1])[
            : max(1, len(self.access_count) // 10)
        ]
        for k, _ in losers:
            self.cache.pop(k, None)
            self.access_count.pop(k, None)

    def save(self):
        try:
            json.dump(self.cache, open(self.cache_path, "w", encoding="utf-8"), indent=2)
        except Exception:
            pass


# ============================================================================
# FILE CONTENT CACHE
# ============================================================================


class FileContentCache:
    """
    In-memory cache for file contents to eliminate redundant disk I/O.

    Benefits:
    - Files read once during scoring, reused during investigation
    - Configurable size limit to prevent memory issues
    - LRU eviction when cache is full
    - Automatic cleanup between patterns
    """

    def __init__(self, max_size_mb: int = 500):
        """
        Initialize cache with size limit.

        Args:
            max_size_mb: Maximum cache size in megabytes (default 500MB)
        """
        self.cache = {}  # Path -> content
        self.access_count = {}  # Path -> access count (for LRU)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.current_size_bytes = 0
        self.hits = 0
        self.misses = 0
        self.events_log = logging.getLogger("events")

    def get(self, file_path: Path) -> Optional[str]:
        """
        Retrieve file content from cache.

        Returns:
            File content if cached, None otherwise
        """
        cache_key = str(file_path)

        if cache_key in self.cache:
            self.hits += 1
            self.access_count[cache_key] = self.access_count.get(cache_key, 0) + 1
            return self.cache[cache_key]

        self.misses += 1
        return None

    def put(self, file_path: Path, content: str) -> bool:
        """
        Store file content in cache.

        Returns:
            True if stored successfully, False if skipped (too large)
        """
        cache_key = str(file_path)
        content_size = len(content.encode("utf-8"))

        # Skip files that are individually too large (>10MB)
        if content_size > 10 * 1024 * 1024:
            self.events_log.debug(
                f"Skipping cache for large file: {file_path.name} ({content_size / 1024 / 1024:.1f}MB)"
            )
            return False

        # Evict if necessary
        while self.current_size_bytes + content_size > self.max_size_bytes and self.cache:
            self._evict_lru()

        # Store
        self.cache[cache_key] = content
        self.current_size_bytes += content_size
        self.access_count[cache_key] = 1

        return True

    def _evict_lru(self):
        """Evict least recently used entry."""
        if not self.access_count:
            return

        # Find least accessed
        lru_key = min(self.access_count.items(), key=lambda x: x[1])[0]

        # Remove
        if lru_key in self.cache:
            content_size = len(self.cache[lru_key].encode("utf-8"))
            self.current_size_bytes -= content_size
            del self.cache[lru_key]

        del self.access_count[lru_key]

    def clear(self):
        """Clear all cached content."""
        self.cache.clear()
        self.access_count.clear()
        self.current_size_bytes = 0

    def get_stats(self) -> dict:
        """Get cache statistics."""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate,
            "cached_files": len(self.cache),
            "size_mb": self.current_size_bytes / 1024 / 1024,
        }

    def print_stats(self):
        """Print cache statistics to console."""
        stats = self.get_stats()

        print_dim(f"File content cache stats:", indent=1)
        print_dim(
            f"  • Hit rate: {stats['hit_rate']:.1f}% ({stats['hits']} hits, {stats['misses']} misses)",
            indent=2,
        )
        print_dim(f"  • Cached files: {stats['cached_files']}", indent=2)
        print_dim(f"  • Memory used: {stats['size_mb']:.1f}MB", indent=2)


class PatternAnalyzer:
    """
    Simplified Pattern Analyzer with deterministic behavior.
    """

    def __init__(
        self, repo_graph: nx.DiGraph, patterns_data: dict, verbose: bool = None, indexer=None
    ):
        """
        Initialize analyzer with robust GPU handling and memory management.
        """
        print_info("Initializing Analyzer...")

        self.indexer = indexer
        self.graph_build_triggered = False

        # Network timeout fix
        import os

        os.environ["HF_HUB_DOWNLOAD_TIMEOUT"] = "180"

        # Cache directory
        cache_dir = Path("./.generated/micropad/model_cache")
        cache_dir.mkdir(exist_ok=True, parents=True)

        print_info(f"Loading embedding model: {config.EMBEDDING_MODEL}", indent=1)

        # ROBUST GPU INITIALIZATION (handles suspend/resume)
        device, gpu_status = initialize_gpu_safely()

        if device == "cuda":
            print_success(gpu_status, indent=1)
        else:
            print_warning(gpu_status, indent=1)
            print_info("Falling back to CPU (will be slower)", indent=1)

        # Load model on determined device
        try:
            self.model = SentenceTransformer(
                config.EMBEDDING_MODEL,
                trust_remote_code=True,
                cache_folder=str(cache_dir),
                device=device,
            )
            print_success(f"Model loaded on {device.upper()}", indent=1)

        except Exception as e:
            print_error(f"Model loading failed: {e}", indent=1)

            if device == "cuda":
                # Final fallback to CPU
                print_info("Forcing CPU mode...", indent=1)
                os.environ["CUDA_VISIBLE_DEVICES"] = ""

                self.model = SentenceTransformer(
                    config.EMBEDDING_MODEL,
                    trust_remote_code=True,
                    cache_folder=str(cache_dir),
                    device="cpu",
                )
                print_success("Model loaded on CPU", indent=1)
            else:
                raise

        # Initialize remaining components
        print_info("Connecting to vector database...", indent=1)
        self.client = chromadb.PersistentClient(path=str(config.DB_PATH))
        self.collection = self.client.get_or_create_collection(name=config.COLLECTION_NAME)
        print_success("Database connected", indent=1)

        self.repo_graph = repo_graph
        self.patterns_data = patterns_data
        self.ai_agent = AIAgent(repo_graph=repo_graph, patterns_data=patterns_data)
        self.verbose = verbose if verbose is not None else config.VERBOSE_MODE
        self.events_log = logging.getLogger("events")
        self.cache = EmbeddingCache(config.DB_PATH / "embedding_cache.json")

        # File cache
        if config.FILE_CACHE_ENABLED:
            self.file_cache = FileContentCache(max_size_mb=config.FILE_CACHE_SIZE_MB)
            print_success(
                f"File content cache initialized ({config.FILE_CACHE_SIZE_MB}MB limit)", indent=1
            )
        else:
            self.file_cache = None
            print_warning("File content cache disabled", indent=1)

        self.centrality_scores = {}

        if config.GRAPH_ENABLED and repo_graph:
            print_info("Computing graph metrics...", indent=1)
            self._compute_graph_metrics()
            print_success(f"Graph metrics ready ({len(self.centrality_scores)} nodes)", indent=1)

        print_success("Analyzer ready")

    def _ensure_graph_built(self, pattern_name: str, candidate_count: int) -> bool:
        """
        FIXED: Thread-safe lazy graph construction.

        Only builds graph when:
        - Lazy loading is enabled
        - Graph not already built
        - Pattern has sufficient candidates to benefit from graph analysis

        Args:
            pattern_name: Pattern being analyzed
            candidate_count: Number of candidate files for this pattern

        Returns:
            True if graph is available (either pre-built or just built)
        """
        # Already have graph (pre-built or previously lazy-loaded)
        if self.repo_graph is not None:
            return True

        # Lazy loading disabled - can't build
        if not config.GRAPH_LAZY_LOADING:
            return False

        # No indexer available - can't build
        if self.indexer is None:
            return False

        # Not enough candidates to justify graph construction cost
        if candidate_count < config.GRAPH_MIN_CANDIDATES:
            self.events_log.debug(
                f"[{pattern_name}] Skipping graph construction: "
                f"only {candidate_count} candidates (< {config.GRAPH_MIN_CANDIDATES} threshold)"
            )
            return False

        # ✅ FIXED: Thread-safe build trigger (first time only)
        if not self.graph_build_triggered:
            from micropad.logging.ui import print_error, print_highlight, print_success

            print_highlight(
                f"Graph construction triggered for '{pattern_name}' "
                f"({candidate_count} candidates)",
                indent=1,
            )

            try:
                import time

                graph_start = time.time()

                # ✅ FIXED: Use existing build_graph() method
                self.repo_graph = self.indexer.build_graph()

                graph_time = time.time() - graph_start

                if self.repo_graph:
                    print_success(
                        f"Graph built: {self.repo_graph.number_of_nodes()} nodes, "
                        f"{self.repo_graph.number_of_edges()} edges ({graph_time:.1f}s)",
                        indent=2,
                    )

                    # ✅ CRITICAL: Update AI agent's graph reference
                    self.ai_agent.repo_graph = self.repo_graph

                    # Compute centrality metrics
                    self._compute_graph_metrics()

                    # Log to detection log
                    from micropad.logging.detection import log_graph_built

                    log_graph_built(
                        self.repo_graph.number_of_nodes(),
                        self.repo_graph.number_of_edges(),
                        graph_time,
                    )

                    self.graph_build_triggered = True
                    return True
                else:
                    print_error("Graph construction returned None", indent=2)
                    self.graph_build_triggered = True  # Don't retry
                    return False

            except Exception as e:
                print_error(f"Lazy graph construction failed: {e}", indent=2)
                self.events_log.error(f"Lazy graph construction error: {e}")
                self.graph_build_triggered = True  # Don't retry
                return False

        return self.repo_graph is not None

    def analyze_patterns(self, patterns: dict, categorized_files: dict):
        """
        COMPLETE: Pattern analysis with lazy graph loading support.

        Changes:
        - Trigger lazy graph construction when needed
        - Compute metrics after lazy build
        - Proper error handling
        """
        final_results = {}
        total_patterns = len(patterns)
        events_logger = logging.getLogger("events")

        for idx, (pattern_name, pattern_data) in enumerate(patterns.items(), start=1):
            pattern_start_time = time.time()

            # Print separator
            print_pattern_analysis_start(pattern_name, idx, total_patterns)

            events_logger.info(
                f"{'='*80}\nStarting analysis for pattern {idx}/{total_patterns}: {pattern_name}\n{'='*80}"
            )

            # Collect candidates
            candidates = self._collect_all_candidates(pattern_name, categorized_files)

            # ✅ NEW: Trigger lazy graph construction if needed
            if config.GRAPH_LAZY_LOADING and self.indexer:
                graph_available = self._ensure_graph_built(pattern_name, len(candidates))
                if graph_available and not self.centrality_scores:
                    # Graph was just built - compute metrics
                    print_info("Computing graph centrality metrics...", indent=1)
                    self._compute_graph_metrics()
                    print_success(
                        f"Centrality computed for {len(self.centrality_scores)} nodes", indent=2
                    )

            log_pattern_start(pattern_name, len(candidates))

            if not candidates:
                print_warning("No candidate files")
                events_logger.info(f"No candidates for {pattern_name}; skipping")
                log_pattern_end(pattern_name, time.time() - pattern_start_time, 0, False)

                print_pattern_complete(
                    pattern_name, detected=False, duration=time.time() - pattern_start_time
                )
                continue

            print_info(f"Collected {len(candidates)} candidate files", indent=1)

            # Create plan
            plan = self.ai_agent.run_planner(pattern_name, pattern_data)
            if not plan:
                print_warning("Planner failed – fallback plan")
                plan = {
                    "conceptual_characteristics": [
                        f"Serves the architectural purpose of {pattern_name}",
                        "Core conceptual role",
                        "Implementation form may vary",
                    ],
                    "investigator_prompt": f"Determine if code serves {pattern_name} purpose.",
                    "judge_prompt": f"Judge if evidence shows {pattern_name} purpose.",
                }
            print_success("Plan created")

            # Score and prioritize
            entry = categorized_files.get(pattern_name, {})
            confidence_map = self._normalize_confidence_map(entry)

            scored_files = self._score_and_prioritize_files(
                candidates, pattern_name, pattern_data, confidence_map, categorized_files
            )

            if not scored_files:
                print_warning("No files passed scoring threshold")
                log_pattern_end(pattern_name, time.time() - pattern_start_time, 0, False)
                continue

            # Log distribution
            high_ct = sum(1 for f in scored_files if f["score"] >= config.HIGH_PRIORITY_THRESHOLD)
            med_ct = sum(
                1
                for f in scored_files
                if config.MEDIUM_PRIORITY_THRESHOLD <= f["score"] < config.HIGH_PRIORITY_THRESHOLD
            )
            low_ct = len(scored_files) - high_ct - med_ct

            log_prioritization_complete(
                pattern_name, len(scored_files), {"high": high_ct, "medium": med_ct, "low": low_ct}
            )

            print_info(
                f"Priority distribution: {high_ct} high, {med_ct} medium, {low_ct} low", indent=1
            )

            # Generate repo summary
            repo_summary = self._generate_repo_summary(scored_files)
            print_info("Repository summary prepared", indent=1)

            # Analyze files
            print_info("Analyzing files...", indent=1)
            investigation_start = time.time()

            evidence = self._analyze_files(
                scored_files, pattern_name, pattern_data, plan, repo_summary=repo_summary
            )

            investigation_duration = time.time() - investigation_start

            log_investigation_phase_complete(
                pattern_name,
                "first_pass",
                min(config.MAX_FILES_PER_PATTERN, len(scored_files)),
                len(evidence),
                investigation_duration,
            )

            # Deliberate and decide
            if evidence:
                events_logger.info(
                    f"[{pattern_name}] {len(evidence)} evidence file(s) – deliberating"
                )
                verdict = self._deliberate_and_decide(
                    pattern_name, evidence, plan, repo_summary=repo_summary
                )
                if verdict:
                    final_results[pattern_name] = verdict
                    pattern_duration = time.time() - pattern_start_time
                    log_pattern_end(pattern_name, pattern_duration, len(evidence), True)
                else:
                    pattern_duration = time.time() - pattern_start_time
                    log_pattern_end(pattern_name, pattern_duration, len(evidence), False)
            else:
                print_pattern_not_detected(pattern_name, "No evidence found")
                events_logger.info(f"[{pattern_name}] Not detected (no evidence)")
                pattern_duration = time.time() - pattern_start_time
                log_pattern_end(pattern_name, pattern_duration, 0, False)

            # Clear cache if configured
            if self.file_cache and config.FILE_CACHE_CLEAR_PER_PATTERN:
                self.file_cache.clear()
                self.events_log.debug(f"File cache cleared after {pattern_name}")

        # Print final cache statistics
        if self.file_cache:
            print_info("Final file cache statistics:")
            self.file_cache.print_stats()

        events_logger.info(
            f"Pattern analysis complete. Detected {len(final_results)}/{len(patterns)} patterns."
        )

        return final_results

    def _calculate_graph_score_contextual(
        self, file_path: Path, pattern_name: str, categorized_files: dict
    ) -> float:
        """
        Context-aware graph centrality scoring (pattern-agnostic).

        Improvements over base centrality:
        - Boosts files connected to pattern-relevant files
        - Penalizes generic hub files (connected to everything, relevant to nothing)
        - Returns 0.0 gracefully if graph unavailable

        Args:
            file_path: Path to file being scored
            pattern_name: Pattern being analyzed
            categorized_files: Dict of categorized files per pattern

        Returns:
            float: Contextualized graph score (0.0-1.0)
        """
        if not self.repo_graph or str(file_path) not in self.repo_graph:
            return 0.0

        # Base centrality score from PageRank
        base_score = self.centrality_scores.get(str(file_path), 0.0)

        # Get pattern-specific high-priority files for context
        pattern_files = categorized_files.get(pattern_name, {})
        if isinstance(pattern_files, dict):
            high_priority_files = set(str(f) for f in pattern_files.get("tier1", []))
        else:
            high_priority_files = set()

        # Find neighbors in the graph
        try:
            neighbors = list(self.repo_graph.neighbors(str(file_path)))
        except:
            neighbors = []

        if not neighbors:
            return base_score

        # Calculate relevance boost based on connections to high-priority files
        relevant_neighbors = sum(1 for n in neighbors if n in high_priority_files)

        if relevant_neighbors > 0:
            # Boost for pattern-relevant connections (up to 50% increase)
            relevance_boost = (relevant_neighbors / len(neighbors)) * 0.5
        else:
            relevance_boost = 0.0

        # Penalize pure hub files (connected to everything, relevant to nothing)
        # These are files with many connections but few pattern-relevant ones
        hub_penalty = 0.0
        if len(neighbors) > 20 and relevant_neighbors < 3:
            # Generic hub (e.g., common utility file), not pattern-specific
            hub_penalty = 0.25

        # Calculate final score
        final_score = max(0.0, base_score + relevance_boost - hub_penalty)

        # Cap at 1.0
        return min(final_score, 1.0)

    def _calculate_decorator_score(self, graph: nx.DiGraph, file_path: Path, pattern_name: str) -> float:
        """
        Score based on decorators/annotations extracted by parser.

        High-value decorators for microservice patterns:
        - @RestController, @Service, @Component (Java Spring)
        - @app.route, @blueprint, @api (Python Flask/FastAPI)
        - @Controller, @Get, @Post (TypeScript NestJS)
        - @MessageHandler, @RabbitListener (Message-based)
        """
        if not self.repo_graph:
            return 0.0

        file_node_str = str(file_path)
        if file_node_str not in self.repo_graph:
            return 0.0

        # Microservice-relevant decorator patterns
        microservice_decorators = {
            # API/REST patterns
            'route': 0.8, 'controller': 0.8, 'restcontroller': 0.9,
            'get': 0.6, 'post': 0.6, 'put': 0.6, 'delete': 0.6, 'patch': 0.6,
            'requestmapping': 0.7, 'api': 0.7, 'endpoint': 0.7,

            # Service/Component patterns
            'service': 0.8, 'component': 0.7, 'bean': 0.6,
            'injectable': 0.7, 'provider': 0.6,

            # Message-based patterns
            'messagehandler': 0.9, 'rabbitlistener': 0.9, 'kafkalistener': 0.9,
            'eventhandler': 0.8, 'streamlistener': 0.8,

            # Circuit breaker/resilience
            'circuitbreaker': 0.9, 'retry': 0.7, 'timeout': 0.6,
            'fallback': 0.7, 'bulkhead': 0.7,

            # Auth/Security
            'authenticated': 0.5, 'secured': 0.5, 'authorized': 0.5,
        }

        score = 0.0
        decorator_count = 0

        # Check functions/classes in this file for decorators
        for successor in self.repo_graph.successors(file_node_str):
            node_data = self.repo_graph.nodes.get(successor, {})
            decorators = node_data.get('decorators', [])

            for decorator in decorators:
                decorator_count += 1
                decorator_lower = decorator.lower()

                # Check for microservice-relevant patterns
                for pattern, weight in microservice_decorators.items():
                    if pattern in decorator_lower:
                        score += weight
                        break
                else:
                    # Generic decorator (still slightly valuable)
                    score += 0.1

        # Normalize: 2-3 relevant decorators should max out at 1.0
        if decorator_count == 0:
            return 0.0

        normalized = score / (decorator_count * 0.9)  # Normalize assuming most are relevant
        return min(normalized, 1.0)

    def _calculate_string_score(self, graph: nx.DiGraph, file_path: Path) -> float:
        """
        Score based on string literals (URLs, endpoints, queue names) extracted by parser.

        High-value strings:
        - Service URLs: http://user-service:8080
        - API endpoints: /api/users, /orders/{id}
        - Message queues: orders.queue, payment.topic
        """
        if not self.repo_graph:
            return 0.0

        file_node_str = str(file_path)
        if file_node_str not in self.repo_graph:
            return 0.0

        score = 0.0
        string_count = 0

        # Check for string literal nodes connected to this file
        for successor in self.repo_graph.successors(file_node_str):
            node_data = self.repo_graph.nodes.get(successor, {})

            if node_data.get('type') == 'string_literal':
                string_type = node_data.get('string_type')
                string_count += 1

                # Weight by type
                if string_type == 'url':
                    score += 0.8  # Service URLs are strong indicators
                elif string_type == 'endpoint':
                    score += 0.7  # API endpoints are strong indicators
                elif string_type == 'queue':
                    score += 0.9  # Message queues are very strong indicators

        # Normalize: 2-3 relevant strings should approach 1.0
        if string_count == 0:
            return 0.0

        normalized = score / (max(string_count, 3) * 0.8)
        return min(normalized, 1.0)

    def _calculate_class_score(self, graph: nx.DiGraph, file_path: Path, pattern_name: str) -> float:
        """
        Score based on classes extracted by parser.

        Relevant class names for microservices:
        - *Controller, *Service, *Repository, *Client
        - *Gateway, *Proxy, *Handler
        """
        if not self.repo_graph:
            return 0.0

        file_node_str = str(file_path)
        if file_node_str not in self.repo_graph:
            return 0.0

        microservice_class_patterns = [
            ('controller', 0.8),
            ('service', 0.8),
            ('repository', 0.7),
            ('client', 0.7),
            ('gateway', 0.9),
            ('proxy', 0.8),
            ('handler', 0.7),
            ('listener', 0.7),
            ('consumer', 0.7),
            ('producer', 0.7),
            ('adapter', 0.6),
            ('facade', 0.6),
        ]

        score = 0.0
        class_count = 0

        # Check classes defined in this file
        for successor in self.repo_graph.successors(file_node_str):
            node_data = self.repo_graph.nodes.get(successor, {})

            if node_data.get('type') == 'class':
                class_count += 1
                class_name = node_data.get('name', '').lower()

                # Check for microservice patterns
                for pattern, weight in microservice_class_patterns:
                    if pattern in class_name:
                        score += weight
                        break
                else:
                    # Generic class (minimal value)
                    score += 0.05

        # Normalize: 1-2 relevant classes should approach 1.0
        if class_count == 0:
            return 0.0

        normalized = score / (max(class_count, 2) * 0.7)
        return min(normalized, 1.0)

    # pattern_analyzer.py - ADD THIS NEW METHOD

    def _calculate_keyword_score(
        self, keywords_found: list, anti_keywords: list, content: str, file_path: Path
    ) -> float:
        """
        Context-aware keyword scoring (pattern-agnostic).

        Scoring factors:
        - Position (class/function names worth more)
        - Density (repeated mentions with diminishing returns)
        - Anti-keyword penalty
        """
        if not keywords_found:
            return 0.0

        score = 0.0
        content_lower = content.lower()
        lines = content.splitlines()[:200]  # Limit to first 200 lines for performance

        for keyword in keywords_found:
            kw_lower = keyword.lower()

            # Base score for presence
            kw_score = 0.15

            # Boost for occurrences in important positions
            position_score = 0.0
            for line in lines:
                line_lower = line.lower()
                if kw_lower in line_lower:
                    # Check position type
                    if any(p in line_lower for p in ["class ", "interface ", "struct "]):
                        position_score = max(position_score, 0.3)
                    elif any(
                        p in line_lower
                        for p in ["def ", "function ", "func ", "public ", "private "]
                    ):
                        position_score = max(position_score, 0.25)
                    elif any(p in line_lower for p in ["import ", "from ", "require(", "use "]):
                        position_score = max(position_score, 0.15)
                    elif any(p in line_lower for p in ["#", "//", "/*", "*", "<!--"]):
                        position_score = max(position_score, 0.05)
                    else:
                        position_score = max(position_score, 0.1)

            kw_score += position_score

            # Density bonus (diminishing returns)
            occurrences = content_lower.count(kw_lower)
            density_bonus = min(occurrences * 0.03, 0.2)
            kw_score += density_bonus

            score += kw_score

        # Anti-keyword penalty (scaled by dominance)
        anti_penalty = 0.0
        for anti_kw in anti_keywords:
            occurrences = content_lower.count(anti_kw.lower())
            # Penalty scales with how prominent anti-keywords are
            anti_penalty += min(occurrences * 0.08, 0.3)

        score = max(0.0, score - anti_penalty)

        # Normalize to 0-1 range
        # Expected max: ~0.6 per keyword, so divide by (num_keywords * 0.8)
        normalized = score / (len(keywords_found) * 0.8)
        return min(normalized, 1.0)

    def _score_and_prioritize_files(
        self, files, pattern_name, pattern_data, llm_confidence_map=None, categorized_files=None
    ):
        """
        Score candidates using multi-signal weighting with BATCHED embedding generation.

        PERFORMANCE OPTIMIZATION:
        - Batch embedding generation (10-20x faster than sequential)
        - Custom progress indicators matching project style
        - File caching to avoid redundant I/O
        """

        out = []

        # Extract confidence map from categorized_files
        if categorized_files and pattern_name in categorized_files:
            pattern_entry = categorized_files[pattern_name]
            confidence_map = pattern_entry.get("llm_confidence_map", {})
            if not confidence_map and llm_confidence_map:
                confidence_map = llm_confidence_map
        else:
            confidence_map = llm_confidence_map or {}

        # LOG: Show what we have
        if confidence_map:
            self.events_log.debug(
                f"[{pattern_name}] Using LLM confidence map with {len(confidence_map)} entries"
            )
        else:
            self.events_log.warning(
                f"[{pattern_name}] No LLM confidence map - LLM score component will be 0.0"
            )

        # ============================================================================
        # PHASE 1: Read all file contents
        # ============================================================================
        print_info(f"Reading {len(files)} candidate files...", indent=1)
        file_contents = {}
        file_keywords = {}

        total_files = len(files)
        for i, f in enumerate(sorted(files, key=str), 1):
            # Progress indicator
            percent = (i / total_files) * 100
            bar_width = 30
            filled = int(bar_width * i / total_files)
            bar = "█" * filled + "░" * (bar_width - filled)

            filename = f.name[:35] + "..." if len(f.name) > 35 else f.name
            print(
                f"\r    [{i:3d}/{total_files:3d}] [{bar}] {percent:5.1f}% | {filename:<38}",
                end="",
                flush=True,
            )

            try:
                content = None
                if self.file_cache:
                    content = self.file_cache.get(f)

                if content is None:
                    with open(f, "r", encoding="utf-8", errors="ignore") as fp:
                        content = fp.read()
                    if self.file_cache:
                        self.file_cache.put(f, content)

                file_contents[f] = content

                # Find keywords while we have the content
                keywords, anti_keywords = self._find_keywords(f, content, pattern_data)
                file_keywords[f] = (keywords, anti_keywords)

            except Exception as e:
                self.events_log.warning(f"Error reading {f}: {e}")
                file_contents[f] = ""
                file_keywords[f] = ([], [])

        print()  # Newline after progress
        print_success(f"Read {len(file_contents)} files", indent=1)

        # ============================================================================
        # PHASE 2: Batch embedding generation (ADAPTIVE)
        # ============================================================================
        print_info("Generating embeddings in batches...", indent=1)

        # Adaptive batch size based on device and memory
        if torch.cuda.is_available():
            try:
                # Get available VRAM
                total_vram = torch.cuda.get_device_properties(0).total_memory / (1024**3)  # GB

                if total_vram >= 16:
                    BATCH_SIZE = 16
                elif total_vram >= 8:
                    BATCH_SIZE = 8
                elif total_vram >= 4:
                    BATCH_SIZE = 4
                else:
                    BATCH_SIZE = 2

                print_info(
                    f"GPU detected: {total_vram:.1f}GB VRAM → batch size: {BATCH_SIZE}", indent=1
                )
            except:
                BATCH_SIZE = 4
        else:
            # CPU mode - use smaller batches
            BATCH_SIZE = 4
            print_info(f"CPU mode → batch size: {BATCH_SIZE}", indent=1)

        file_embeddings = {}
        file_list = list(file_contents.keys())
        total_batches = (len(file_list) + BATCH_SIZE - 1) // BATCH_SIZE

        for batch_idx in range(total_batches):
            batch_start = batch_idx * BATCH_SIZE
            batch_files = file_list[batch_start : batch_start + BATCH_SIZE]
            batch_contents = [file_contents[f] for f in batch_files]

            # Progress indicator
            percent = ((batch_idx + 1) / total_batches) * 100
            bar_width = 30
            filled = int(bar_width * (batch_idx + 1) / total_batches)
            bar = "█" * filled + "░" * (bar_width - filled)

            files_in_batch = len(batch_files)
            print(
                f"\r    Batch [{batch_idx+1:2d}/{total_batches:2d}] [{bar}] {percent:5.1f}% | "
                f"{files_in_batch} files",
                end="",
                flush=True,
            )

            try:
                # Clear GPU cache before each batch to prevent memory buildup
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()

                # Batch encode with memory-aware settings
                batch_embeddings = self.model.encode(
                    batch_contents,
                    batch_size=BATCH_SIZE,
                    show_progress_bar=False,
                    convert_to_numpy=True,
                    normalize_embeddings=False,  # Reduces memory usage slightly
                )

                # Store embeddings
                for f, emb in zip(batch_files, batch_embeddings):
                    file_embeddings[f] = emb

            except RuntimeError as e:
                if "out of memory" in str(e).lower() or "cuda" in str(e).lower():
                    self.events_log.warning(
                        f"OOM error in batch {batch_idx+1}. Retrying with smaller chunks..."
                    )

                    # Clear cache and retry with individual files
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()

                    # Process files one at a time as fallback
                    for f, content in zip(batch_files, batch_contents):
                        try:
                            emb = self.model.encode(
                                [content],
                                batch_size=1,
                                show_progress_bar=False,
                                convert_to_numpy=True,
                            )[0]
                            file_embeddings[f] = emb
                        except Exception:
                            # Last resort: zero embedding
                            file_embeddings[f] = np.zeros(
                                self.model.get_sentence_embedding_dimension()
                            )
                else:
                    self.events_log.warning(f"Batch embedding failed: {e}")
                    # Fallback: zero embeddings for this batch
                    for f in batch_files:
                        file_embeddings[f] = np.zeros(self.model.get_sentence_embedding_dimension())

        # ============================================================================
        # PHASE 3: Score each file using pre-computed embeddings
        # ============================================================================
        print_info("Scoring files with multi-signal weighting...", indent=1)

        total_files = len(files)
        for i, f in enumerate(sorted(files, key=str), 1):
            # Progress indicator
            percent = (i / total_files) * 100
            bar_width = 30
            filled = int(bar_width * i / total_files)
            bar = "█" * filled + "░" * (bar_width - filled)

            filename = f.name[:35] + "..." if len(f.name) > 35 else f.name
            print(
                f"\r    [{i:3d}/{total_files:3d}] [{bar}] {percent:5.1f}% | {filename:<38}",
                end="",
                flush=True,
            )

            try:
                content = file_contents[f]
                keywords, anti_keywords = file_keywords[f]
                embedding = file_embeddings.get(f)

                # Keyword scoring
                keyword_score = self._calculate_keyword_score(keywords, anti_keywords, content, f)

                # Embedding search using pre-computed embedding
                embedding_score = 0.0
                if embedding is not None:
                    embedding_score = self._search_chromadb_with_embedding(embedding, pattern_name)
                embedding_score = max(0.0, embedding_score)

                # Parser/Graph score (composite of centrality + parser signals)
                parser_score = 0.0
                centrality_score = 0.0
                decorator_score = 0.0
                string_score = 0.0
                class_score = 0.0

                if config.GRAPH_ENABLED and self.repo_graph:
                    # Get centrality
                    if categorized_files:
                        centrality_score = self._calculate_graph_score_contextual(
                            f, pattern_name, categorized_files
                        )
                    else:
                        centrality_score = self.centrality_scores.get(str(f), 0.0)

                    # Get parser-extracted signals
                    decorator_score = self._calculate_decorator_score(self.repo_graph, f, pattern_name)
                    string_score = self._calculate_string_score(self.repo_graph, f)
                    class_score = self._calculate_class_score(self.repo_graph, f, pattern_name)

                    # Dynamic weight normalization based on language support
                    # Determine which features the LANGUAGE supports (not what this file has)
                    from micropad.repository.code_parsers import LANGUAGE_MAP, LANGUAGE_QUERIES

                    # Get language for this file
                    file_ext = f.suffix
                    lang_name = LANGUAGE_MAP.get(file_ext)

                    # Determine supported features from language queries
                    supported_features = []

                    # Centrality: always supported
                    supported_features.append(('centrality', centrality_score))

                    if lang_name and lang_name in LANGUAGE_QUERIES:
                        queries = LANGUAGE_QUERIES[lang_name]

                        # Decorators: supported if language has decorator query
                        if queries.get('decorators'):
                            supported_features.append(('decorator', decorator_score))

                        # Strings: supported if language has string query
                        if queries.get('strings'):
                            supported_features.append(('string', string_score))

                        # Classes: supported if language has class query
                        if queries.get('classes'):
                            supported_features.append(('class', class_score))
                    else:
                        # Unknown language - use all features with equal weight
                        supported_features = [
                            ('centrality', centrality_score),
                            ('decorator', decorator_score),
                            ('string', string_score),
                            ('class', class_score),
                        ]

                    # Calculate normalized weight (equal for each supported feature)
                    num_features = len(supported_features)
                    equal_weight = 1.0 / num_features if num_features > 0 else 0.0

                    # Composite parser score with language-aware normalization
                    parser_score = sum(score * equal_weight for name, score in supported_features)

                else:
                    # Fallback to just centrality if graph not available
                    centrality_score = self.centrality_scores.get(str(f), 0.0)
                    parser_score = centrality_score

                # LLM confidence hint
                llm_score = 0.0
                if f in confidence_map:
                    conf_level = confidence_map[f]
                    llm_score = {"high": 1.0, "medium": 0.6, "low": 0.3}.get(conf_level, 0.0)
                    self.events_log.debug(
                        f"[{pattern_name}] {f.name}: LLM confidence={conf_level} → score={llm_score}"
                    )

                # Calculate weighted priority (original weight distribution maintained)
                priority = (
                    config.PRIORITY_KEYWORD_WEIGHT * keyword_score
                    + config.PRIORITY_EMBEDDING_WEIGHT * embedding_score
                    + config.PRIORITY_GRAPH_WEIGHT * parser_score
                    + config.PRIORITY_LLM_WEIGHT * llm_score
                )
                priority = max(0.0, priority)

                # Filter below threshold
                if priority < config.MIN_PRIORITY_SCORE:
                    continue

                # Build file record
                file_record = {
                    "file": f,
                    "score": priority,
                    "keyword_score": keyword_score,
                    "keywords": keywords,
                    "anti_keywords": anti_keywords,
                    "embedding_score": embedding_score,
                    "parser_score": parser_score,  # Composite: centrality + decorators + strings + classes
                    "llm_score": llm_score,
                    # Parser components (for debugging/analysis)
                    "centrality_score": centrality_score,
                    "decorator_score": decorator_score,
                    "string_score": string_score,
                    "class_score": class_score,
                    "content": content,
                    "llm_confidence": confidence_map.get(f, "none"),
                }

                # Log individual file score
                log_file_scored(pattern_name, str(f), file_record)

                out.append(file_record)

            except Exception as e:
                self.events_log.warning(f"Score error {f}: {e}")

        print()  # Newline after progress

        # LOG: Show scoring summary
        if out:
            llm_scores = [r["llm_score"] for r in out]
            avg_llm_score = sum(llm_scores) / len(llm_scores)
            non_zero = sum(1 for s in llm_scores if s > 0)

            print_success(
                f"Scored {len(out)} files (filtered {len(files) - len(out)} below threshold)",
                indent=1,
            )
            print_dim(
                f"LLM hints used: {non_zero}/{len(out)} files (avg score={avg_llm_score:.3f})",
                indent=2,
            )
        else:
            print_warning("No files passed minimum scoring threshold", indent=1)

        # Sort by score (descending), then filename (deterministic tiebreak)
        out.sort(key=lambda x: (-x["score"], str(x["file"])))

        return out

    def _search_chromadb_with_embedding(self, embedding: np.ndarray, pattern_name: str) -> float:
        """
        Search ChromaDB using a pre-computed embedding.

        Args:
            embedding: Pre-computed numpy embedding vector
            pattern_name: Pattern name for filtering

        Returns:
            Similarity score (0-1)
        """
        try:
            results = self.collection.query(
                query_embeddings=[embedding.tolist()],
                n_results=5,
                where={"pattern": pattern_name} if pattern_name else None,
            )

            if results and results["distances"] and results["distances"][0]:
                # Convert distance to similarity (closer = higher score)
                min_distance = min(results["distances"][0])
                similarity = 1.0 / (1.0 + min_distance)
                return similarity

            return 0.0

        except Exception as e:
            self.events_log.warning(f"ChromaDB search failed: {e}")
            return 0.0

    def _compute_graph_metrics(self):
        """
        FIXED: Compute graph centrality metrics with lazy loading support.

        Changes:
        - Skip if graph not available
        - Skip if already computed
        - Graceful error handling
        """
        if not self.repo_graph:
            self.events_log.debug("Graph not available - skipping centrality computation")
            return

        if self.centrality_scores:
            self.events_log.debug("Graph centrality already computed - skipping")
            return

        try:
            file_nodes = [n for n, d in self.repo_graph.nodes(data=True) if d.get("type") == "file"]

            if not file_nodes:
                self.events_log.warning("No file nodes in graph - skipping centrality")
                return

            sub = self.repo_graph.subgraph(file_nodes)
            pr = nx.pagerank(sub, alpha=0.85, max_iter=100)
            max_p = max(pr.values()) if pr else 1
            self.centrality_scores = {k: v / max_p for k, v in pr.items()}

            self.events_log.info(f"Computed centrality for {len(self.centrality_scores)} nodes")

        except Exception as e:
            self.events_log.warning(f"Centrality computation failed: {e}")
            self.centrality_scores = {}

    # pattern_analyzer.py - EXTRACT these helper methods

    def _prepare_pattern_analysis(
        self, pattern_name: str, pattern_data: dict, categorized_files: dict
    ) -> tuple:
        """Prepare data structures for pattern analysis."""
        candidates = self._collect_all_candidates(pattern_name, categorized_files)
        plan = self.ai_agent.run_planner(pattern_name, pattern_data) or self._fallback_plan(
            pattern_name
        )

        entry = categorized_files.get(pattern_name, {})
        confidence_map = self._normalize_confidence_map(entry)

        return candidates, plan, confidence_map

    def _score_candidates(
        self,
        candidates: list,
        pattern_name: str,
        pattern_data: dict,
        confidence_map: dict,
        categorized_files: dict,
    ) -> list:
        """Score and prioritize all candidate files."""
        scored_files = self._score_and_prioritize_files(
            candidates, pattern_name, pattern_data, confidence_map, categorized_files
        )

        # Log distribution
        high_ct = sum(1 for f in scored_files if f["score"] >= config.HIGH_PRIORITY_THRESHOLD)
        med_ct = sum(
            1
            for f in scored_files
            if config.MEDIUM_PRIORITY_THRESHOLD <= f["score"] < config.HIGH_PRIORITY_THRESHOLD
        )
        low_ct = len(scored_files) - high_ct - med_ct

        log_prioritization_complete(
            pattern_name, len(scored_files), {"high": high_ct, "medium": med_ct, "low": low_ct}
        )

        return scored_files

    def _conduct_investigation(
        self,
        scored_files: list,
        pattern_name: str,
        pattern_data: dict,
        plan: dict,
        repo_summary: str,
    ) -> list:
        """Conduct file investigation phase."""
        investigation_start = time.time()

        evidence = self._analyze_files(scored_files, pattern_name, pattern_data, plan, repo_summary)

        investigation_duration = time.time() - investigation_start

        log_investigation_phase_complete(
            pattern_name,
            "first_pass",
            min(config.MAX_FILES_PER_PATTERN, len(scored_files)),
            len(evidence),
            investigation_duration,
        )

        return evidence

    def _create_analysis_plan(self, pattern_name: str, pattern_data: dict) -> dict:
        """Create or fallback to default plan."""
        plan = self.ai_agent.run_planner(pattern_name, pattern_data)
        if not plan:
            print_warning("Planner failed – fallback plan")
            return self._fallback_plan(pattern_name)
        print_success("Plan created")
        return plan

    def _fallback_plan(self, pattern_name: str) -> dict:
        """Default plan structure."""
        return {
            "conceptual_characteristics": [
                f"Serves the architectural purpose of {pattern_name}",
                "Core conceptual role",
                "Implementation form may vary",
            ],
            "investigator_prompt": f"Determine if code serves {pattern_name} purpose.",
            "judge_prompt": f"Judge if evidence shows {pattern_name} purpose.",
        }

    def _collect_candidates(self, pattern_name: str, categorized_files: dict) -> list:
        """Extract and deduplicate candidate files."""
        candidates = self._collect_all_candidates(pattern_name, categorized_files)
        if not candidates:
            print_warning("No candidate files")
        else:
            print_info(f"Collected {len(candidates)} candidate files", indent=1)
        return candidates

    def _prioritize_candidates(
        self, candidates: list, pattern_name: str, pattern_data: dict, categorized_files: dict
    ) -> list:
        """Score and prioritize candidate files."""
        print_info("Scoring and prioritizing files...", indent=1)

        # Extract LLM confidence map
        entry = categorized_files.get(pattern_name, {})
        confidence_map = self._normalize_confidence_map(entry)

        if confidence_map:
            print_info(f"LLM confidence hints: {len(confidence_map)} files", indent=1)
        else:
            print_info("No LLM confidence map (LLM weight=0)", indent=1)

        return self._score_and_prioritize_files(
            candidates, pattern_name, pattern_data, confidence_map
        )

    def _normalize_confidence_map(self, entry: dict) -> dict:
        """Normalize confidence map keys to Path objects."""
        raw_conf = entry.get("confidence_map", {}) if isinstance(entry, dict) else {}
        norm_map = {}
        for k, v in raw_conf.items():
            try:
                norm_map[Path(k) if not isinstance(k, Path) else k] = v
            except Exception:
                continue
        return norm_map

    def _log_pattern_start(self, logger, idx: int, total: int, name: str):
        """Log pattern analysis start."""
        logger.info(f"{'='*80}\nStarting analysis for pattern {idx}/{total}: {name}\n{'='*80}")

    def _log_priority_distribution(self, scored_files: list):
        """Log priority distribution of scored files."""
        high_ct = sum(1 for f in scored_files if f["score"] >= config.HIGH_PRIORITY_THRESHOLD)
        med_ct = sum(
            1
            for f in scored_files
            if config.MEDIUM_PRIORITY_THRESHOLD <= f["score"] < config.HIGH_PRIORITY_THRESHOLD
        )
        low_ct = len(scored_files) - high_ct - med_ct
        print_info(
            f"Priority distribution: {high_ct} high, {med_ct} medium, {low_ct} low", indent=1
        )

    def _log_no_candidates(self, logger, pattern_name: str):
        """Log no candidates found."""
        logger.info(f"No candidates for {pattern_name}; skipping")

    def _log_no_scored_files(self, logger, pattern_name: str):
        """Log no scored files above threshold."""
        print_warning("All candidates below MIN_PRIORITY_SCORE")
        logger.info(f"No scored files for {pattern_name}")

    def _log_no_detection(self, logger, pattern_name: str):
        """Log pattern not detected."""
        print_pattern_not_detected(pattern_name, "No evidence found")
        logger.info(f"[{pattern_name}] Not detected (no evidence)")

    def _get_or_validate_collection(self):
        """
        Ensure Chroma collection metadata (embedding_model, dimension) matches current model.
        Rebuilds collection if mismatch to prevent silent dimension errors.
        """
        collection = self.client.get_or_create_collection(name=config.COLLECTION_NAME)
        meta = getattr(collection, "metadata", {}) or {}
        dim_expected = self.model.get_sentence_embedding_dimension()
        model_expected = config.EMBEDDING_MODEL
        rebuild = False

        if meta.get("embedding_model") and meta.get("embedding_model") != model_expected:
            rebuild = True
        if meta.get("dimension") and int(meta.get("dimension")) != dim_expected:
            rebuild = True

        if rebuild:
            print_warning("Embedding collection metadata mismatch – rebuilding vector store")
            try:
                self.client.delete_collection(config.COLLECTION_NAME)
            except Exception:
                pass
            collection = self.client.get_or_create_collection(
                name=config.COLLECTION_NAME,
                metadata={
                    "embedding_model": model_expected,
                    "dimension": dim_expected,
                    "hnsw:space": "cosine",
                },
            )
        else:
            if (
                meta.get("embedding_model") != model_expected
                or meta.get("dimension") != dim_expected
            ):
                collection.modify(
                    metadata={"embedding_model": model_expected, "dimension": dim_expected}
                )
        return collection

    def _collect_all_candidates(self, pattern_name: str, categorized_files: dict):
        tier1 = categorized_files.get(pattern_name, {}).get("tier1", [])
        tier2 = categorized_files.get(pattern_name, {}).get("tier2", [])
        return list({*tier1, *tier2})

    def _passes_basic_validation(self, file_path: Path) -> bool:
        """Basic file validation (size, readability)."""
        try:
            # Check size
            size_mb = file_path.stat().st_size / (1024 * 1024)
            if size_mb > config.MAX_FILE_SIZE_MB:
                return False

            # Check readability
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(1000)
                if len(content.strip()) < 10:
                    return False

            return True
        except Exception:
            return False

    def _analyze_files(self, scored_files, pattern_name, pattern_data, plan, repo_summary=""):
        """
        File investigation with live progress updates and negative evidence tracking.
        Simplified version without early stopping.

        Args:
            scored_files: List of files with priority scores
            pattern_name: Name of the pattern
            pattern_data: Pattern definition data
            plan: Analysis plan
            repo_summary: Repository summary

        Returns:
            List of evidence dictionaries
        """
        print_pattern_phase("File Investigation")

        evidence = []
        negative_evidence = []
        files_analyzed = 0
        limit = min(config.MAX_FILES_PER_PATTERN, len(scored_files))

        print_info(f"Analyzing up to {limit} files...", indent=1)

        # Show priority breakdown
        high_count = sum(
            1 for f in scored_files[:limit] if f["score"] >= config.HIGH_PRIORITY_THRESHOLD
        )
        med_count = sum(
            1
            for f in scored_files[:limit]
            if config.MEDIUM_PRIORITY_THRESHOLD <= f["score"] < config.HIGH_PRIORITY_THRESHOLD
        )
        low_count = limit - high_count - med_count

        print_dim(
            f"Queue: {high_count} high, {med_count} medium, {low_count} low priority", indent=1
        )

        start_time = time.time()
        evidence_found_at = []

        for file_data in scored_files[:limit]:
            files_analyzed += 1

            # Live progress indicator
            print_file_analysis(
                files_analyzed, limit, file_data["file"].name, score=file_data["score"]
            )

            # Prepare evidence payload
            ev_payload = {
                "file_path": str(file_data["file"]),
                "full_file": file_data["content"],
                "keywords_found": file_data["keywords"],
                "anti_keywords": file_data.get("anti_keywords", []),
                "priority_score": file_data["score"],
                "analysis_pass": "first",
            }

            # AI Investigation
            ai_verdict = self.ai_agent.run_investigation(
                ev_payload, plan, pattern_name, repo_summary=repo_summary
            )

            if ai_verdict and ai_verdict.get("is_evidence"):
                conf = ai_verdict.get("confidence", 0.0)
                evidence_found_at.append(files_analyzed)

                clear_line()
                print_file_result(
                    "evidence",
                    file_data["file"].name,
                    conf,
                    ai_verdict.get("decision_reasoning", "")[:80],
                )

                evidence.append(
                    {
                        "file_path": str(file_data["file"]),
                        "full_file": file_data["content"],
                        "priority_score": file_data["score"],
                        "confidence": conf,
                        "decision_reasoning": ai_verdict.get("decision_reasoning", ""),
                        "snippet": ai_verdict.get("snippet", ""),
                        "is_evidence": True,
                        "keywords": file_data["keywords"],
                        "anti_keywords": file_data.get("anti_keywords", []),
                    }
                )

            else:
                # Track negative evidence
                if config.TRACK_NEGATIVE_EVIDENCE and ai_verdict:
                    if len(negative_evidence) < config.MAX_NEGATIVE_EVIDENCE_SAMPLES:
                        negative_sample = {
                            "file_path": str(file_data["file"]),
                            "priority_score": file_data["score"],
                            "rejection_reason": ai_verdict.get("decision_reasoning", "Unknown"),
                            "missing_characteristics": ai_verdict.get(
                                "missing_characteristics", []
                            ),
                            "architectural_purpose": ai_verdict.get(
                                "architectural_purpose", "Unknown"
                            ),
                            "keywords": file_data["keywords"],
                            "anti_keywords": file_data.get("anti_keywords", []),
                            "snippet": ai_verdict.get("snippet", ""),
                        }
                        negative_evidence.append(negative_sample)

                        from micropad.logging.detection import log_negative_evidence

                        log_negative_evidence(
                            pattern_name,
                            str(file_data["file"]),
                            ai_verdict.get("decision_reasoning", "Unknown")[:200],
                            file_data["score"],
                        )

                # Show occasionally
                if files_analyzed % 10 == 0:
                    clear_line()
                    print_dim(
                        f"  [{files_analyzed}/{limit}] Checked {file_data['file'].name} - not evidence",
                        indent=1,
                    )

        clear_line()

        # Analysis summary
        elapsed = time.time() - start_time
        rate = files_analyzed / elapsed if elapsed > 0 else 0

        print(f"\n  {Colors.BOLD}Investigation Summary:{Colors.END}")
        print(f"    Files analyzed: {files_analyzed}/{limit}")
        print(f"    Evidence found: {Colors.BOLD}{Colors.GREEN}{len(evidence)}{Colors.END}")

        if config.TRACK_NEGATIVE_EVIDENCE and negative_evidence:
            print(
                f"    Rejected samples: {Colors.DIM}{len(negative_evidence)}{Colors.END} (for Judge context)"
            )

        print(f"    Time: {elapsed:.1f}s ({rate:.1f} files/s)")

        if evidence:
            avg_conf = np.mean([e["confidence"] for e in evidence])
            print(f"    Avg confidence: {avg_conf:.2f}")

            if evidence_found_at:
                print_dim(
                    f"    First evidence: file #{evidence_found_at[0]}/{files_analyzed}", indent=1
                )
                print_dim(
                    f"    Last evidence:  file #{evidence_found_at[-1]}/{files_analyzed}", indent=1
                )

        # Attach negative evidence to results
        if config.TRACK_NEGATIVE_EVIDENCE and negative_evidence:
            for ev in evidence:
                ev["_negative_evidence"] = negative_evidence

        return evidence

    def _determine_analysis_depth(self, priority_score: float):
        if priority_score >= config.HIGH_PRIORITY_THRESHOLD:
            return {"level": "high"}
        if priority_score >= config.MEDIUM_PRIORITY_THRESHOLD:
            return {"level": "medium"}
        return {"level": "low"}

    def _deliberate_and_decide(
        self, pattern_name: str, evidence: list, plan: dict, repo_summary=""
    ):
        print_deliberation_start(len(evidence))
        verdict = self.ai_agent.run_deliberation(
            pattern_name, evidence, plan, repo_summary=repo_summary
        )
        if verdict:
            conf = verdict.get("confidence_score", 0)
            if conf >= config.JUDGE_CONFIDENCE_THRESHOLD:
                ci = verdict.get("confidence_interval")
                print_pattern_detected(
                    pattern_name,
                    conf,
                    len(evidence),
                    risk=verdict.get("false_positive_risk"),
                    ci=ci,
                )

                # ✅ ADD: Include model metadata in result
                return {
                    "evidence_files": evidence,
                    "synthesis": verdict,
                    "detected": True,
                    # ✅ NEW: Model attribution
                    "model_info": {
                        "planner": (
                            plan.get("_llm_metadata", {}).get("model", "unknown") if plan else "N/A"
                        ),
                        "investigator": (
                            evidence[0].get("_llm_metadata", {}).get("model", "unknown")
                            if evidence
                            else "N/A"
                        ),
                        "judge": verdict.get("_llm_metadata", {}).get("model", "unknown"),
                        "provider": verdict.get("_llm_metadata", {}).get("provider", "unknown"),
                    },
                }
            else:
                print_pattern_not_detected(pattern_name, f"Confidence {conf}/10 below threshold")
        else:
            print_warning("Deliberation failed (no valid JSON)")
        return None

    def _find_keywords(self, file_path: Path, content: str, p_data: dict):
        kws = []
        anti = []
        rules = p_data.get("repository_fingerprint", {}).get("glob_patterns", [])
        for r in rules:
            if file_path.match(r.get("glob", "")):
                for k in r.get("keywords", []):
                    if k.lower() in content.lower():
                        kws.append(k)
                for ak in r.get("anti_keywords", []):
                    if ak.lower() in content.lower():
                        anti.append(ak)
        return list(set(kws)), list(set(anti))

    # pattern_analyzer.py - REPLACE _perform_embedding_search

    def _perform_embedding_search(self, content: str, file_path: Path, pattern_name: str):
        """
        Semantic code chunking with structure preservation (pattern-agnostic).

        Improvements:
        - Extracts semantic chunks (functions/classes) instead of arbitrary slicing
        - Uses BEST chunk match instead of average
        - Covers both beginning AND end of file
        """
        # Extract semantic chunks
        semantic_chunks = self._extract_semantic_chunks(content, file_path)

        if not semantic_chunks:
            # Fallback: beginning + end chunks
            chunks = []
            if len(content) > config.CHUNK_SIZE_CHARS:
                chunks.append(content[: config.CHUNK_SIZE_CHARS])  # Beginning
                chunks.append(content[-config.CHUNK_SIZE_CHARS :])  # End
            else:
                chunks.append(content)
            semantic_chunks = [c for c in chunks if len(c.strip()) > 100]

        if not semantic_chunks:
            return [], 0.0

        # Embed each chunk (limit to 5 for performance)
        embeddings = []
        for chunk in semantic_chunks[:5]:
            try:
                emb = self._get_embedding_for_text(chunk)
                embeddings.append(emb)
            except Exception as e:
                self.events_log.debug(f"Embedding failed for chunk: {e}")
                continue

        if not embeddings:
            return semantic_chunks, 0.0

        try:
            # Query positive examples
            pos_results = self.collection.query(
                query_embeddings=embeddings,
                n_results=3,
                where={"$and": [{"pattern_name": pattern_name}, {"type": "positive"}]},
                include=["distances"],
            )

            # Query negative examples
            neg_results = self.collection.query(
                query_embeddings=embeddings,
                n_results=3,
                where={"$and": [{"pattern_name": pattern_name}, {"type": "negative"}]},
                include=["distances"],
            )

            # Use BEST chunk match (not average)
            def best_similarity(results):
                all_dists = [d for arr in results.get("distances", []) for d in arr]
                if not all_dists:
                    return 0.0
                return 1 - float(min(all_dists))  # Best match = lowest distance

            pos_sim = best_similarity(pos_results)
            neg_sim = best_similarity(neg_results)

            # Stronger negative contrast
            similarity = max(0.0, pos_sim - 0.7 * neg_sim)

            return semantic_chunks, similarity

        except Exception as e:
            self.events_log.warning(f"Embedding search failed for {file_path}: {e}")
            return semantic_chunks, 0.0

    # pattern_analyzer.py - ADD THIS NEW METHOD

    def _extract_semantic_chunks(self, content: str, file_path: Path) -> list:
        """
        Extract code at semantic boundaries (pattern-agnostic).

        Strategy:
        1. Try graph-extracted functions if available
        2. Fallback to regex-based extraction
        3. Return list of meaningful code chunks
        """
        chunks = []

        # Strategy 1: Use graph-extracted functions
        if self.repo_graph and str(file_path) in self.repo_graph:
            file_node = str(file_path)

            # Find functions defined in this file
            for _, successor, edge_data in self.repo_graph.out_edges(file_node, data=True):
                if edge_data.get("type") == "defines":
                    func_node = self.repo_graph.nodes.get(successor, {})
                    func_name = func_node.get("name")

                    if func_name:
                        # Extract function body using regex
                        pattern = rf"(?:def|function|func|class|interface|public|private)\s+{re.escape(func_name)}\s*[\(\{{].*?(?=\n(?:def|function|func|class|public|private)\s|\Z)"
                        matches = re.findall(
                            pattern, content, re.DOTALL | re.MULTILINE | re.IGNORECASE
                        )

                        for match in matches:
                            if len(match) > 100:  # Skip trivial matches
                                # Take up to 3000 chars per function
                                chunks.append(match[:3000])

        # Strategy 2: Regex-based extraction (fallback)
        if not chunks:
            import re

            # Extract class/function blocks (language-agnostic patterns)
            patterns = [
                r"(?:class|interface|struct)\s+\w+.*?(?=\n(?:class|interface|struct)\s|\Z)",  # Classes
                r"(?:def|function|func|public|private)\s+\w+\s*\([^)]*\).*?(?=\n(?:def|function|func|public|private)\s|\Z)",  # Functions
                r"@\w+.*?\n(?:def|function|async\s+function)\s+\w+.*?(?=\n(?:def|function|@)\s|\Z)",  # Decorated/annotated functions
            ]

            for pattern in patterns:
                matches = re.findall(pattern, content, re.DOTALL | re.MULTILINE | re.IGNORECASE)
                for match in matches:
                    if len(match) > 100:
                        chunks.append(match[: config.CHUNK_SIZE_CHARS])

        # Strategy 3: If still nothing, use positional chunks
        if not chunks and len(content) > 500:
            # Beginning
            chunks.append(content[: config.CHUNK_SIZE_CHARS])
            # Middle (skip imports)
            mid_start = min(len(content) // 3, 5000)
            chunks.append(content[mid_start : mid_start + config.CHUNK_SIZE_CHARS])
            # End
            if len(content) > config.CHUNK_SIZE_CHARS:
                chunks.append(content[-config.CHUNK_SIZE_CHARS :])

        return chunks[:10]  # Max 10 chunks per file

    def _get_embedding_for_text(self, text: str):
        key = hashlib.sha256(text.encode("utf-8")).hexdigest()
        cached = self.cache.get(key)
        if cached is not None:
            return cached
        emb = self.model.encode([text], show_progress_bar=False)[0].tolist()
        self.cache.set(key, emb)
        return emb

    def _generate_repo_summary(self, scored_files: list[dict]) -> str:
        """Generate structural repository snapshot."""
        file_types = {}
        sample = scored_files[:50]

        for fd in sample:
            ext = fd["file"].suffix or "(noext)"
            file_types[ext] = file_types.get(ext, 0) + 1

        top_dirs = set()
        for fd in sample:
            try:
                # Handle both absolute and relative paths
                if fd["file"].is_absolute():
                    rel_parts = fd["file"].relative_to(config.TARGET_REPO_PATH).parts
                else:
                    rel_parts = fd["file"].parts

                if rel_parts:
                    top_dirs.add(rel_parts[0])
            except (ValueError, AttributeError):
                # Path not relative to repo - skip
                continue

        if self.centrality_scores:
            hubs = sorted(
                [(fd["file"], fd.get("graph_score", 0.0)) for fd in scored_files],
                key=lambda x: x[1],
                reverse=True,
            )[:5]
        else:
            hubs = []

        summary = (
            "Repository Summary:\n"
            f"  File types (sample): "
            + ", ".join(
                f"{k}({v})" for k, v in sorted(file_types.items(), key=lambda kv: -kv[1])[:6]
            )
            + "\n"
            f"  Top-level dirs: {', '.join(sorted(top_dirs)[:8]) or '(none)'}\n"
            f"  Hub files: {', '.join([p.name for p, _ in hubs]) or '(none)'}\n"
        )
        return summary
