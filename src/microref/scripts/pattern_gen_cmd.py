"""Entry point for microref-pattern-gen command."""
from microref.pattern_generator import main as pattern_main

def main():
    """Generate patterns from repositories."""
    pattern_main()

if __name__ == "__main__":
    main()
