"""Tests for the interactive main.py launcher."""

from unittest.mock import Mock

import pytest

import main as tracker_main


def test_main_dispatches_to_goal_tracker(monkeypatch):
    """Selecting option 1 should run the Goal Tracker entry point."""
    goal_main = Mock()
    project_main = Mock()

    monkeypatch.setattr(tracker_main.goal_tracker, "main", goal_main)
    monkeypatch.setattr(tracker_main.project_tracker, "main", project_main)
    monkeypatch.setattr("builtins.input", lambda _: "1")

    tracker_main.main()

    goal_main.assert_called_once()
    project_main.assert_not_called()


def test_main_dispatches_to_project_tracker(monkeypatch):
    """Selecting option 2 should run the Project Tracker entry point."""
    goal_main = Mock()
    project_main = Mock()

    monkeypatch.setattr(tracker_main.goal_tracker, "main", goal_main)
    monkeypatch.setattr(tracker_main.project_tracker, "main", project_main)
    monkeypatch.setattr("builtins.input", lambda _: "2")

    tracker_main.main()

    project_main.assert_called_once()
    goal_main.assert_not_called()


def test_main_rejects_invalid_selection(monkeypatch):
    """Invalid selections should exit with status 1."""
    monkeypatch.setattr("builtins.input", lambda _: "x")

    with pytest.raises(SystemExit) as exc_info:
        tracker_main.main()

    assert exc_info.value.code == 1
