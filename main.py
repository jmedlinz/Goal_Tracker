"""Interactive launcher for Goal and Project tracker generation."""

import sys

import goal_tracker
import project_tracker


def main() -> None:
    """Prompt for tracker type and run the selected tracker generator."""
    print("Choose a tracker to generate:")
    print("1. Goal Tracker")
    print("2. Project Tracker")

    choice = input("Enter 1 or 2: ").strip()

    if choice == "1":
        goal_tracker.main()
    elif choice == "2":
        project_tracker.main()
    else:
        print("Invalid selection. Please run again and enter 1 or 2.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
