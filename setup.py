"""
MicroPAD setup configuration.
"""
from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme = Path(__file__).parent / "README.md"
long_description = readme.read_text(encoding="utf-8") if readme.exists() else ""

setup(
    name="micropad",
    version="2.0.0",
    description="AI-powered microservices architecture pattern detection",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="MicroPAD Team",
    author_email="ceduarte at fe dot up dot pt",
    url="https://github.com/ceduarte31/micropad",
    license="MIT",

    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.9",

    install_requires=[
        "chromadb>=0.4.0",
        "sentence-transformers>=2.2.0",
        "torch>=2.0.0",
        "networkx>=3.0",
        "numpy>=1.24.0",
        "pyyaml>=6.0",
        "python-dotenv>=1.0.0",
        "tqdm>=4.65.0",
        "tree-sitter>=0.20.0",
        "tree-sitter-python>=0.20.0",
        "tree-sitter-javascript>=0.20.0",
        "tree-sitter-java>=0.20.0",
        "tree-sitter-go>=0.20.0",
        "tree-sitter-rust>=0.20.0",
        "tree-sitter-cpp>=0.20.0",
        "openai>=1.0.0",
        "ollama>=0.1.0",
    ],

    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "pylint>=2.17.0",
            "mypy>=1.0.0",
            "isort>=5.12.0",
        ],
        "docs": [
            "sphinx>=6.0.0",
            "sphinx-rtd-theme>=1.2.0",
            "myst-parser>=1.0.0",
        ],
    },

    entry_points={
        "console_scripts": [
            "micropad=micropad.core.scanner:main",
            "micropad-seed=scripts.seed_database:main",
        ],
    },

    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],

    keywords="microservices architecture patterns ai llm detection analysis",
    project_urls={
        "Bug Reports": "https://github.com/ceduarte31/micropad/issues",
        "Source": "https://github.com/ceduarte31/micropad",
        "Documentation": "https://github.com/ceduarte31/micropad/docs",
    },
)
