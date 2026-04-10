"""Goal Tracker PDF generator wrapper over shared tracker core."""

from tracker_core import run_tracker_cli


def main() -> None:
    """Run the Goal Tracker CLI entry point."""
    run_tracker_cli(
        tracker_type="Goal",
        description="Generate a printable annual Goal Tracker PDF",
    )


if __name__ == "__main__":
    main()
