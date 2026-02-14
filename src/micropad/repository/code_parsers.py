import logging
import re
from abc import ABC, abstractmethod
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import networkx as nx

try:
    from tree_sitter import Language, Parser, Query
    import tree_sitter_languages
except ImportError:
    Parser = None
    Query = None
    Language = None
    tree_sitter_languages = None

# ============================================================================
# LANGUAGE CONFIGURATION (from repository_graph.py)
# ============================================================================

LANGUAGE_MAP = {}  # Will be populated by _initialize_languages()
LANGUAGE_QUERIES = {}

FULL_CODE_LANGUAGES = {
    ".py": {
        "name": "python",
        "function_query": "(function_definition name: (identifier) @function)",
        "call_query": "(call function: (identifier) @call)",
        "import_query": "[(import_statement) (import_from_statement)]",
        "class_query": "(class_definition name: (identifier) @class)",
        "decorator_query": "(decorator) @decorator",
        "string_query": "(string) @string",
    },
    ".js": {
        "name": "javascript",
        "function_query": "(function_declaration name: (identifier) @function)",
        "call_query": "(call_expression function: (identifier) @call)",
        "import_query": "[(import_statement) (call_expression function: (identifier) @require)]",
        "class_query": "(class_declaration name: (identifier) @class)",
        "decorator_query": "(decorator) @decorator",
        "string_query": "[(string) (template_string)] @string",
    },
    ".ts": {
        "name": "typescript",
        "function_query": "(function_declaration name: (identifier) @function)",
        "call_query": "(call_expression function: (identifier) @call)",
        "import_query": "(import_statement)",
        "class_query": "(class_declaration name: (identifier) @class)",
        "decorator_query": "(decorator) @decorator",
        "string_query": "[(string) (template_string)] @string",
    },
    ".java": {
        "name": "java",
        "function_query": "(method_declaration name: (identifier) @method)",
        "call_query": "(method_invocation name: (identifier) @call)",
        "import_query": "(import_declaration)",
        "class_query": "(class_declaration name: (identifier) @class)",
        "decorator_query": "[(annotation) (marker_annotation)] @annotation",
        "string_query": "(string_literal) @string",
    },
    ".go": {
        "name": "go",
        "function_query": "(function_declaration name: (identifier) @function)",
        "call_query": "(call_expression function: (identifier) @call)",
        "import_query": "(import_declaration)",
        "class_query": "(type_declaration (type_spec name: (type_identifier) @class))",
        "decorator_query": "",  # Go doesn't have decorators
        "string_query": "[(interpreted_string_literal) (raw_string_literal)] @string",
    },
    ".cs": {
        "name": "c_sharp",
        "function_query": "(method_declaration (identifier) @method)",
        "call_query": "(invocation_expression (identifier) @call)",
        "import_query": "(using_directive)",
        "class_query": "(class_declaration (identifier) @class)",
        "decorator_query": "(attribute_list) @annotation",
        "string_query": "(string_literal) @string",
    },
    ".rb": {
        "name": "ruby",
        "function_query": "(method name: (identifier) @function)",
        "call_query": "(call method: (identifier) @call)",
        "import_query": "(call method: (identifier) @require)",
        "class_query": "(class name: (constant) @class)",
        "decorator_query": "",  # Ruby doesn't have traditional decorators
        "string_query": "(string) @string",
    },
    ".php": {
        "name": "php",
        "function_query": "(function_definition name: (name) @function)",
        "call_query": "(function_call_expression function: (name) @call)",
        "import_query": "[(namespace_use_declaration) (include_expression)]",
        "class_query": "(class_declaration name: (name) @class)",
        "decorator_query": "(attribute_group) @annotation",
        "string_query": "(string) @string",
    },
    ".sh": {
        "name": "bash",
        "function_query": "(function_definition name: (word) @function)",
        "call_query": "(command name: (command_name (word) @call))",
        "import_query": "(command name: (command_name) @source)",
        "class_query": "",  # Bash doesn't have classes
        "decorator_query": "",  # Bash doesn't have decorators
        "string_query": "(string) @string",
    },
    ".rs": {
        "name": "rust",
        "function_query": "(function_item name: (identifier) @function)",
        "call_query": "(call_expression function: (identifier) @call)",
        "import_query": "(use_declaration)",
        "class_query": "[(struct_item name: (type_identifier) @class) (impl_item type: (type_identifier) @class)]",
        "decorator_query": "(attribute_item) @annotation",
        "string_query": "(string_literal) @string",
    },
}

# code_parsers.py - REPLACE _load_language function


