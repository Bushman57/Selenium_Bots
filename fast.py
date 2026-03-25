"""Shim: use `python fast.py` from the Flirt_Bot folder (same as `python -m fast_monitor.cli`)."""

from fast_monitor.cli import main

if __name__ == "__main__":
    main()
