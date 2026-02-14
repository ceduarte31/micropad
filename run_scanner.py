#!/usr/bin/env python3
"""
MicroPAD Scanner - Entry Point

This is a convenience wrapper that runs the scanner from the new package structure.
It's equivalent to: python -m micropad.core.scanner

Usage:
    python run_scanner.py
    python run_scanner.py --eval ground_truth.json
"""
import sys
from micropad.core.scanner import main

if __name__ == '__main__':
    sys.exit(main())