def _load_language(lang_name: str) -> Optional[Language]:
    """
    Load a tree-sitter language grammar from the tree-sitter-languages package.
    """
    if tree_sitter_languages is None:
        return None
    try:
        return tree_sitter_languages.get_language(lang_name)
    except Exception as e:
        logging.getLogger("events").debug(
            f"Failed to load language '{lang_name}' via tree-sitter-languages: {e}"
        )
        return None


# code_parsers.py - REPLACE _initialize_languages function


def _initialize_languages():
    """
    Initialize language map and queries with installation guidance.
    """
    global LANGUAGE_MAP, LANGUAGE_QUERIES

    success_count = 0
    failed_languages = []

    for ext, cfg in FULL_CODE_LANGUAGES.items():
        lang_name = cfg["name"]
        language = _load_language(lang_name)

        if language:
            LANGUAGE_MAP[ext] = lang_name
            LANGUAGE_QUERIES[lang_name] = {
                "functions": cfg["function_query"],
                "calls": cfg["call_query"],
                "imports": cfg["import_query"],
                "classes": cfg.get("class_query", ""),
                "decorators": cfg.get("decorator_query", ""),
                "strings": cfg.get("string_query", ""),
            }
            success_count += 1
        else:
            failed_languages.append((ext, lang_name))

    # Log results
    logger = logging.getLogger("events")

    if success_count > 0:
        logger.info(
            f"Tree-sitter initialized: {success_count}/{len(FULL_CODE_LANGUAGES)} languages loaded"
        )
        logger.debug(f"Loaded languages: {list(LANGUAGE_MAP.values())}")
    else:
        logger.warning(
            "Tree-sitter failed to load ANY languages! "
            "All files will use heuristic parsing (much less accurate)."
        )

    if failed_languages:
        logger.warning(
            f"Failed to load {len(failed_languages)} languages: "
            f"{', '.join(f'{ext} ({lang})' for ext, lang in failed_languages)}"
        )

        # Provide installation instructions
        logger.info(
            "To enable full code parsing, install tree-sitter languages:\n"
            "  pip install tree-sitter-languages  # Recommended (all-in-one)\n"
            "OR install individual packages:\n"
            + "\n".join(
                f"  pip install tree-sitter-{lang.replace('_', '-')}"
                for _, lang in failed_languages[:3]
            )
        )


# Initialize on import
_initialize_languages()


# ============================================================================
# BASE PARSER CLASS
# ============================================================================


