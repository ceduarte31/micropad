# repository_graph.py
import logging

# repository_graph.py - ADD these imports at the top
import time
from collections import defaultdict  # ✅ ADD THIS LINE
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import networkx as nx

from micropad.logging.ui import (
    Colors,
    print_dim,
    print_error,
    print_info,
    print_section,
    print_success,
    print_warning,
)
from micropad.repository.code_parsers import HeuristicParser, ParserFactory, TreeSitterParser

try:
    import tree_sitter_languages  # noqa

    TSL_MODULE = tree_sitter_languages
except ImportError:
    TSL_MODULE = None

try:
    from tree_sitter import Language as TSLanguage
    from tree_sitter import Parser, Query

    TREE_SITTER_NEW_API = True
except ImportError:
    from tree_sitter import Language, Parser

    TREE_SITTER_NEW_API = False

# --- Language Support Tiers ---
# Tier 1: Full code analysis (functions + calls + imports)
FULL_CODE_LANGUAGES = {
    ".py": {
        "name": "python",
        "function_query": "(function_definition name: (identifier) @function)",
        "call_query": "(call function: (identifier) @call)",
        "import_query": "[(import_statement) (import_from_statement)]",
    },
    ".js": {
        "name": "javascript",
        "function_query": "(function_declaration name: (identifier) @function)",
        "call_query": "(call_expression function: (identifier) @call)",
        "import_query": "[(import_statement) (call_expression function: (identifier) @require)]",
    },
    ".ts": {
        "name": "typescript",
        "function_query": "(function_declaration name: (identifier) @function)",
        "call_query": "(call_expression function: (identifier) @call)",
        "import_query": "(import_statement)",
    },
    ".java": {
        "name": "java",
        "function_query": "(method_declaration name: (identifier) @method)",
        "call_query": "(method_invocation name: (identifier) @call)",
        "import_query": "(import_declaration)",
    },
    ".go": {
        "name": "go",
        "function_query": "(function_declaration name: (identifier) @function)",
        "call_query": "(call_expression function: (identifier) @call)",
        "import_query": "(import_declaration)",
    },
    ".cs": {
        "name": "c_sharp",
        "function_query": "(method_declaration name: (identifier) @method)",
        "call_query": "(invocation_expression function: (identifier) @call)",
        "import_query": "(using_directive)",
    },
    ".rb": {
        "name": "ruby",
        "function_query": "(method name: (identifier) @function)",
        "call_query": "(call method: (identifier) @call)",
        "import_query": "(call method: (identifier) @require)",
    },
    ".php": {
        "name": "php",
        "function_query": "(function_definition name: (name) @function)",
        "call_query": "(function_call_expression function: (name) @call)",
        "import_query": "[(namespace_use_declaration) (include_expression)]",
    },
    ".sh": {
        "name": "bash",
        "function_query": "(function_definition name: (word) @function)",
        "call_query": "(command name: (command_name (word) @call))",
        "import_query": "(command name: (command_name) @source)",
    },
    ".rs": {
        "name": "rust",
        "function_query": "(function_item name: (identifier) @function)",
        "call_query": "(call_expression function: (identifier) @call)",
        "import_query": "(use_declaration)",
    },
}

# Tier 2: Structural parsing (imports/references only)
STRUCTURAL_LANGUAGES = {
    ".yaml": "yaml",
    ".yml": "yaml",
    ".json": "json",
    ".toml": "toml",
    ".hcl": "hcl",
    ".tf": "hcl",
    ".xml": "xml",
    "Dockerfile": "dockerfile",
    "Makefile": "make",
}

# Tier 3: Heuristic parsing only (regex-based)
HEURISTIC_EXTENSIONS = {
    ".properties",
    ".cfg",
    ".conf",
    ".ini",
    ".bicep",
    ".ps1",
    ".bat",
    ".gradle",
    "Procfile",
    "Tiltfile",
    ".service",
    "Vagrantfile",
    "Jenkinsfile",
    ".plist",
    ".nomad",
}

