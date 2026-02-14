from __future__ import annotations

import logging
import sys
import time  # ✅ ADD THIS
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set

import yaml

from micropad.config import settings as config

# ✅ ADD THIS IMPORT BLOCK
from micropad.logging.ui import (
    Colors,
    print_dim,
    print_error,
    print_info,
    print_section,
    print_success,
    print_warning,
)


class RepositoryParser:
    def __init__(self):
        print_section("Repository Parser Initialization")

        print_info("Validating repository path...")
        self.repo_path: Path = config.TARGET_REPO_PATH
        self.events_log = logging.getLogger("events")  # ✅ ADD THIS LINE
        self._validate_repo_path()
        print_success(f"Repository: {self.repo_path.name}")

        print_info("Loading pattern definitions...")
        load_start = time.time()
        self.patterns: Dict[str, dict] = self._load_patterns()
        load_time = time.time() - load_start
        print_success(f"Loaded {len(self.patterns)} patterns ({load_time:.2f}s)")

        # Show pattern names
        if self.patterns:
            print_dim("Patterns loaded:", indent=1)
            for i, name in enumerate(sorted(self.patterns.keys()), 1):
                print_dim(f"{i:2d}. {name}", indent=2)

        print_info("Discovering repository files...")
        scan_start = time.time()
        self.scannable_files: Set[Path] = self._get_scannable_files()
        scan_time = time.time() - scan_start
        print_success(f"Found {len(self.scannable_files)} files ({scan_time:.2f}s)")

        # File type breakdown
        self._print_file_breakdown()

    # repository_parser.py - ADD THIS METHOD to RepositoryParser class

    def _validate_pattern_definition(self, pattern_name: str, data: dict) -> tuple[bool, list[str]]:
        """
        Validate pattern YAML structure.

        Returns:
            (is_valid, error_messages)
        """
        errors = []

        # Required top-level fields
        required_fields = ["pattern_name", "description", "repository_fingerprint"]
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")

        # Check description is non-empty
        if "description" in data:
            desc = data["description"]
            if not isinstance(desc, str) or not desc.strip():
                errors.append("Empty or invalid description")

        # Check repository_fingerprint structure
        if "repository_fingerprint" in data:
            rf = data["repository_fingerprint"]

            if not isinstance(rf, dict):
                errors.append("repository_fingerprint must be a dict")
            else:
                if "glob_patterns" not in rf:
                    errors.append("Missing glob_patterns in repository_fingerprint")
                else:
                    globs = rf["glob_patterns"]

                    if not isinstance(globs, list):
                        errors.append("glob_patterns must be a list")
                    elif len(globs) == 0:
                        errors.append("glob_patterns is empty (need at least one glob rule)")
                    else:
                        # Validate each glob rule
                        for i, glob_rule in enumerate(globs):
                            if not isinstance(glob_rule, dict):
                                errors.append(f"glob_patterns[{i}] must be a dict")
                                continue

                            # ✅ FIXED: Only require 'glob' field
                            # analysis_priority is OPTIONAL (your YAMLs use search_method instead)
                            if "glob" not in glob_rule:
                                errors.append(f"glob_patterns[{i}] missing 'glob' field")
                            elif (
                                not isinstance(glob_rule["glob"], str)
                                or not glob_rule["glob"].strip()
                            ):
                                errors.append(f"glob_patterns[{i}] has empty glob string")

                            # ✅ NEW: Validate your actual structure (search_method + keywords)
                            if "search_method" in glob_rule:
                                if glob_rule["search_method"] not in [
                                    "keyword",
                                    "embedding",
                                    "hybrid",
                                ]:
                                    errors.append(
                                        f"glob_patterns[{i}] invalid search_method: {glob_rule['search_method']}"
                                    )

                            # ✅ OPTIONAL: Validate keywords/anti_keywords if present
                            for kw_field in ["keywords", "anti_keywords"]:
                                if kw_field in glob_rule:
                                    if not isinstance(glob_rule[kw_field], list):
                                        errors.append(
                                            f"glob_patterns[{i}] {kw_field} must be a list"
                                        )
                                    else:
                                        # Check all keywords are non-empty strings
                                        for j, kw in enumerate(glob_rule[kw_field]):
                                            if not isinstance(kw, str) or not kw.strip():
                                                errors.append(
                                                    f"glob_patterns[{i}] {kw_field}[{j}] is empty or invalid"
                                                )

        # Check examples exist and are non-empty
        for ex_type in ["positive_examples", "negative_examples"]:
            if ex_type in data:
                examples = data[ex_type]
                if not isinstance(examples, list):
                    errors.append(f"{ex_type} must be a list")
                elif len(examples) == 0:
                    errors.append(f"{ex_type} is empty (should have at least 1 example)")
                else:
                    # Validate each example
                    for i, ex in enumerate(examples):
                        if not isinstance(ex, str):
                            errors.append(f"{ex_type}[{i}] must be a string")
                        elif not ex.strip():
                            errors.append(f"{ex_type}[{i}] is empty")
                        elif len(ex) < 20:
                            errors.append(
                                f"{ex_type}[{i}] is too short (< 20 chars) - provide meaningful examples"
                            )

        # Warn if no examples (not an error, but suspicious)
        if "positive_examples" not in data or not data["positive_examples"]:
            errors.append("WARNING: No positive_examples defined - detection may be less accurate")

        return len(errors) == 0, errors

    def _validate_repo_path(self):
        """Validate that the repository path exists and is a directory."""
        if not self.repo_path.exists():
            print_error(f"Repository path does not exist: {self.repo_path}")
            sys.exit(1)

        if not self.repo_path.is_dir():
            print_error(f"Repository path is not a directory: {self.repo_path}")
            sys.exit(1)

    # repository_parser.py - REPLACE _load_patterns method

    def _load_patterns(self) -> dict:
        """Load pattern definitions from YAML files with validation."""
        patterns: Dict[str, dict] = {}

        if not config.PATTERNS_DIR_PATH.is_dir():
            print_warning(f"Patterns directory not found: {config.PATTERNS_DIR_PATH}")
            return {}

        yaml_files = list(config.PATTERNS_DIR_PATH.glob("*.yaml"))

        if not yaml_files:
            print_error("No pattern YAML files found!")
            return {}

        print_info(f"Found {len(yaml_files)} pattern files", indent=1)

        validation_failures = 0

        for yaml_file in yaml_files:
            try:
                with open(yaml_file, "r", encoding="utf-8") as fp:
                    data = yaml.safe_load(fp)

                if not isinstance(data, dict):
                    print_warning(f"Invalid YAML structure in {yaml_file.name}", indent=2)
                    validation_failures += 1
                    continue

                pname = data.get("pattern_name")
                if not pname:
                    print_warning(f"No pattern_name in {yaml_file.name}", indent=2)
                    validation_failures += 1
                    continue

                # ✅ NEW: Validate pattern definition
                is_valid, validation_errors = self._validate_pattern_definition(pname, data)

                if not is_valid:
                    print_error(f"Pattern '{pname}' validation failed:", indent=2)
                    for error in validation_errors:
                        if error.startswith("WARNING"):
                            print_warning(error.replace("WARNING: ", ""), indent=3)
                        else:
                            print_dim(f"• {error}", indent=3)

                    # Check if errors are all warnings
                    critical_errors = [e for e in validation_errors if not e.startswith("WARNING")]
                    if critical_errors:
                        print_error(f"Skipping pattern '{pname}' due to critical errors", indent=3)
                        validation_failures += 1
                        continue
                    else:
                        print_warning(f"Loading pattern '{pname}' with warnings", indent=3)

                patterns[pname] = data
                print_success(f"Loaded: {pname}", indent=2)

            except yaml.YAMLError as e:
                print_error(f"YAML syntax error in {yaml_file.name}: {e}", indent=2)
                validation_failures += 1
                logging.getLogger("events").error(f"YAML error in {yaml_file.name}: {e}")

            except Exception as e:
                print_error(f"Failed to load {yaml_file.name}: {e}", indent=2)
                validation_failures += 1
                logging.getLogger("events").error(f"Pattern load error {yaml_file.name}: {e}")

        # Summary
        if validation_failures > 0:
            print_warning(f"{validation_failures} patterns failed validation", indent=1)

        if not patterns:
            print_error("No valid patterns loaded - cannot proceed!")
            import sys

            sys.exit(1)

        return patterns

    def _print_file_breakdown(self):
        """Print breakdown of discovered files by extension."""
        from collections import Counter

        extensions = Counter(f.suffix or "(no extension)" for f in self.scannable_files)

        print_dim("File type distribution:", indent=1)
        for ext, count in extensions.most_common(10):
            bar_width = int(count / len(self.scannable_files) * 30)
            bar = "█" * bar_width + "░" * (30 - bar_width)
            print_dim(f"  {ext:20s} [{bar}] {count:4d} files", indent=2)

        if len(extensions) > 10:
            others = sum(count for ext, count in extensions.most_common()[10:])
            print_dim(f"  {'(other types)':20s} {'':30s} {others:4d} files", indent=2)

    # ----------------------------------------------------------------------------------
    # Public API
    # ----------------------------------------------------------------------------------
    # repository_parser.py - UPDATE get_categorized_files_with_llm

    def get_categorized_files_with_llm(self) -> dict:
        """Multi-stage categorization with detailed progress and LLM selection visibility."""
        print_section("LLM-Powered File Categorization")
        print_info("Strategy: Path-based → YAML fallback")

        try:
            from micropad.llm.helpers import call_llm_for_categorization
        except ImportError as e:
            print_error(f"LLM helper import failed: {e}")
            print_warning("Falling back to YAML-only categorization")
            return self.get_categorized_files()

        categorized = {}

        # Prepare stable file list
        print_info("Preparing file index...")
        file_tree = self._get_file_tree_string()
        print_success(f"File tree ready ({len(file_tree)} chars)")

        # Process each pattern
        total_patterns = len(self.patterns)
        print(f"\n{Colors.BOLD}Categorizing files for {total_patterns} patterns...{Colors.END}\n")

        for idx, (pattern_name, pattern_data) in enumerate(self.patterns.items(), 1):
            pattern_start = time.time()

            print(f"  [{idx:2d}/{total_patterns}] {Colors.BOLD}{pattern_name}{Colors.END}")

            # Extract YAML hints
            yaml_hints = self._extract_yaml_hints(pattern_name, pattern_data)
            hint_summary = f"{len(yaml_hints.get('high_priority_globs', []))} high-priority globs"
            print_dim(f"YAML hints: {hint_summary}", indent=2)

            # ---- Strategy 1: Path-based categorization ----
            print_info("Strategy 1/2: Path-based categorization...", indent=2)
            try:
                path_start = time.time()
                path_res = call_llm_for_categorization(
                    file_tree=file_tree,
                    pattern_name=pattern_name,
                    pattern_description=pattern_data.get("description", ""),
                    yaml_hints=yaml_hints,
                )
                path_time = time.time() - path_start

                # ✅ NEW: Show what LLM returned
                llm_high = path_res.get("high_confidence", [])
                llm_med = path_res.get("medium_confidence", [])
                llm_low = path_res.get("low_confidence", [])

                print_dim(f"LLM categorized:", indent=3)
                print_dim(f"  High:   {len(llm_high)} files", indent=4)
                print_dim(f"  Medium: {len(llm_med)} files", indent=4)
                print_dim(f"  Low:    {len(llm_low)} files", indent=4)

                # ✅ NEW: Show sample files from each tier
                if llm_high:
                    print_dim("Sample high-confidence files:", indent=4)
                    for file_path in llm_high[:3]:
                        print_dim(f"• {file_path}", indent=5)
                    if len(llm_high) > 3:
                        print_dim(f"• ... and {len(llm_high) - 3} more", indent=5)

                if llm_med and len(llm_med) <= 5:
                    print_dim("Medium-confidence files:", indent=4)
                    for file_path in llm_med:
                        print_dim(f"• {file_path}", indent=5)
                elif llm_med:
                    print_dim(f"Medium-confidence: {len(llm_med)} files", indent=4)

                if llm_low and len(llm_low) <= 3:
                    print_dim("Low-confidence files:", indent=4)
                    for file_path in llm_low:
                        print_dim(f"• {file_path}", indent=5)
                elif llm_low:
                    print_dim(f"Low-confidence: {len(llm_low)} files", indent=4)

                # Resolve paths to Path objects
                rel_lookup = {str(f.relative_to(self.repo_path)): f for f in self.scannable_files}

                high = self._resolve_paths(llm_high, rel_lookup)
                med = self._resolve_paths(llm_med, rel_lookup)
                low = self._resolve_paths(llm_low, rel_lookup)

                # ✅ NEW: Show resolution success rate
                print_dim(f"Path resolution:", indent=3)
                print_dim(
                    f"  High:   {len(high)}/{len(llm_high)} resolved ({len(high)/len(llm_high)*100 if llm_high else 0:.0f}%)",
                    indent=4,
                )
                print_dim(
                    f"  Medium: {len(med)}/{len(llm_med)} resolved ({len(med)/len(llm_med)*100 if llm_med else 0:.0f}%)",
                    indent=4,
                )
                print_dim(
                    f"  Low:    {len(low)}/{len(llm_low)} resolved ({len(low)/len(llm_low)*100 if llm_low else 0:.0f}%)",
                    indent=4,
                )

                # ✅ NEW: Show which paths failed to resolve
                failed_high = set(llm_high) - {str(f.relative_to(self.repo_path)) for f in high}
                if failed_high:
                    print_warning(
                        f"{len(failed_high)} high-confidence paths failed to resolve", indent=4
                    )
                    print_dim("Failed paths:", indent=5)
                    for fp in list(failed_high)[:3]:
                        print_dim(f"• {fp}", indent=6)
                    if len(failed_high) > 3:
                        print_dim(f"• ... and {len(failed_high) - 3} more", indent=6)

                if high or med or low:
                    print_success(
                        f"Path-based: {len(high)} high, {len(med)} med, {len(low)} low ({path_time:.2f}s)",
                        indent=3,
                    )
                else:
                    print_warning("Path-based returned empty after resolution", indent=3)

            except Exception as e:
                print_error(f"Path-based failed: {str(e)[:60]}", indent=3)
                import traceback

                print_dim(traceback.format_exc()[:200], indent=4)
                high, med, low = [], [], []

            # ---- Strategy 2: YAML fallback ----
            if not (high or med or low):
                print_info("Strategy 2/2: YAML glob fallback...", indent=2)
                yaml_start = time.time()
                yaml_only = self.get_categorized_files().get(pattern_name, {})
                high = yaml_only.get("tier1", [])
                med = yaml_only.get("tier2", [])
                low = []
                yaml_time = time.time() - yaml_start

                if high or med:
                    print_success(
                        f"YAML: {len(high)} high, {len(med)} med ({yaml_time:.2f}s)", indent=3
                    )

                    # ✅ NEW: Show YAML matches
                    if high:
                        print_dim("YAML high-priority matches:", indent=4)
                        for f in high[:3]:
                            print_dim(f"• {f.name}", indent=5)
                        if len(high) > 3:
                            print_dim(f"• ... and {len(high) - 3} more", indent=5)
                else:
                    print_warning("YAML also returned empty - check pattern globs!", indent=3)
                    # ✅ NEW: Show what globs were tried
                    print_dim(f"YAML globs tried:", indent=4)
                    for glob in yaml_hints.get("high_priority_globs", [])[:3]:
                        print_dim(f"• {glob}", indent=5)

                    # ✅ NEW: Test if globs match ANY files in repo
                    if yaml_hints.get("high_priority_globs"):
                        sample_glob = yaml_hints["high_priority_globs"][0]
                        matches = list(self.repo_path.glob(sample_glob))
                        if matches:
                            print_dim(
                                f"Note: glob '{sample_glob}' matches {len(matches)} files in repo",
                                indent=4,
                            )
                            print_dim("But they may be excluded by config.EXCLUDED_PATHS", indent=5)
                        else:
                            print_dim(
                                f"Note: glob '{sample_glob}' matches NO files in repo", indent=4
                            )

            # Build confidence map
            conf_map = {}
            for f in high:
                conf_map[f] = "high"
            for f in med:
                conf_map.setdefault(f, "medium")
            for f in low:
                conf_map.setdefault(f, "low")

            categorized[pattern_name] = {
                "tier1": high,
                "tier2": list({*med, *low}),
                "llm_confidence_map": conf_map,
            }

            pattern_time = time.time() - pattern_start
            total_files = len(high) + len(med) + len(low)

            if total_files > 0:
                print_success(
                    f"Complete: {total_files} files categorized ({pattern_time:.2f}s)", indent=2
                )
            else:
                print_error(f"Complete: 0 files found ({pattern_time:.2f}s)", indent=2)

        # Summary
        grand_total = sum(len(v["tier1"]) + len(v["tier2"]) for v in categorized.values())

        if grand_total == 0:
            print_error("All patterns returned empty!")
            print_warning("Debugging checklist:", indent=1)
            print_dim("1. Check if LLM is returning paths", indent=2)
            print_dim("2. Check if path resolution is working", indent=2)
            print_dim("3. Check if YAML globs match any files", indent=2)
            print_dim("4. Check pattern YAML files have glob_patterns defined", indent=2)

            # ✅ NEW: Show one pattern's YAML for debugging
            if self.patterns:
                sample_pattern = list(self.patterns.keys())[0]
                sample_data = self.patterns[sample_pattern]
                print_dim(f"\nSample pattern '{sample_pattern}' YAML:", indent=1)
                globs = sample_data.get("repository_fingerprint", {}).get("glob_patterns", [])
                if globs:
                    print_dim(f"  Has {len(globs)} glob rules", indent=2)
                    print_dim(f"  First glob: {globs[0].get('glob', 'N/A')}", indent=2)
                else:
                    print_error(f"  No glob_patterns defined!", indent=2)

            return self.get_categorized_files()

        print(
            f"\n{Colors.GREEN}✓{Colors.END} {Colors.BOLD}Categorization complete:{Colors.END} {grand_total} total file assignments"
        )
        return categorized

    def _resolve_paths(self, paths, lookup):
        """
        Enhanced path resolution with fuzzy matching.

        Strategy:
        1. Exact match (fast path)
        2. Case-insensitive match
        3. Suffix match (for partial paths like "gateway.py" → "src/services/gateway.py")
        4. Basename match (last resort)
        """
        out = []
        unresolved = []

        for p in paths:
            p_clean = p.strip()
            resolved = False

            # Strategy 1: Exact match
            if p_clean in lookup:
                out.append(lookup[p_clean])
                resolved = True
                continue

            # Strategy 2: Case-insensitive match
            p_lower = p_clean.lower()
            for lookup_path, path_obj in lookup.items():
                if lookup_path.lower() == p_lower:
                    out.append(path_obj)
                    resolved = True
                    break

            if resolved:
                continue

            # Strategy 3: Suffix match (LLM returned partial path)
            # Example: LLM says "services/gateway.py" but real path is "src/services/gateway.py"
            for lookup_path, path_obj in lookup.items():
                if lookup_path.endswith(p_clean) or lookup_path.endswith("/" + p_clean):
                    out.append(path_obj)
                    resolved = True
                    self.events_log.debug(
                        f"Resolved '{p_clean}' via suffix match to '{lookup_path}'"
                    )
                    break

            if resolved:
                continue

            # Strategy 4: Basename match (last resort)
            # Example: LLM says "gateway.py" but real path is "src/services/gateway/gateway.py"
            from pathlib import Path as _P

            p_basename = _P(p_clean).name

            for lookup_path, path_obj in lookup.items():
                if _P(lookup_path).name == p_basename:
                    out.append(path_obj)
                    resolved = True
                    self.events_log.debug(
                        f"Resolved '{p_clean}' via basename match to '{lookup_path}'"
                    )
                    break

            if not resolved:
                unresolved.append(p_clean)

        # Log unresolved paths for debugging
        if unresolved:
            self.events_log.warning(
                f"Could not resolve {len(unresolved)} LLM paths. "
                f"Examples: {', '.join(unresolved[:3])}"
            )

        return out

    def get_categorized_files(self) -> dict:
        """
        Deterministic YAML-only categorization using pattern glob rules.
        Output format matches LLM method but leaves confidence_map empty.
        """
        categorized = defaultdict(lambda: {"tier1": set(), "tier2": set()})
        for pattern_name, pattern_data in self.patterns.items():
            rules = pattern_data.get("repository_fingerprint", {}).get("glob_patterns", [])
            for file in self.scannable_files:
                for rule in rules:
                    glob_pattern = rule.get("glob", "")
                    if not glob_pattern:
                        continue
                    try:
                        if file.match(glob_pattern):
                            priority = rule.get("analysis_priority", "low")
                            target = (
                                categorized[pattern_name]["tier1"]
                                if priority == "high"
                                else categorized[pattern_name]["tier2"]
                            )
                            target.add(file)
                    except Exception:
                        continue

        output = {}
        for pname, tiers in categorized.items():
            output[pname] = {
                "tier1": sorted(tiers["tier1"]),
                "tier2": sorted(tiers["tier2"]),
                "confidence_map": {},
            }
        return output

    # ----------------------------------------------------------------------------------
    # Internal Helpers
    # ----------------------------------------------------------------------------------
    def _extract_yaml_hints(self, pattern_name: str, pattern_data: dict) -> dict:
        """
        Collect glob priorities, keywords, anti_keywords from the pattern definition.
        Returned dict is passed to LLM categorization prompts.
        """
        rules = pattern_data.get("repository_fingerprint", {}).get("glob_patterns", [])
        hints = {
            "high_priority_globs": [],
            "low_priority_globs": [],
            "keywords": [],
            "anti_keywords": [],
        }
        for rule in rules:
            glob = rule.get("glob", "")
            if not glob:
                continue
            priority = rule.get("analysis_priority", "low")
            if priority == "high":
                hints["high_priority_globs"].append(glob)
            else:
                hints["low_priority_globs"].append(glob)
            hints["keywords"].extend(rule.get("keywords", []))
            hints["anti_keywords"].extend(rule.get("anti_keywords", []))
        # Uniquify
        hints["keywords"] = list(dict.fromkeys(hints["keywords"]))
        hints["anti_keywords"] = list(dict.fromkeys(hints["anti_keywords"]))
        return hints

    def _get_file_tree_string(self) -> str:
        """Return a newline-delimited list of repository-relative file paths."""
        return "\n".join(str(f.relative_to(self.repo_path)) for f in sorted(self.scannable_files))

    def _get_scannable_files(self) -> Set[Path]:
        """Scan repository with progress indicator."""
        print_info("Enumerating all files...", indent=1)

        all_files = set()
        for p in self.repo_path.rglob("*"):
            if p.is_file():
                all_files.add(p)

        print_success(f"Found {len(all_files)} total files", indent=1)

        print_info("Applying exclusion rules...", indent=1)
        excluded = {f for pattern in config.EXCLUDED_PATHS for f in self.repo_path.glob(pattern)}

        print_dim(f"Excluded {len(excluded)} files", indent=2)

        scannable = all_files - excluded

        # Show what was excluded
        if excluded:
            from collections import Counter

            excluded_dirs = Counter(f.parent.name for f in excluded)
            print_dim("Top excluded directories:", indent=2)
            for dir_name, count in excluded_dirs.most_common(5):
                print_dim(f"  • {dir_name}: {count} files", indent=3)

        return scannable