class CodeParser(ABC):
    """Base class for all code parsing strategies."""

    @abstractmethod
    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file."""
        pass

    @abstractmethod
    def parse(self, file_path: Path, content: str, graph: nx.DiGraph) -> bool:
        """
        Parse file and add nodes/edges to graph.

        Returns:
            True if parsing succeeded, False otherwise
        """
        pass


# ============================================================================
# TREE-SITTER PARSER (Full Code Analysis)
# ============================================================================


class TreeSitterParser(CodeParser):
    """Full code parsing using tree-sitter (functions, calls, imports)."""

    # code_parsers.py - TreeSitterParser.__init__

    def __init__(self, language_map: dict, language_queries: dict):
        # FIXED: Initialize events_log FIRST
        self.events_log = logging.getLogger("events")

        self.language_map = language_map
        self.language_queries = language_queries
        self.parser = Parser() if Parser else None
        self.function_index = {}
        self.functions_by_file = {}

        # Track parse failures by type
        self.parse_failures = defaultdict(int)
        self.successful_parses = 0
        self.files_attempted = 0

        # Log initialization status
        if self.parser and self.language_map:
            self.events_log.info(
                f"TreeSitterParser initialized: {len(self.language_map)} languages available"
            )
        elif not self.parser:
            self.events_log.warning("TreeSitterParser disabled: tree-sitter not installed")
        else:
            self.events_log.warning(
                "TreeSitterParser initialized but NO languages loaded! "
                "Install tree-sitter-languages: pip install tree-sitter-languages"
            )

    def can_parse(self, file_path: Path) -> bool:
        """Check if file extension is supported by tree-sitter."""
        if not self.parser:
            return False
        ext = file_path.suffix.lower()
        return ext in self.language_map

    def parse(self, file_path: Path, content: str, graph: nx.DiGraph) -> bool:
        """Extract functions, calls, and imports using tree-sitter."""
        self.files_attempted += 1  # ✅ ADD: Track all attempts

        ext = file_path.suffix.lower()
        lang_name = self.language_map.get(ext)

        if not lang_name or lang_name not in self.language_queries:
            self.parse_failures["unsupported_language"] += 1
            return False

        language = _load_language(lang_name)
        if not language:
            self.parse_failures["language_load_failed"] += 1
            return False

        try:
            # Set language
            # Handle different tree-sitter versions
            if hasattr(self.parser, "language"):
                self.parser.language = language
            elif hasattr(self.parser, "set_language"):
                self.parser.set_language(language)
            else:
                # This should not happen with supported versions
                raise AttributeError("Parser object has no 'language' or 'set_language' attribute.")

            # Parse source code with encoding handling
            try:
                tree = self.parser.parse(content.encode("utf-8"))
            except UnicodeEncodeError:
                # Try with error handling
                tree = self.parser.parse(content.encode("utf-8", errors="replace"))

            # Check: Tree parsing failed
            if not tree or not tree.root_node:
                self.parse_failures["tree_parse_failed"] += 1
                return False

            if tree.root_node.has_error:
                self.events_log.debug(
                    f"Syntax errors in {file_path}, continuing with partial parse"
                )

            queries = self.language_queries[lang_name]

            # Extract classes
            classes = self._extract_classes(
                file_path, tree, language, queries.get("classes", ""), graph
            )

            # Extract functions
            functions = self._extract_functions(
                file_path, tree, language, queries["functions"], graph
            )

            # Cache for call resolution
            self.functions_by_file[str(file_path)] = functions

            # Extract decorators/annotations
            self._extract_decorators(
                file_path, tree, language, queries.get("decorators", ""), graph, functions, classes
            )

            # Extract imports
            self._extract_imports(file_path, tree, language, queries["imports"], graph)

            # Extract calls
            self._extract_calls(file_path, tree, language, queries["calls"], graph, functions)

            # Extract string literals (for URLs, endpoints, etc.)
            self._extract_strings(
                file_path, tree, language, queries.get("strings", ""), graph, functions
            )

            # Index functions for cross-file resolution
            for func_name, _ in functions:
                self.function_index.setdefault(func_name, []).append(f"{file_path}:{func_name}")

            self.successful_parses += 1  # ✅ ADD: Track success
            return True

        except UnicodeDecodeError as e:
            self.parse_failures["encoding_error"] += 1
            self.events_log.debug(f"Encoding error for {file_path}: {e}")
            return False
        except Exception as e:
            # Better error categorization
            error_type = type(e).__name__
            self.parse_failures[f"exception_{error_type}"] += 1
            self.events_log.debug(f"Tree-sitter parsing failed for {file_path}: {error_type}: {e}")
            return False

    def _extract_functions(
        self, file_path: Path, tree, language, query_str: str, graph: nx.DiGraph
    ) -> List[Tuple[str, any]]:
        """Extract function definitions and add to graph."""
        functions = []

        try:
            captures = self._query_captures(tree, language, query_str)

            for node, capture_name in captures:
                # Accept any capture (simplified queries don't use dotted names)
                try:
                    func_name = (
                        node.text.decode("utf-8")
                        if isinstance(node.text, bytes)
                        else str(node.text)
                    )
                except Exception:
                    func_name = str(node.text)

                # Clean up function name (remove special characters)
                func_name = func_name.strip().replace("\n", "").replace("\r", "")

                if func_name and len(func_name) < 200:  # Sanity check
                    # Create function node
                    func_id = f"{file_path}:{func_name}"
                    if not graph.has_node(func_id):
                        graph.add_node(
                            func_id, type="function", name=func_name, file=str(file_path)
                        )
                        graph.add_edge(str(file_path), func_id, type="defines")

                    functions.append((func_name, node))

        except Exception as e:
            self.events_log.debug(f"Function extraction failed for {file_path}: {e}")
            self.parse_failures["function_extraction_failed"] += 1

        return functions

    def _extract_imports(self, file_path: Path, tree, language, query_str: str, graph: nx.DiGraph):
        """Extract import statements and add dependencies to graph."""
        try:
            captures = self._query_captures(tree, language, query_str)

            for node, capture_name in captures:
                if "import" in capture_name:
                    import_target = node.text.decode("utf-8").strip("\"'")

                    # Check if it's a local file import
                    if import_target.startswith(".") or import_target.startswith("/"):
                        potential_file = self._resolve_import_path(file_path, import_target)
                        if potential_file and graph.has_node(str(potential_file)):
                            graph.add_edge(str(file_path), str(potential_file), type="imports")
                    else:
                        # External dependency
                        dep_id = f"external:{import_target}"
                        if not graph.has_node(dep_id):
                            graph.add_node(dep_id, type="external_dependency", name=import_target)
                        graph.add_edge(str(file_path), dep_id, type="imports")

        except Exception as e:
            self.events_log.debug(f"Import extraction failed for {file_path}: {e}")

    def _extract_calls(
        self,
        file_path: Path,
        tree,
        language,
        query_str: str,
        graph: nx.DiGraph,
        functions: List[Tuple[str, any]],
    ):
        """Extract function calls and create call edges."""
        try:
            captures = self._query_captures(tree, language, query_str)

            for node, capture_name in captures:
                if "call" in capture_name:
                    call_name = node.text.decode("utf-8")
                    base_name = self._extract_base_function_name(call_name)

                    # Find enclosing function (caller)
                    caller_func_id = self._find_enclosing_function(file_path, node, functions)

                    # Find target function
                    target_id = self._resolve_call_target(file_path, call_name, base_name, graph)

                    if target_id:
                        if caller_func_id:
                            # Function -> Function edge
                            graph.add_edge(caller_func_id, target_id, type="calls")

                            # Project to file level if cross-file
                            target_file = graph.nodes[target_id].get("file")
                            if target_file and str(file_path) != target_file:
                                graph.add_edge(str(file_path), target_file, type="calls_file")
                        else:
                            # File-level call (no enclosing function)
                            graph.add_edge(str(file_path), target_id, type="calls_from_file")

        except Exception as e:
            self.events_log.debug(f"Call extraction failed for {file_path}: {e}")

    def _extract_classes(
        self, file_path: Path, tree, language, query_str: str, graph: nx.DiGraph
    ) -> List[Tuple[str, any]]:
        """Extract class/type definitions and add to graph."""
        classes = []

        if not query_str:  # Skip if language doesn't have classes
            return classes

        try:
            captures = self._query_captures(tree, language, query_str)

            for node, capture_name in captures:
                try:
                    class_name = (
                        node.text.decode("utf-8")
                        if isinstance(node.text, bytes)
                        else str(node.text)
                    )
                except Exception:
                    class_name = str(node.text)

                class_name = class_name.strip().replace("\n", "").replace("\r", "")

                if class_name and len(class_name) < 200:
                    # Create class node
                    class_id = f"{file_path}:{class_name}"
                    if not graph.has_node(class_id):
                        graph.add_node(
                            class_id, type="class", name=class_name, file=str(file_path)
                        )
                        graph.add_edge(str(file_path), class_id, type="defines")

                    classes.append((class_name, node))

        except Exception as e:
            self.events_log.debug(f"Class extraction failed for {file_path}: {e}")

        return classes

    def _extract_decorators(
        self,
        file_path: Path,
        tree,
        language,
        query_str: str,
        graph: nx.DiGraph,
        functions: List[Tuple[str, any]],
        classes: List[Tuple[str, any]]
    ):
        """Extract decorators/annotations and link to functions/classes."""
        if not query_str:  # Skip if language doesn't have decorators
            return

        try:
            captures = self._query_captures(tree, language, query_str)

            for node, capture_name in captures:
                try:
                    decorator_text = (
                        node.text.decode("utf-8")
                        if isinstance(node.text, bytes)
                        else str(node.text)
                    )
                except Exception:
                    continue

                # Clean and extract decorator name
                decorator_text = decorator_text.strip()

                # Find what this decorator is attached to (function or class)
                target_id = self._find_decorator_target(file_path, node, functions, classes)

                if target_id:
                    # Add decorator as node attribute (for pattern matching)
                    if graph.has_node(target_id):
                        decorators = graph.nodes[target_id].get("decorators", [])
                        decorators.append(decorator_text)
                        graph.nodes[target_id]["decorators"] = decorators

        except Exception as e:
            self.events_log.debug(f"Decorator extraction failed for {file_path}: {e}")

    def _extract_strings(
        self,
        file_path: Path,
        tree,
        language,
        query_str: str,
        graph: nx.DiGraph,
        functions: List[Tuple[str, any]]
    ):
        """Extract string literals (URLs, endpoints, queue names, etc.)."""
        if not query_str:
            return

        try:
            captures = self._query_captures(tree, language, query_str)

            # Patterns for microservice-relevant strings
            import re
            url_pattern = re.compile(r'https?://[^\s\'"]+|[a-zA-Z0-9_-]+://[^\s\'"]+')
            endpoint_pattern = re.compile(r'^/[a-zA-Z0-9/_\-{}.]+$')
            queue_pattern = re.compile(r'[a-z0-9_-]+\.(queue|topic|exchange|channel)')

            for node, capture_name in captures:
                try:
                    string_text = (
                        node.text.decode("utf-8")
                        if isinstance(node.text, bytes)
                        else str(node.text)
                    )
                except Exception:
                    continue

                # Remove quotes
                string_value = string_text.strip().strip('"\'`')

                # Skip empty or very long strings
                if not string_value or len(string_value) > 500:
                    continue

                # Check if it's a microservice-relevant string
                string_type = None
                if url_pattern.match(string_value):
                    string_type = "url"
                elif endpoint_pattern.match(string_value):
                    string_type = "endpoint"
                elif queue_pattern.search(string_value):
                    string_type = "queue"

                if string_type:
                    # Find enclosing function
                    func_id = self._find_enclosing_function(file_path, node, functions)

                    # Create string literal node
                    string_id = f"string:{string_type}:{string_value}"
                    if not graph.has_node(string_id):
                        graph.add_node(
                            string_id,
                            type="string_literal",
                            string_type=string_type,
                            value=string_value
                        )

                    # Link to function or file
                    if func_id:
                        graph.add_edge(func_id, string_id, type="uses_string")
                    else:
                        graph.add_edge(str(file_path), string_id, type="uses_string")

        except Exception as e:
            self.events_log.debug(f"String extraction failed for {file_path}: {e}")

    def _find_decorator_target(
        self,
        file_path: Path,
        decorator_node,
        functions: List[Tuple[str, any]],
        classes: List[Tuple[str, any]]
    ) -> Optional[str]:
        """Find the function or class that a decorator is attached to."""
        # Decorators are typically right before the function/class they decorate
        # Find the closest function/class after this decorator node

        decorator_end = decorator_node.end_byte

        # Check functions
        for func_name, func_node in functions:
            if func_node.start_byte >= decorator_end and func_node.start_byte - decorator_end < 100:
                return f"{file_path}:{func_name}"

        # Check classes
        for class_name, class_node in classes:
            if class_node.start_byte >= decorator_end and class_node.start_byte - decorator_end < 100:
                return f"{file_path}:{class_name}"

        return None

    def _query_captures(self, tree, language, query_str: str) -> List[Tuple[any, str]]:
        """Execute tree-sitter query and return captures."""
        if not query_str:
            return []
        try:
            query = language.query(query_str)
            return query.captures(tree.root_node)
        except Exception as e:
            self.events_log.debug(f"Query execution error: {e} | Query: {query_str[:100]}")
            return []

    def _extract_base_function_name(self, call_expression: str) -> str:
        """Extract base function name from call expression (e.g., 'obj.method' -> 'method')."""
        return call_expression.strip().split(".")[-1]

    def _find_enclosing_function(
        self, file_path: Path, call_node, functions: List[Tuple[str, any]]
    ) -> Optional[str]:
        """Find the function that contains this call node."""
        for func_name, func_node in functions:
            if (
                func_node.start_byte <= call_node.start_byte
                and call_node.end_byte <= func_node.end_byte
            ):
                return f"{file_path}:{func_name}"
        return None

    def _resolve_call_target(
        self, file_path: Path, call_name: str, base_name: str, graph: nx.DiGraph
    ) -> Optional[str]:
        """Resolve call to a function ID."""
        # Try exact match in same file
        local_exact = f"{file_path}:{call_name}"
        if graph.has_node(local_exact):
            return local_exact

        # Try base name in same file
        local_base = f"{file_path}:{base_name}"
        if graph.has_node(local_base):
            return local_base

        # Try cross-file lookup
        for candidate in self.function_index.get(base_name, []):
            if not candidate.startswith(str(file_path)):
                return candidate

        return None

    def _resolve_import_path(self, from_file: Path, import_path: str) -> Optional[Path]:
        """Attempt to resolve a relative import to an actual file."""
        try:
            import_path = import_path.lstrip("./")
            base_path = from_file.parent / import_path

            # Try common extensions
            for ext in ["", ".py", ".js", ".ts", ".java", ".go"]:
                candidate = Path(str(base_path) + ext)
                if candidate.exists():
                    return candidate
        except Exception:
            pass

        return None


# ============================================================================
# Dockerfile PARSER
# ============================================================================


class DockerfileParser(CodeParser):
    """Parse Dockerfiles for service definitions."""

    def __init__(self):
        self.events_log = logging.getLogger("events")

    def can_parse(self, file_path: Path) -> bool:
        return file_path.name.lower() == "dockerfile" or file_path.name.lower().startswith(
            "dockerfile."
        )

    def parse(self, file_path: Path, content: str, graph: nx.DiGraph) -> bool:
        """Extract service information from Dockerfile."""
        try:
            # Extract exposed ports (service endpoints)
            expose_pattern = r"EXPOSE\s+(\d+)"
            for match in re.finditer(expose_pattern, content, re.IGNORECASE):
                port = match.group(1)
                service_id = f"service:{file_path.parent.name}:{port}"

                if not graph.has_node(service_id):
                    graph.add_node(
                        service_id,
                        type="service",
                        name=f"{file_path.parent.name}:{port}",
                        source="dockerfile",
                    )
                graph.add_edge(str(file_path), service_id, type="defines_service")

            # Extract healthcheck endpoints
            healthcheck_pattern = r"HEALTHCHECK.*?CMD\s+.*?(http://[^\s]+)"
            for match in re.finditer(healthcheck_pattern, content, re.IGNORECASE):
                endpoint = match.group(1)
                self.events_log.debug(f"Found healthcheck endpoint: {endpoint}")

            # Extract base images (dependencies)
            from_pattern = r"FROM\s+([^\s]+)"
            for match in re.finditer(from_pattern, content, re.IGNORECASE):
                base_image = match.group(1)
                dep_id = f"docker_image:{base_image}"

                if not graph.has_node(dep_id):
                    graph.add_node(dep_id, type="docker_image", name=base_image)
                graph.add_edge(str(file_path), dep_id, type="uses_base_image")

            return True

        except Exception as e:
            self.events_log.debug(f"Dockerfile parsing failed for {file_path}: {e}")
            return False


# ============================================================================
# YAML PARSER
# ============================================================================


class YAMLParser(CodeParser):
    """Parse YAML structure (Kubernetes, Docker Compose, etc.)."""

    def __init__(self):
        self.events_log = logging.getLogger("events")

    def can_parse(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in [".yaml", ".yml"]

    def parse(self, file_path: Path, content: str, graph: nx.DiGraph) -> bool:
        """Enhanced YAML parsing with Kubernetes-specific logic."""
        try:
            import yaml

            data = yaml.safe_load(content)

            if not data or not isinstance(data, dict):
                return self._parse_heuristic(file_path, content, graph)

            # ✅ NEW: Kubernetes resource detection
            if "apiVersion" in data and "kind" in data:
                return self._parse_kubernetes_resource(file_path, data, graph)

            # Existing Kubernetes Service logic
            if data.get("kind") == "Service" and "metadata" in data:
                service_name = data["metadata"].get("name", "unknown")
                service_id = f"k8s_service:{service_name}"
                graph.add_node(service_id, type="k8s_service", name=service_name)
                graph.add_edge(str(file_path), service_id, type="defines_service")

            # Docker Compose services
            if "services" in data:
                for service_name, service_def in data["services"].items():
                    service_id = f"service:{service_name}"
                    graph.add_node(
                        service_id, type="service", name=service_name, source="docker-compose"
                    )
                    graph.add_edge(str(file_path), service_id, type="defines_service")

                    # Extract dependencies
                    if "depends_on" in service_def:
                        deps = service_def["depends_on"]
                        if isinstance(deps, list):
                            for dep in deps:
                                dep_id = f"service:{dep}"
                                if not graph.has_node(dep_id):
                                    graph.add_node(dep_id, type="service", name=dep)
                                graph.add_edge(service_id, dep_id, type="depends_on")

            return True

        except Exception as e:
            self.events_log.debug(f"YAML parsing failed for {file_path}: {e}")
            return self._parse_heuristic(file_path, content, graph)

    def _parse_kubernetes_resource(self, file_path: Path, data: dict, graph: nx.DiGraph) -> bool:
        """Parse Kubernetes-specific resources."""
        kind = data.get("kind")
        api_version = data.get("apiVersion", "")
        metadata = data.get("metadata", {})
        name = metadata.get("name", "unknown")

        # Map Kubernetes kinds to graph node types
        kind_mappings = {
            "Deployment": "k8s_deployment",
            "StatefulSet": "k8s_statefulset",
            "DaemonSet": "k8s_daemonset",
            "Service": "k8s_service",
            "Ingress": "k8s_ingress",
            "ConfigMap": "k8s_configmap",
            "Secret": "k8s_secret",
            "Pod": "k8s_pod",
            "Job": "k8s_job",
            "CronJob": "k8s_cronjob",
        }

        node_type = kind_mappings.get(kind, "k8s_resource")
        resource_id = f"{node_type}:{name}"

        # Create resource node
        graph.add_node(resource_id, type=node_type, name=name, kind=kind, api_version=api_version)
        graph.add_edge(str(file_path), resource_id, type="defines_resource")

        # Extract workload -> service relationships
        if kind in ["Deployment", "StatefulSet", "DaemonSet"]:
            spec = data.get("spec", {})

            # Extract replicas (for scaling patterns)
            replicas = spec.get("replicas", 1)
            graph.nodes[resource_id]["replicas"] = replicas

            # Extract selector labels (for service linkage)
            selector = spec.get("selector", {}).get("matchLabels", {})
            if selector:
                # Look for matching Service resources
                for node, node_data in graph.nodes(data=True):
                    if node_data.get("type") == "k8s_service":
                        # Could match by labels if we stored them
                        # For now, just note the selector
                        graph.nodes[resource_id]["selector"] = selector

        # Extract service endpoints
        if kind == "Service":
            spec = data.get("spec", {})
            ports = spec.get("ports", [])

            for port in ports:
                port_num = port.get("port")
                target_port = port.get("targetPort", port_num)

                if port_num:
                    endpoint_id = f"k8s_endpoint:{name}:{port_num}"
                    graph.add_node(
                        endpoint_id, type="k8s_endpoint", port=port_num, target_port=target_port
                    )
                    graph.add_edge(resource_id, endpoint_id, type="exposes_port")

        # Extract ingress routes
        if kind == "Ingress":
            spec = data.get("spec", {})
            rules = spec.get("rules", [])

            for rule in rules:
                host = rule.get("host", "*")
                http = rule.get("http", {})
                paths = http.get("paths", [])

                for path in paths:
                    backend = path.get("backend", {})
                    service_name = backend.get("service", {}).get("name") or backend.get(
                        "serviceName"
                    )

                    if service_name:
                        # Create edge to service
                        service_id = f"k8s_service:{service_name}"
                        if not graph.has_node(service_id):
                            graph.add_node(service_id, type="k8s_service", name=service_name)
                        graph.add_edge(resource_id, service_id, type="routes_to")

        return True

    def _parse_heuristic(self, file_path: Path, content: str, graph: nx.DiGraph) -> bool:
        """Fallback heuristic parsing."""
        # Will be handled by HeuristicParser
        return False


# ============================================================================
# JSON PARSER
# ============================================================================


class JSONParser(CodeParser):
    """Parse JSON files (package.json, etc.)."""

    def __init__(self):
        self.events_log = logging.getLogger("events")

    def can_parse(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == ".json"

    def parse(self, file_path: Path, content: str, graph: nx.DiGraph) -> bool:
        """Extract dependencies from JSON."""
        try:
            import json

            data = json.loads(content)

            if not data or not isinstance(data, dict):
                return False

            # package.json dependencies
            for dep_type in ["dependencies", "devDependencies", "peerDependencies"]:
                if dep_type in data:
                    for pkg_name, version in data[dep_type].items():
                        dep_id = f"npm:{pkg_name}"
                        if not graph.has_node(dep_id):
                            graph.add_node(dep_id, type="npm_package", name=pkg_name)
                        graph.add_edge(str(file_path), dep_id, type="requires", version=version)

            return True

        except Exception as e:
            self.events_log.debug(f"JSON parsing failed for {file_path}: {e}")
            return False


# ============================================================================
# HCL PARSER (Terraform)
# ============================================================================


class HCLParser(CodeParser):
    """Parse HCL/Terraform files."""

    def __init__(self):
        self.events_log = logging.getLogger("events")

    def can_parse(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in [".hcl", ".tf"]

    def parse(self, file_path: Path, content: str, graph: nx.DiGraph) -> bool:
        """Extract Terraform resources and modules."""
        try:
            # Resource blocks: resource "type" "name"
            resource_pattern = r'resource\s+"([^"]+)"\s+"([^"]+)"'
            for match in re.finditer(resource_pattern, content):
                resource_type, resource_name = match.groups()
                resource_id = f"terraform:{resource_type}.{resource_name}"
                graph.add_node(
                    resource_id,
                    type="terraform_resource",
                    resource_type=resource_type,
                    name=resource_name,
                )
                graph.add_edge(str(file_path), resource_id, type="defines_resource")

            # Module references
            module_pattern = r'module\s+"([^"]+)"'
            for match in re.finditer(module_pattern, content):
                module_name = match.group(1)
                module_id = f"terraform:module.{module_name}"
                if not graph.has_node(module_id):
                    graph.add_node(module_id, type="terraform_module", name=module_name)
                graph.add_edge(str(file_path), module_id, type="uses_module")

            return True

        except Exception as e:
            self.events_log.debug(f"HCL parsing failed for {file_path}: {e}")
            return False


# ============================================================================
# XML PARSER (Maven POM, etc.)
# ============================================================================


class XMLParser(CodeParser):
    """Parse XML files (Maven POM, etc.)."""

    def __init__(self):
        self.events_log = logging.getLogger("events")

    def can_parse(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == ".xml" or file_path.name.lower() == "pom.xml"

    def parse(self, file_path: Path, content: str, graph: nx.DiGraph) -> bool:
        """Extract Maven dependencies."""
        try:
            import xml.etree.ElementTree as ET

            root = ET.fromstring(content)

            # Maven POM dependencies
            if root.tag.endswith("project") or "project" in root.tag:
                ns = {"maven": root.tag.split("}")[0].strip("{")} if "}" in root.tag else {}

                deps_elem = (
                    root.find(".//maven:dependencies", ns) if ns else root.find(".//dependencies")
                )

                if deps_elem is not None:
                    dep_elements = (
                        deps_elem.findall(".//maven:dependency", ns)
                        if ns
                        else deps_elem.findall(".//dependency")
                    )

                    for dep in dep_elements:
                        group_id_elem = (
                            dep.find(".//maven:groupId", ns) if ns else dep.find(".//groupId")
                        )
                        artifact_id_elem = (
                            dep.find(".//maven:artifactId", ns) if ns else dep.find(".//artifactId")
                        )

                        if group_id_elem is not None and artifact_id_elem is not None:
                            dep_name = f"{group_id_elem.text}:{artifact_id_elem.text}"
                            dep_id = f"maven:{dep_name}"

                            if not graph.has_node(dep_id):
                                graph.add_node(dep_id, type="maven_artifact", name=dep_name)
                            graph.add_edge(str(file_path), dep_id, type="requires")

            return True

        except Exception as e:
            self.events_log.debug(f"XML parsing failed for {file_path}: {e}")
            return False


# ============================================================================
# HEURISTIC PARSER (Fallback)
# ============================================================================


class HeuristicParser(CodeParser):
    """Regex-based fallback parser for unsupported languages."""

    def __init__(self):
        self.events_log = logging.getLogger("events")

    def can_parse(self, file_path: Path) -> bool:
        return True  # Always available as fallback

    def parse(self, file_path: Path, content: str, graph: nx.DiGraph) -> bool:
        """Find file mentions and extract pseudo-functions using regex."""
        if not content:
            return False

        # Extract pseudo-functions using common patterns
        patterns = [
            r"^\s*def\s+([A-Za-z_]\w*)\s*\(",  # Python
            r"^\s*function\s+([A-Za-z_]\w*)\s*\(",  # JavaScript
            r"^\s*([A-Za-z_]\w*)\s*=\s*\([^)]*\)\s*=>",  # Arrow functions
            r"^\s*class\s+([A-Za-z_]\w*)\s*[:\{]",  # Classes
            r"^\s*func\s+([A-Za-z_]\w*)\s*\(",  # Go
        ]

        combined = re.compile("|".join(patterns))
        added = 0

        for line in content.splitlines()[:2000]:  # Limit for performance
            match = combined.match(line)
            if match:
                for group in match.groups():
                    if group:
                        func_id = f"{file_path}:{group}"
                        if not graph.has_node(func_id):
                            graph.add_node(
                                func_id, type="function", name=group, file=str(file_path)
                            )
                            graph.add_edge(str(file_path), func_id, type="defines")
                            added += 1
                        break

        if added > 0:
            self.events_log.debug(
                f"Heuristic parser extracted {added} pseudo-functions from {file_path}"
            )

        return added > 0


# ============================================================================
# PARSER FACTORY
# ============================================================================


class ParserFactory:
    def __init__(self, language_map: dict = None, language_queries: dict = None):
        self.language_map = language_map if language_map is not None else LANGUAGE_MAP
        self.language_queries = (
            language_queries if language_queries is not None else LANGUAGE_QUERIES
        )

        # NOW initialize parsers (they can access self.language_map)
        self.parsers = [
            TreeSitterParser(self.language_map, self.language_queries),
            YAMLParser(),
            JSONParser(),
            DockerfileParser(),
            HCLParser(),
            XMLParser(),
            HeuristicParser(),
        ]

    def get_parser(self, file_path: Path) -> CodeParser:
        """Return first parser that can handle the file."""
        for parser in self.parsers:
            if parser.can_parse(file_path):
                return parser

        # Should never reach here (HeuristicParser always accepts)
        return self.parsers[-1]
