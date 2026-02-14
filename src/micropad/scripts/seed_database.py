"""
Vector Database Seeder for MicroPAD.

This module seeds the ChromaDB vector database with positive and negative
pattern examples extracted from YAML pattern definition files.

Usage:
    python seed_database.py
"""

import hashlib
import sys
from datetime import datetime
from pathlib import Path

import chromadb
import torch
import yaml
from sentence_transformers import SentenceTransformer

from micropad.config import settings as config

# Import UI utilities from centralized module
from micropad.logging.ui import (
    Colors,
    print_dim,
    print_error,
    print_info,
    print_success,
    print_warning,
)


def print_banner():
    """Print seeding banner."""
    width = 80
    print(f"\n{Colors.CYAN}{'='*width}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'Vector Database Seeder':^80}{Colors.END}")
    print(f"{Colors.CYAN}{'='*width}{Colors.END}\n")


def print_section(title: str):
    """Print section header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}▶ {title}{Colors.END}")
    print(f"{Colors.BLUE}{'─'*80}{Colors.END}")


class DatabaseSeeder:
    """Seeds the ChromaDB vector database with positive and negative examples."""

    def __init__(self):
        print_banner()
        print_section("Initialization")

        # Device detection
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        if self.device == "cuda":
            gpu_name = torch.cuda.get_device_name(0)
            vram = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            print_success(f"GPU detected: {gpu_name} ({vram:.1f}GB VRAM)")
        else:
            print_warning("No GPU detected - using CPU (slower)")

        # Load embedding model
        print_info(f"Loading embedding model: {Colors.BOLD}{config.EMBEDDING_MODEL}{Colors.END}")
        try:
            self.model = SentenceTransformer(config.EMBEDDING_MODEL, device=self.device)
            dim = self.model.get_sentence_embedding_dimension()
            print_success(f"Model loaded successfully (dimension: {dim})", indent=1)
        except Exception as e:
            print_error(f"Failed to load model: {e}", indent=1)
            sys.exit(1)

        # Initialize ChromaDB
        print_info(f"Connecting to vector database: {config.DB_PATH}")
        try:
            client = chromadb.PersistentClient(path=str(config.DB_PATH))

            # Check if collection exists
            existing_collections = [c.name for c in client.list_collections()]
            collection_exists = config.COLLECTION_NAME in existing_collections

            if collection_exists:
                print_warning(f"Collection '{config.COLLECTION_NAME}' already exists", indent=1)
                existing_collection = client.get_collection(name=config.COLLECTION_NAME)
                existing_count = existing_collection.count()
                print_info(f"Current count: {existing_count} embeddings", indent=2)

                # Ask user if they want to clear
                response = input(
                    f"\n  {Colors.YELLOW}Clear existing data and reseed? (y/n):{Colors.END} "
                ).lower()
                if response == "y":
                    print_info("Deleting existing collection...", indent=2)
                    client.delete_collection(name=config.COLLECTION_NAME)
                    print_success("Collection deleted", indent=2)
                    collection_exists = False
                else:
                    print_info("Will append new examples to existing collection", indent=2)

            self.collection = client.get_or_create_collection(
                name=config.COLLECTION_NAME,
                metadata={
                    "hnsw:space": "cosine",
                    "embedding_model": config.EMBEDDING_MODEL,
                    "dimension": dim,
                    "seeded_at": datetime.now().isoformat(),
                },
            )

            if not collection_exists:
                print_success(f"Collection '{config.COLLECTION_NAME}' created", indent=1)
            else:
                print_success(f"Using existing collection", indent=1)

        except Exception as e:
            print_error(f"Failed to initialize database: {e}", indent=1)
            sys.exit(1)

    def run(self):
        """Main seeding workflow."""
        print_section("Loading Pattern Examples")

        # Check patterns directory
        if not config.PATTERNS_DIR_PATH.is_dir():
            print_error(f"Patterns directory not found: {config.PATTERNS_DIR_PATH}")
            sys.exit(1)

        print_info(f"Scanning directory: {config.PATTERNS_DIR_PATH}")

        # Count YAML files
        yaml_files = list(config.PATTERNS_DIR_PATH.glob("*.yaml"))
        print_info(f"Found {len(yaml_files)} pattern definition files")

        if not yaml_files:
            print_error("No pattern YAML files found")
            sys.exit(1)

        # Load all examples
        docs, metadatas, ids, embeddings = self._load_all_examples()

        if not docs:
            print_error("No examples loaded from pattern files")
            sys.exit(1)

        print_section("Seeding Database")

        print_info(f"Total examples to seed: {Colors.BOLD}{len(docs)}{Colors.END}")
        print_dim(
            f"  Positive examples: {sum(1 for m in metadatas if m['type'] == 'positive')}", indent=1
        )
        print_dim(
            f"  Negative examples: {sum(1 for m in metadatas if m['type'] == 'negative')}", indent=1
        )

        # Estimate memory usage
        embedding_size_mb = (len(embeddings) * len(embeddings[0]) * 4) / (1024 * 1024)
        print_dim(f"  Estimated embedding size: {embedding_size_mb:.1f}MB", indent=1)

        # Perform upsert
        print_info("Writing embeddings to database...")
        try:
            self.collection.upsert(
                documents=docs, metadatas=metadatas, ids=ids, embeddings=embeddings
            )
            print_success("Embeddings written successfully")
        except Exception as e:
            print_error(f"Failed to write embeddings: {e}")
            sys.exit(1)

        # Verify
        final_count = self.collection.count()
        print_section("Verification")
        print_success(f"Final collection count: {Colors.BOLD}{final_count}{Colors.END}")

        # Test query
        print_info("Testing database query...")
        try:
            test_result = self.collection.query(query_embeddings=[embeddings[0]], n_results=1)
            if test_result and test_result["ids"]:
                print_success("Database query test passed", indent=1)
            else:
                print_warning("Database query returned empty result", indent=1)
        except Exception as e:
            print_error(f"Database query test failed: {e}", indent=1)

        print_section("Summary")
        print(f"\n  {Colors.GREEN}✓{Colors.END} Database seeding complete!")
        print(f"  {Colors.CYAN}•{Colors.END} Location: {config.DB_PATH}")
        print(f"  {Colors.CYAN}•{Colors.END} Collection: {config.COLLECTION_NAME}")
        print(f"  {Colors.CYAN}•{Colors.END} Total embeddings: {final_count}")
        print(f"  {Colors.CYAN}•{Colors.END} Embedding model: {config.EMBEDDING_MODEL}")
        print(f"  {Colors.CYAN}•{Colors.END} Device: {self.device.upper()}\n")

    def _process_pattern_file(
        self, yaml_file: Path, docs: list, metadatas: list, ids: list, embeddings: list
    ) -> tuple:
        """Process single pattern YAML file. Returns (pos_count, neg_count, error_msg)."""
        data = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
        pname = data.get("pattern_name")

        if not pname:
            return 0, 0, "Missing pattern_name"

        pos_examples = data.get("positive_examples", [])
        neg_examples = data.get("negative_examples", [])

        if not pos_examples and not neg_examples:
            return 0, 0, "No examples"

        total_positive = 0
        total_negative = 0

        if pos_examples:
            total_positive = self._add_examples_by_type(
                docs, metadatas, ids, embeddings, pname, data, "positive"
            )

        if neg_examples:
            total_negative = self._add_examples_by_type(
                docs, metadatas, ids, embeddings, pname, data, "negative"
            )

        return total_positive, total_negative, None

    def _print_loading_summary(
        self, yaml_files, failed_files, total_positive, total_negative, total_embeddings
    ):
        """Print summary of loading process."""
        print(f"\n{Colors.BOLD}Loading Summary:{Colors.END}")
        print_success(
            f"Successfully processed: {len(yaml_files) - len(failed_files)}/{len(yaml_files)} files"
        )
        print_info(f"Total positive examples: {total_positive}")
        print_info(f"Total negative examples: {total_negative}")
        print_info(f"Total embeddings generated: {total_embeddings}")

        if failed_files:
            print_warning(f"Failed files: {len(failed_files)}")
            for fname, reason in failed_files:
                print_dim(f"  • {fname}: {reason}", indent=1)

    def _load_all_examples(self):
        """Load all examples from pattern YAML files."""
        docs, metadatas, ids, embeddings = [], [], [], []

        yaml_files = sorted(config.PATTERNS_DIR_PATH.glob("*.yaml"))
        print_info("Processing pattern files:")

        total_positive = 0
        total_negative = 0
        failed_files = []

        for file_num, yaml_file in enumerate(yaml_files, start=1):
            print(f"\n  [{file_num}/{len(yaml_files)}] {Colors.BOLD}{yaml_file.name}{Colors.END}")

            try:
                pos_count, neg_count, error = self._process_pattern_file(
                    yaml_file, docs, metadatas, ids, embeddings
                )

                if error:
                    print_warning(error, indent=2)
                    failed_files.append((yaml_file.name, error))
                else:
                    total_positive += pos_count
                    total_negative += neg_count
                    print_success(f"Added {pos_count} positive, {neg_count} negative", indent=2)

            except Exception as e:
                error_msg = f"Processing error: {str(e)[:50]}"
                print_error(error_msg, indent=2)
                failed_files.append((yaml_file.name, error_msg))

        self._print_loading_summary(
            yaml_files, failed_files, total_positive, total_negative, len(embeddings)
        )

        return docs, metadatas, ids, embeddings

    def _add_examples_by_type(self, docs, metadatas, ids, embeddings, p_name, data, ex_type) -> int:
        """Adds a specific type of example (positive or negative) to the lists."""
        count = 0
        examples = data.get(f"{ex_type}_examples", [])

        for i, example in enumerate(examples):
            try:
                # Truncate very long examples for display
                example_preview = example[:80].replace("\n", " ")
                if len(example) > 80:
                    example_preview += "..."

                # Add document text
                docs.append(example)

                # Add metadata
                metadatas.append(
                    {
                        "pattern_name": p_name,
                        "type": ex_type,
                        "example_index": i,
                        "length": len(example),
                    }
                )

                # Create unique, deterministic ID
                unique_str = f"{p_name}-{ex_type}-{i}-{example[:50]}"
                doc_id = hashlib.sha256(unique_str.encode()).hexdigest()
                ids.append(doc_id)

                # Generate embedding
                embedding = self.model.encode(example, show_progress_bar=False).tolist()
                embeddings.append(embedding)

                count += 1

                # Progress indicator for large sets
                if len(examples) > 10 and (i + 1) % 5 == 0:
                    print_dim(f"    Progress: {i+1}/{len(examples)} examples encoded", indent=3)

            except Exception as e:
                print_warning(f"Failed to encode example {i}: {str(e)[:50]}", indent=3)
                continue

        return count


def main():
    """Main entry point."""
    try:
        seeder = DatabaseSeeder()
        seeder.run()
        sys.exit(0)
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}⚠{Colors.END} Seeding interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n{Colors.RED}✗ Fatal error:{Colors.END} {e}")
        import traceback

        print(f"\n{Colors.DIM}{traceback.format_exc()}{Colors.END}")
        sys.exit(1)


if __name__ == "__main__":
    main()
