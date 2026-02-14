"""Entry point for microref-generate-csv command."""
from microref.generate_csv import main as csv_main

def main():
    """Generate CSV from filtered repositories."""
    csv_main()

if __name__ == "__main__":
    main()