LANGUAGE_MAP: Dict[str, str] = {}
LANGUAGE_QUERIES: Dict[str, Dict[str, str]] = {}


def _initialize_languages():
    if not TSL_MODULE:
        print("⚠️ No tree-sitter language bundle. Only heuristic parsing will run.")
        return
    for ext, cfg in FULL_CODE_LANGUAGES.items():
        lang_name = cfg["name"]
        language = _load_language(lang_name)
        if language:
            LANGUAGE_MAP[ext] = lang_name
            LANGUAGE_QUERIES[lang_name] = {
                "functions": cfg["function_query"],
                "calls": cfg["call_query"],
                "imports": cfg["import_query"],
            }


def _load_language(lang_name: str):
    """
    Load tree-sitter language with multiple loading strategies.

    Attempts (in order):
    1. tree-sitter-languages package (bundled)
    2. Individual tree-sitter-X packages

    Returns:
        Language object if successful, None otherwise
    """
    if Parser is None:
        return None

    # Strategy 1: tree-sitter-languages (recommended - all-in-one package)
    try:
        import tree_sitter_languages

        # FIXED: Return directly - already correct type
        language = tree_sitter_languages.get_language(lang_name)
        return language

    except ImportError:
        logging.getLogger("events").debug(
            "tree-sitter-languages not installed - trying individual packages"
        )
    except Exception as e:
        logging.getLogger("events").debug(f"tree-sitter-languages failed for {lang_name}: {e}")

    # Strategy 2: Individual tree-sitter-X packages
    module_map = {
        "python": "tree_sitter_python",
        "javascript": "tree_sitter_javascript",
        "typescript": "tree_sitter_typescript",
        "java": "tree_sitter_java",
        "go": "tree_sitter_go",
        "c_sharp": "tree_sitter_c_sharp",
        "ruby": "tree_sitter_ruby",
        "php": "tree_sitter_php",
        "bash": "tree_sitter_bash",
        "rust": "tree_sitter_rust",
    }

    if lang_name not in module_map:
        return None

    try:
        import importlib

        mod = importlib.import_module(module_map[lang_name])

        # Try different attribute names
        for candidate in [
            f"language_{lang_name}",
            "language",
            f'language_{lang_name.replace("_", "")}',
            lang_name,
        ]:
            if hasattr(mod, candidate):
                try:
                    capsule = getattr(mod, candidate)()
                    if capsule:
                        if TREE_SITTER_NEW_API:
                            return TSLanguage(capsule)
                        else:
                            return Language(capsule)
                except Exception:
                    continue
    except Exception:
        pass

    return None


_initialize_languages()


