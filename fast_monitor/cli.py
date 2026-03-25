"""Command-line entry for Task Scheduler and scripts."""

from __future__ import annotations

import argparse

from fast_monitor.core import MonitorConfig, run_monitor


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Poll fast.com, log speeds, optional Windows toast with average."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--headless",
        action="store_true",
        help="Run Chrome in headless mode.",
    )
    mode.add_argument(
        "--minimized",
        action="store_true",
        help="Minimize the browser after opening fast.com.",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=6,
        metavar="N",
        help="Number of speed test runs (default: 6).",
    )
    parser.add_argument(
        "--interval-minutes",
        type=int,
        default=10,
        metavar="M",
        help="Minutes between runs (default: 10).",
    )
    parser.add_argument(
        "--no-toast",
        action="store_true",
        help="Do not show Windows toast at the end.",
    )
    args = parser.parse_args()

    config = MonitorConfig(
        num_runs=max(1, args.runs),
        interval_sec=max(0, args.interval_minutes * 60),
        headless=args.headless,
        minimized=args.minimized,
        show_toast=not args.no_toast,
    )
    run_monitor(config)


if __name__ == "__main__":
    main()
