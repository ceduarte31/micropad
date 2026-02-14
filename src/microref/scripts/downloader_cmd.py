"""Entry point for microref-downloader command."""
from microref.downloader import main as downloader_main

def main():
    """Download filtered repositories."""
    downloader_main()

if __name__ == "__main__":
    main()