class Indexer:
    def __init__(self, scannable_files: List[Path]):
        self.scannable_files = scannable_files
        self.repo_graph = nx.DiGraph()

        # FIXED: Initialize events_log FIRST
        self.events_log = logging.getLogger("events")
        self.functions_by_file = {}

        # Initialize parser factory
        from micropad.repository.code_parsers import LANGUAGE_MAP, LANGUAGE_QUERIES

        self.parser_factory = ParserFactory(
            language_map=LANGUAGE_MAP, language_queries=LANGUAGE_QUERIES
        )

        # Log language support status
        if LANGUAGE_MAP:
            self.events_log.info(f"Parser factory ready: {len(LANGUAGE_MAP)} languages available")
        else:
            self.events_log.warning(
                "Parser factory initialized but NO languages available! "
                "Only heuristic parsing will work."
            )

    def build_graph(self) -> nx.DiGraph:
        """Build graph with detailed progress tracking."""
        print_section("Code Knowledge Graph Construction")

        print_info(f"Processing {len(self.scannable_files)} files...")

        # Add file nodes
        print_info("Creating file nodes...", indent=1)
        for f in self.scannable_files:
            self.repo_graph.add_node(str(f), type="file")
        print_success(f"Added {self.repo_graph.number_of_nodes()} file nodes", indent=1)

        # Process files with progress bar
        print_info("Extracting code relationships...", indent=1)
        processed = 0
        errors = 0
        parser_counts = defaultdict(int)

        start_time = time.time()

        for f in self.scannable_files:
            try:
                parser = self.parser_factory.get_parser(f)
                parser_name = parser.__class__.__name__
                parser_counts[parser_name] += 1

                # ✅ ADD: Track if TreeSitterParser rejected the file
                if isinstance(parser, TreeSitterParser):
                    # TreeSitterParser tracks attempts internally
                    pass

                success = self._process_file(f)
                if not success:
                    errors += 1

            except Exception as e:
                errors += 1
                self.events_log.debug(f"Failed to process {f}: {e}")

            processed += 1

            # Progress indicator every 50 files
            if processed % 50 == 0:
                elapsed = time.time() - start_time
                rate = processed / elapsed
                remaining = (len(self.scannable_files) - processed) / rate

                print_dim(
                    f"  Progress: {processed}/{len(self.scannable_files)} "
                    f"({processed/len(self.scannable_files)*100:.0f}%) "
                    f"• {rate:.1f} files/s • ~{remaining:.0f}s remaining",
                    indent=2,
                )

        total_time = time.time() - start_time

        # Summary
        print_success(f"Processed {processed} files in {total_time:.1f}s", indent=1)
        if errors > 0:
            print_warning(f"{errors} files had parsing errors", indent=1)

            # ✅ NEW: Show error breakdown
            self._print_parse_error_breakdown()

        # Parser distribution
        print_dim("Parsers used:", indent=1)
        for parser_name, count in sorted(parser_counts.items(), key=lambda x: -x[1]):
            print_dim(f"  • {parser_name}: {count} files", indent=2)

        # Graph statistics
        self._print_graph_stats()

        return self.repo_graph

    def _print_parse_error_breakdown(self):
        """Show breakdown of parse failures with actionable advice."""
        # Get TreeSitterParser instance from factory
        ts_parser = None
        for parser in self.parser_factory.parsers:
            if isinstance(parser, TreeSitterParser):
                ts_parser = parser
                break

        if not ts_parser:
            return

        # Calculate statistics
        from micropad.repository.code_parsers import LANGUAGE_MAP

        total_files = len(self.scannable_files)
        ts_attempted = ts_parser.successful_parses + sum(ts_parser.parse_failures.values())

        # Show language support status
        if not LANGUAGE_MAP:
            print_warning("Tree-sitter languages NOT loaded!", indent=2)
            print_dim("All files fell back to heuristic parsing", indent=3)
            print_info("To enable full parsing:", indent=3)
            print_dim("pip install tree-sitter-languages", indent=4)
            return

        # Show what worked
        print_dim("Parse statistics:", indent=2)
        print_dim(
            f"  • Successful: {ts_parser.successful_parses}/{ts_attempted} ({ts_parser.successful_parses/ts_attempted*100 if ts_attempted > 0 else 0:.0f}%)",
            indent=3,
        )

        # Show supported extensions
        print_dim(f"  • Supported extensions: {', '.join(sorted(LANGUAGE_MAP.keys()))}", indent=3)

        # Show error breakdown if any
        if ts_parser.parse_failures:
            print_dim("Error breakdown:", indent=2)
            for error_type, count in sorted(ts_parser.parse_failures.items(), key=lambda x: -x[1]):
                print_dim(f"  • {error_type}: {count}", indent=3)

    def _process_file(self, file_path: Path):
        """Process single file using appropriate parser."""
        content = self._read(file_path)
        if not content:
            return False

        # ✅ NEW: Use factory to get parser and delegate
        parser = self.parser_factory.get_parser(file_path)
        return parser.parse(file_path, content, self.repo_graph)

    def _print_graph_stats(self):
        """Enhanced graph statistics with visualization."""
        node_types = defaultdict(int)
        edge_types = defaultdict(int)

        for _, d in self.repo_graph.nodes(data=True):
            node_types[d.get("type", "unknown")] += 1

        for _, _, d in self.repo_graph.edges(data=True):
            edge_types[d.get("type", "unknown")] += 1

        print(f"\n  {Colors.BOLD}Graph Statistics:{Colors.END}")
        print(f"  {Colors.CYAN}{'─' * 60}{Colors.END}")

        # Nodes
        print(f"  {Colors.BOLD}Nodes:{Colors.END} {self.repo_graph.number_of_nodes()} total")
        for node_type, count in sorted(node_types.items(), key=lambda x: -x[1]):
            bar_width = int(count / self.repo_graph.number_of_nodes() * 30)
            bar = "█" * bar_width
            print(f"    {node_type:20s} [{bar:30s}] {count:5d}")

        # Edges
        print(f"\n  {Colors.BOLD}Edges:{Colors.END} {self.repo_graph.number_of_edges()} total")
        if edge_types:
            for edge_type, count in sorted(edge_types.items(), key=lambda x: -x[1]):
                bar_width = int(count / self.repo_graph.number_of_edges() * 30)
                bar = "█" * bar_width
                print(f"    {edge_type:20s} [{bar:30s}] {count:5d}")
        else:
            print(f"    {Colors.YELLOW}⚠{Colors.END} No edges extracted")
            print(f"    {Colors.DIM}Possible causes:{Colors.END}")
            print(f"    {Colors.DIM}• Tree-sitter modules not installed{Colors.END}")
            print(f"    {Colors.DIM}• Unsupported file types only{Colors.END}")
            print(f"    {Colors.DIM}• Parsing errors (check logs){Colors.END}")

        # ✅ NEW: Parser success rates
        print(f"\n  {Colors.BOLD}Parser Statistics:{Colors.END}")
        for parser in self.parser_factory.parsers:
            if isinstance(parser, TreeSitterParser):
                total = parser.successful_parses + sum(parser.parse_failures.values())
                if total > 0:
                    success_rate = (parser.successful_parses / total) * 100
                    print(
                        f"    TreeSitter:  {parser.successful_parses}/{total} ({success_rate:.1f}% success)"
                    )

                    # Show top 3 error types
                    if parser.parse_failures:
                        sorted_errors = sorted(parser.parse_failures.items(), key=lambda x: -x[1])[
                            :3
                        ]
                        print(f"    {Colors.DIM}Top errors:{Colors.END}")
                        for error_type, count in sorted_errors:
                            print(f"      • {error_type}: {count}")
                break

        print(f"  {Colors.CYAN}{'─' * 60}{Colors.END}\n")

    def _base_name(self, expr: str) -> str:
        return expr.strip().split(".")[-1]

    def _record_import(self, file_path: Path, import_raw: str):
        """
        Updated: also create file->file edges for local same-repo paths heuristically.
        """
        imp = import_raw.strip("\"'")
        if not imp:
            return
        # Heuristic local path detection
        if imp.startswith(".") or "/" in imp:
            # Try to resolve relative segments
            candidate = (file_path.parent / imp).resolve()
            # Attempt with common extensions
            for ext in ["", ".py", ".js", ".ts", ".go", ".java"]:
                c2 = Path(str(candidate) + ext)
                if any(str(c2).endswith(str(sf)) for sf in self.scannable_files):
                    for sf in self.scannable_files:
                        if str(sf) == str(c2):
                            self.repo_graph.add_edge(str(file_path), str(sf), type="imports")
                            return
        # External dependency
        ext_id = f"external:{imp.split()[0]}"
        if not self.repo_graph.has_node(ext_id):
            self.repo_graph.add_node(ext_id, type="external_dependency", name=imp)
        self.repo_graph.add_edge(str(file_path), ext_id, type="imports")

    def _read(self, file_path: Path) -> Optional[str]:
        """Read file content safely with multiple encoding attempts."""
        encodings = ["utf-8", "latin-1", "cp1252", "iso-8859-1"]

        for encoding in encodings:
            try:
                return file_path.read_text(encoding=encoding)
            except UnicodeDecodeError:
                continue
            except Exception:
                return None

        # Last resort: read as binary and decode with error handling
        try:
            return file_path.read_bytes().decode("utf-8", errors="ignore")
        except Exception:
            return None
