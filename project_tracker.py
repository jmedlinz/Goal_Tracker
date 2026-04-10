"""Project Tracker PDF generator wrapper over shared tracker core."""

from tracker_core import run_tracker_cli


def main() -> None:
    """Run the Project Tracker CLI entry point."""
    run_tracker_cli(
        tracker_type="Project",
        description="Generate a printable Project Tracker PDF",
    )


if __name__ == "__main__":
    main()
