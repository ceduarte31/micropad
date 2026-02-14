"""Entry point for microref-collector command."""
from microref.collector import main as collector_main

def main():
    """Collect repository data from GitHub Archive."""
    collector_main()

if __name__ == "__main__":
    main()
