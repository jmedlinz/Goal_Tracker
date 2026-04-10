"""
Unit and integration tests for Goal Tracker PDF Generator
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

import tracker_core
from goal_tracker import main as goal_tracker_main
from project_tracker import main as project_tracker_main
from tracker_core import (
    DrawingHelper,
    FontConfig,
    GoalTrackerConfig,
    GoalTrackerPDF,
    LayoutManager,
    PageConfig,
)


class TestGoalTrackerConfig:
    """Tests for GoalTrackerConfig class."""

    def test_config_loads_successfully(self, tmp_path):
        """Test that configuration loads from YAML file."""
        config_file = tmp_path / "config.yaml"
        config_content = """
page:
  size: letter
  orientation: portrait
  margins:
    top: 0.5
    bottom: 0.5
    left: 0.5
    right: 0.5

fonts:
  family: Helvetica
  title_size: 18
  goal_line_size: 10
  quarter_label_size: 10
  month_label_size: 9
  week_number_size: 8

colors:
  grid_line: [0, 0, 0]
  light_grid: [180, 180, 180]
  text: [0, 0, 0]

layout:
  quarterly_column_width: 1.25
  monthly_column_width: 1.25
  weekly_column_width: 4.5
  checkbox_size: 0.15
  row_height: 0.185

output:
  directory: output
  filename: goal_tracker_template.pdf
"""
        config_file.write_text(config_content)

        config = GoalTrackerConfig(str(config_file))
        assert config is not None
        assert config.config["page"]["size"] == "letter"

    def test_config_file_not_found(self):
        """Test that FileNotFoundError is raised for missing config file."""
        with pytest.raises(FileNotFoundError):
            GoalTrackerConfig("nonexistent_config.yaml")

    def test_get_page_config(self, tmp_path):
        """Test getting page configuration."""
        config_file = tmp_path / "config.yaml"
        config_content = """
page:
  size: letter
  orientation: portrait
  margins:
    top: 0.5
    bottom: 0.5
    left: 0.5
    right: 0.5

fonts:
  family: Helvetica
  title_size: 18
  goal_line_size: 10
  quarter_label_size: 10
  month_label_size: 9
  week_number_size: 8

colors:
  grid_line: [0, 0, 0]
  light_grid: [180, 180, 180]
  text: [0, 0, 0]

layout:
  quarterly_column_width: 1.25
  monthly_column_width: 1.25
  weekly_column_width: 4.5
  checkbox_size: 0.15
  row_height: 0.185

output:
  directory: output
  filename: goal_tracker_template.pdf
"""
        config_file.write_text(config_content)

        config = GoalTrackerConfig(str(config_file))
        page_config = config.get_page_config()

        assert isinstance(page_config, PageConfig)
        assert page_config.width > 0
        assert page_config.height > 0

    def test_get_font_config(self, tmp_path):
        """Test getting font configuration."""
        config_file = tmp_path / "config.yaml"
        config_content = """
page:
  size: letter
  orientation: portrait
  margins:
    top: 0.5
    bottom: 0.5
    left: 0.5
    right: 0.5

fonts:
  family: Helvetica
  title_size: 18
  goal_line_size: 10
  quarter_label_size: 10
  month_label_size: 9
  week_number_size: 8

colors:
  grid_line: [0, 0, 0]
  light_grid: [180, 180, 180]
  text: [0, 0, 0]

layout:
  quarterly_column_width: 1.25
  monthly_column_width: 1.25
  weekly_column_width: 4.5
  checkbox_size: 0.15
  row_height: 0.185

output:
  directory: output
  filename: goal_tracker_template.pdf
"""
        config_file.write_text(config_content)

        config = GoalTrackerConfig(str(config_file))
        font_config = config.get_font_config()

        assert isinstance(font_config, FontConfig)
        assert font_config.family == "Helvetica"
        assert font_config.title_size == 18


class TestLayoutManager:
    """Tests for LayoutManager class."""

    @pytest.fixture
    def layout_manager(self):
        """Fixture for LayoutManager instance."""
        page_config = PageConfig(
            width=612,  # 8.5 inches in points
            height=792,  # 11 inches in points
            top_margin=36,  # 0.5 inches
            bottom_margin=36,
            left_margin=36,
            right_margin=36,
        )
        layout_config = {
            "quarterly_column_width": 1.25,
            "monthly_column_width": 1.25,
            "weekly_column_width": 4.5,
            "checkbox_size": 0.15,
            "row_height": 0.185,
        }
        return LayoutManager(page_config, layout_config)

    def test_layout_initialization(self, layout_manager):
        """Test that LayoutManager initializes correctly."""
        assert layout_manager is not None
        assert layout_manager.WEEKS_IN_YEAR == 52
        assert layout_manager.WEEKS_PER_QUARTER == 13

    def test_get_column_x_positions(self, layout_manager):
        """Test getting column x-coordinates."""
        positions = layout_manager.get_column_x_positions()

        assert "quarterly" in positions
        assert "monthly" in positions
        assert "weekly" in positions
        assert "checkbox" in positions

        # Verify ordering (left to right)
        assert positions["quarterly"] < positions["monthly"]
        assert positions["monthly"] < positions["weekly"]
        assert positions["weekly"] < positions["checkbox"]

    def test_get_column_widths(self, layout_manager):
        """Test getting column widths."""
        widths = layout_manager.get_column_widths()

        assert all(width > 0 for width in widths.values())
        assert "quarterly" in widths
        assert "monthly" in widths
        assert "weekly" in widths
        assert "checkbox" in widths

    def test_get_quarter_for_week(self):
        """Test quarter calculation for week numbers."""
        assert LayoutManager.get_quarter_for_week(1) == 1
        assert LayoutManager.get_quarter_for_week(13) == 1
        assert LayoutManager.get_quarter_for_week(14) == 2
        assert LayoutManager.get_quarter_for_week(26) == 2
        assert LayoutManager.get_quarter_for_week(27) == 3
        assert LayoutManager.get_quarter_for_week(39) == 3
        assert LayoutManager.get_quarter_for_week(40) == 4
        assert LayoutManager.get_quarter_for_week(52) == 4

    def test_is_catch_up_week(self):
        """Test catch-up week detection."""
        assert LayoutManager.is_catch_up_week(13) is True
        assert LayoutManager.is_catch_up_week(26) is True
        assert LayoutManager.is_catch_up_week(39) is True
        assert LayoutManager.is_catch_up_week(52) is True
        assert LayoutManager.is_catch_up_week(1) is False
        assert LayoutManager.is_catch_up_week(25) is False
        assert LayoutManager.is_catch_up_week(51) is False

    def test_get_month_abbreviation(self):
        """Test month abbreviation retrieval."""
        assert LayoutManager.get_month_abbreviation(1) == "Jan"
        assert LayoutManager.get_month_abbreviation(6) == "Jun"
        assert LayoutManager.get_month_abbreviation(12) == "Dec"
        assert LayoutManager.get_month_abbreviation(0) == ""
        assert LayoutManager.get_month_abbreviation(13) == ""

    def test_get_row_height(self, layout_manager):
        """Test row height calculation."""
        row_height = layout_manager.get_row_height()
        assert row_height > 0

    def test_get_header_height(self, layout_manager):
        """Test header height calculation."""
        header_height = layout_manager.get_header_height()
        assert header_height > 0

    def test_get_week_y_position(self, layout_manager):
        """Test y-position calculation for weeks."""
        y_week_1 = layout_manager.get_week_y_position(1)
        y_week_2 = layout_manager.get_week_y_position(2)
        y_week_52 = layout_manager.get_week_y_position(52)

        # Week 2 should be lower than week 1
        assert y_week_2 < y_week_1

        # Week 52 should be even lower
        assert y_week_52 < y_week_2


class TestDrawingHelper:
    """Tests for DrawingHelper class."""

    @patch("tracker_core.canvas.Canvas")
    def test_draw_line(self, mock_canvas):
        """Test drawing a line."""
        c = Mock()
        DrawingHelper.draw_line(c, 0, 0, 100, 100)

        c.setLineWidth.assert_called()
        c.setStrokeColorRGB.assert_called()
        c.line.assert_called_with(0, 0, 100, 100)

    @patch("tracker_core.canvas.Canvas")
    def test_draw_rectangle(self, mock_canvas):
        """Test drawing a rectangle."""
        c = Mock()
        DrawingHelper.draw_rectangle(c, 0, 0, 50, 50)

        c.setLineWidth.assert_called()
        c.setStrokeColorRGB.assert_called()
        c.rect.assert_called()

    @patch("tracker_core.canvas.Canvas")
    def test_draw_text(self, mock_canvas):
        """Test drawing text."""
        c = Mock()
        DrawingHelper.draw_text(c, "Test", 0, 0)

        c.setFont.assert_called()
        c.setFillColorRGB.assert_called()
        c.drawString.assert_called_with(0, 0, "Test")

    @patch("tracker_core.canvas.Canvas")
    def test_draw_diamond(self, mock_canvas):
        """Test drawing a diamond."""
        c = Mock()
        DrawingHelper.draw_diamond(c, center_x=10, center_y=20, width=8, height=6)

        assert c.line.call_count == 4


class TestGoalTrackerPDF:
    """Tests for GoalTrackerPDF class."""

    @pytest.fixture
    def goal_tracker_pdf(self, tmp_path):
        """Fixture for GoalTrackerPDF instance."""
        config_file = tmp_path / "config.yaml"
        config_content = """
page:
  size: letter
  orientation: portrait
  margins:
    top: 0.5
    bottom: 0.5
    left: 0.5
    right: 0.5

fonts:
  family: Helvetica
  title_size: 18
  goal_line_size: 10
  quarter_label_size: 10
  month_label_size: 9
  week_number_size: 8

colors:
  grid_line: [0, 0, 0]
  light_grid: [180, 180, 180]
  text: [0, 0, 0]

layout:
  quarterly_column_width: 1.25
  monthly_column_width: 1.25
  weekly_column_width: 4.5
  checkbox_size: 0.15
  row_height: 0.185

output:
  directory: output
  filename: goal_tracker_template.pdf
"""
        config_file.write_text(config_content)
        config = GoalTrackerConfig(str(config_file))
        return GoalTrackerPDF(config)

    def test_pdf_initialization(self, goal_tracker_pdf):
        """Test that GoalTrackerPDF initializes correctly."""
        assert goal_tracker_pdf is not None
        assert goal_tracker_pdf.page_config is not None
        assert goal_tracker_pdf.font_config is not None
        assert goal_tracker_pdf.colors is not None

    def test_pdf_generation(self, goal_tracker_pdf, tmp_path):
        """Test PDF generation creates a file."""
        output_path = tmp_path / "test_output.pdf"
        goal_tracker_pdf.generate(str(output_path))

        assert output_path.exists()
        assert output_path.stat().st_size > 0

    @pytest.mark.parametrize(
        "tracker_type,expected_title,expected_label",
        [
            ("Goal", "Goal Tracker for 2026", "Goal:"),
            ("Project", "Project Tracker for 2026", "Project:"),
        ],
    )
    def test_draw_header_uses_tracker_type(self, tmp_path, tracker_type, expected_title, expected_label):
        """Test header text uses the configured tracker type for title and label."""
        config_file = tmp_path / "config.yaml"
        config_content = """
page:
  size: letter
  orientation: portrait
  margins:
    top: 0.5
    bottom: 0.5
    left: 0.5
    right: 0.5

fonts:
  family: Helvetica
  title_size: 18
  goal_line_size: 10
  quarter_label_size: 10
  month_label_size: 9
  week_number_size: 8

colors:
  grid_line: [0, 0, 0]
  light_grid: [180, 180, 180]
  text: [0, 0, 0]

layout:
  quarterly_column_width: 1.25
  monthly_column_width: 1.25
  weekly_column_width: 4.5
  checkbox_size: 0.15
  row_height: 0.185

output:
  directory: output
  filename: goal_tracker_template.pdf
"""
        config_file.write_text(config_content)
        config = GoalTrackerConfig(str(config_file))
        pdf = GoalTrackerPDF(config, year=2026, tracker_type=tracker_type)

        c = Mock()
        pdf.draw_header(c)

        drawn_text = [call.args[2] for call in c.drawString.call_args_list]
        assert expected_title in drawn_text
        assert expected_label in drawn_text


def test_iso_week_shift_starts_at_week2_for_53_week_year(tmp_path):
    """Week labels should start at ISO week 2 in 53-week years (e.g., 2020 -> 6-10 for first row)."""
    config_file = tmp_path / "config.yaml"
    config_content = """
page:
  size: letter
  orientation: portrait
  margins:
    top: 0.5
    bottom: 0.5
    left: 0.5
    right: 0.5

fonts:
  family: Helvetica
  title_size: 18
  goal_line_size: 10
  quarter_label_size: 10
  month_label_size: 9
  week_number_size: 8

colors:
  grid_line: [0, 0, 0]
  light_grid: [180, 180, 180]
  text: [0, 0, 0]

layout:
  quarterly_column_width: 1.25
  monthly_column_width: 1.25
  weekly_column_width: 4.5
  checkbox_size: 0.15
  row_height: 0.185

output:
  directory: output
  filename: goal_tracker_template.pdf
"""
    config_file.write_text(config_content)

    config = GoalTrackerConfig(str(config_file))
    pdf = GoalTrackerPDF(config, year=2020)  # 2020 has ISO week 53

    c = Mock()
    c.stringWidth.return_value = 10  # deterministic width for positioning

    pdf.draw_weekly_column(c)

    first_label = c.drawString.call_args_list[0][0][2]
    assert first_label == "6-10"


def test_console_note_for_iso53_year(monkeypatch, tmp_path, capsys):
    """Console note should appear when the selected year has 53 ISO weeks."""
    config_file = tmp_path / "config.yaml"
    config_content = """
page:
  size: letter
  orientation: portrait
  margins:
    top: 0.5
    bottom: 0.5
    left: 0.5
    right: 0.5

fonts:
  family: Helvetica
  title_size: 18
  goal_line_size: 10
  quarter_label_size: 10
  month_label_size: 9
  week_number_size: 8

colors:
  grid_line: [0, 0, 0]
  light_grid: [180, 180, 180]
  text: [0, 0, 0]

layout:
  quarterly_column_width: 1.25
  monthly_column_width: 1.25
  weekly_column_width: 4.5
  checkbox_size: 0.15
  row_height: 0.185

output:
  directory: output
  filename: goal_tracker_template.pdf
"""
    config_file.write_text(config_content)

    # Avoid generating an actual PDF during this test
    monkeypatch.setattr(tracker_core.GoalTrackerPDF, "generate", lambda self, output_path: None)

    output_path = tmp_path / "out.pdf"
    monkeypatch.setattr(
        "sys.argv",
        [
            "goal_tracker.py",
            "--config",
            str(config_file),
            "--output",
            str(output_path),
            "2020",  # Year with ISO week 53
        ],
        raising=False,
    )

    goal_tracker_main()

    out, _ = capsys.readouterr()
    assert "Note: For better alignment, starting at ISO week 2." in out


def test_project_tracker_cli_uses_project_type(monkeypatch, tmp_path):
    """Project tracker entry point should instantiate generator with Project tracker type."""
    config_file = tmp_path / "config.yaml"
    config_content = """
page:
  size: letter
  orientation: portrait
  margins:
    top: 0.5
    bottom: 0.5
    left: 0.5
    right: 0.5

fonts:
  family: Helvetica
  title_size: 18
  goal_line_size: 10
  quarter_label_size: 10
  month_label_size: 9
  week_number_size: 8

colors:
  grid_line: [0, 0, 0]
  light_grid: [180, 180, 180]
  text: [0, 0, 0]

layout:
  quarterly_column_width: 1.25
  monthly_column_width: 1.25
  weekly_column_width: 4.5
  checkbox_size: 0.15
  row_height: 0.185

output:
  directory: output
  filename: goal_tracker_template.pdf
"""
    config_file.write_text(config_content)

    seen_tracker_types = []

    def _capture_generate(self, output_path):
        seen_tracker_types.append(self.tracker_type)

    monkeypatch.setattr(tracker_core.GoalTrackerPDF, "generate", _capture_generate)

    output_path = tmp_path / "project_out.pdf"
    monkeypatch.setattr(
        "sys.argv",
        [
            "project_tracker.py",
            "--config",
            str(config_file),
            "--output",
            str(output_path),
            "2026",
        ],
        raising=False,
    )

    project_tracker_main()

    assert seen_tracker_types == ["Project"]


def test_project_tracker_default_output_filename(monkeypatch, tmp_path):
    """Project tracker should default to project_tracker_template.pdf when output is not provided."""
    config_file = tmp_path / "config.yaml"
    output_dir = tmp_path / "out"
    config_content = f"""
page:
  size: letter
  orientation: portrait
  margins:
    top: 0.5
    bottom: 0.5
    left: 0.5
    right: 0.5

fonts:
  family: Helvetica
  title_size: 18
  goal_line_size: 10
  quarter_label_size: 10
  month_label_size: 9
  week_number_size: 8

colors:
  grid_line: [0, 0, 0]
  light_grid: [180, 180, 180]
  text: [0, 0, 0]

layout:
  quarterly_column_width: 1.25
  monthly_column_width: 1.25
  weekly_column_width: 4.5
  checkbox_size: 0.15
  row_height: 0.185

output:
  directory: {output_dir.as_posix()}
  filename: goal_tracker_template.pdf
"""
    config_file.write_text(config_content)

    seen_output_paths = []

    def _capture_generate(self, output_path):
        seen_output_paths.append(output_path)

    monkeypatch.setattr(tracker_core.GoalTrackerPDF, "generate", _capture_generate)

    monkeypatch.setattr(
        "sys.argv",
        [
            "project_tracker.py",
            "--config",
            str(config_file),
            "2026",
        ],
        raising=False,
    )

    project_tracker_main()

    assert len(seen_output_paths) == 1
    assert Path(seen_output_paths[0]).name == "project_tracker_template.pdf"


def test_catch_up_messages_use_new_wording(tmp_path):
    """Catch-up messaging should use the new wording for Q1-Q4."""
    config_file = tmp_path / "config.yaml"
    config_content = """
page:
  size: letter
  orientation: portrait
  margins:
    top: 0.5
    bottom: 0.5
    left: 0.5
    right: 0.5

fonts:
  family: Helvetica
  title_size: 18
  goal_line_size: 10
  quarter_label_size: 10
  month_label_size: 9
  week_number_size: 8

colors:
  grid_line: [0, 0, 0]
  light_grid: [180, 180, 180]
  text: [0, 0, 0]

layout:
  quarterly_column_width: 1.25
  monthly_column_width: 1.25
  weekly_column_width: 4.5
  checkbox_size: 0.15
  row_height: 0.185

output:
  directory: output
  filename: goal_tracker_template.pdf
"""
    config_file.write_text(config_content)

    config = GoalTrackerConfig(str(config_file))
    pdf = GoalTrackerPDF(config, year=2026)

    c = Mock()
    c.stringWidth.return_value = 10

    pdf.draw_weekly_column(c)

    drawn_text = [call.args[2] for call in c.drawString.call_args_list]
    assert "Close out Q1. Plan next quarter." in drawn_text
    assert "Close out Q2. Plan next quarter." in drawn_text
    assert "Close out Q3. Plan next quarter." in drawn_text
    assert "Close out Q4." in drawn_text


def test_project_checkbox_column_uses_diamonds(tmp_path, monkeypatch):
    """Project style should draw diamonds instead of square checkboxes."""
    config_file = tmp_path / "config.yaml"
    config_content = """
page:
  size: letter
  orientation: portrait
  margins:
    top: 0.5
    bottom: 0.5
    left: 0.5
    right: 0.5

fonts:
  family: Helvetica
  title_size: 18
  goal_line_size: 10
  quarter_label_size: 10
  month_label_size: 9
  week_number_size: 8

colors:
  grid_line: [0, 0, 0]
  light_grid: [180, 180, 180]
  text: [0, 0, 0]

layout:
  quarterly_column_width: 1.25
  monthly_column_width: 1.25
  weekly_column_width: 4.5
  checkbox_size: 0.15
  row_height: 0.185

output:
  directory: output
  filename: goal_tracker_template.pdf
"""
    config_file.write_text(config_content)

    config = GoalTrackerConfig(str(config_file))
    pdf = GoalTrackerPDF(config, year=2026, tracker_type="Project")

    calls = {"diamond": 0, "rectangle": 0}

    def _capture_diamond(c, center_x, center_y, width, height, stroke_width=1, color=(0, 0, 0)):
        calls["diamond"] += 1
        assert height <= pdf.layout.get_row_height()

    def _capture_rectangle(c, x, y, width, height, stroke_width=1, color=(0, 0, 0)):
        calls["rectangle"] += 1

    monkeypatch.setattr(DrawingHelper, "draw_diamond", _capture_diamond)
    monkeypatch.setattr(DrawingHelper, "draw_rectangle", _capture_rectangle)

    pdf.draw_checkbox_column(Mock())

    assert calls["diamond"] == 52
    assert calls["rectangle"] == 0


def test_project_grid_keeps_quarter_tops_and_drops_three_month_box_borders(tmp_path, monkeypatch):
    """Project style should keep quarter top lines but remove 3-month outer month-box borders."""
    config_file = tmp_path / "config.yaml"
    config_content = """
page:
  size: letter
  orientation: portrait
  margins:
    top: 0.5
    bottom: 0.5
    left: 0.5
    right: 0.5

fonts:
  family: Helvetica
  title_size: 18
  goal_line_size: 10
  quarter_label_size: 10
  month_label_size: 9
  week_number_size: 8

colors:
  grid_line: [0, 0, 0]
  light_grid: [180, 180, 180]
  text: [0, 0, 0]

layout:
  quarterly_column_width: 1.25
  monthly_column_width: 1.25
  weekly_column_width: 4.5
  checkbox_size: 0.15
  row_height: 0.185

output:
  directory: output
  filename: goal_tracker_template.pdf
"""
    config_file.write_text(config_content)

    config = GoalTrackerConfig(str(config_file))
    goal_pdf = GoalTrackerPDF(config, year=2026, tracker_type="Goal")
    project_pdf = GoalTrackerPDF(config, year=2026, tracker_type="Project")
    quarter_x = goal_pdf.layout.get_column_x_positions()["quarterly"]
    monthly_x = goal_pdf.layout.get_column_x_positions()["monthly"]
    x_right = (
        project_pdf.layout.get_column_x_positions()["checkbox"]
        + project_pdf.layout.get_column_widths()["checkbox"]
    )

    goal_x_values = []
    project_x_values = []
    project_lines = []

    def _capture_goal_rect(c, x, y, width, height, stroke_width=1, color=(0, 0, 0)):
        goal_x_values.append(x)

    def _capture_project_rect(c, x, y, width, height, stroke_width=1, color=(0, 0, 0)):
        project_x_values.append(x)

    def _capture_project_line(c, x1, y1, x2, y2, stroke_width=0.5, color=(0, 0, 0), dash=None):
        project_lines.append((x1, y1, x2, y2, stroke_width))

    monkeypatch.setattr(DrawingHelper, "draw_rectangle", _capture_goal_rect)
    goal_pdf.draw_grid(Mock())

    monkeypatch.setattr(DrawingHelper, "draw_rectangle", _capture_project_rect)
    monkeypatch.setattr(DrawingHelper, "draw_line", _capture_project_line)
    project_pdf.draw_grid(Mock())

    assert any(abs(x - quarter_x) < 0.0001 for x in goal_x_values)
    assert not any(abs(x - quarter_x) < 0.0001 for x in project_x_values)

    # Project style keeps quarter top borders (4 lines across full quarter region width).
    quarter_top_lines = [
        line
        for line in project_lines
        if abs(line[0] - quarter_x) < 0.0001 and abs(line[2] - x_right) < 0.0001 and abs(line[4] - 1.0) < 0.0001
    ]
    assert len(quarter_top_lines) == 4

    # Project style draws only internal month separators (months 1,2,4,5,7,8,10,11), not quarter-end borders.
    month_separator_lines = [
        line
        for line in project_lines
        if abs(line[0] - monthly_x) < 0.0001 and abs(line[2] - x_right) < 0.0001 and abs(line[4] - 0.75) < 0.0001
    ]
    assert len(month_separator_lines) == 8


class TestIntegration:
    """Integration tests."""

    def test_full_pdf_generation_workflow(self, tmp_path):
        """Test complete workflow from config to PDF generation."""
        # Create a temporary config file
        config_file = tmp_path / "config.yaml"
        config_content = """
page:
  size: letter
  orientation: portrait
  margins:
    top: 0.5
    bottom: 0.5
    left: 0.5
    right: 0.5

fonts:
  family: Helvetica
  title_size: 18
  goal_line_size: 10
  quarter_label_size: 10
  month_label_size: 9
  week_number_size: 8

colors:
  grid_line: [0, 0, 0]
  light_grid: [180, 180, 180]
  text: [0, 0, 0]

layout:
  quarterly_column_width: 1.25
  monthly_column_width: 1.25
  weekly_column_width: 4.5
  checkbox_size: 0.15
  row_height: 0.185

output:
  directory: output
  filename: goal_tracker_template.pdf
"""
        config_file.write_text(config_content)

        # Load configuration
        config = GoalTrackerConfig(str(config_file))

        # Generate PDF
        output_path = tmp_path / "output" / "test.pdf"
        pdf_generator = GoalTrackerPDF(config)
        pdf_generator.generate(str(output_path))

        # Verify PDF was created
        assert output_path.exists()
        assert output_path.stat().st_size > 0


class TestCoverageGaps:
    """Targeted tests for previously uncovered high-value branches."""

    def test_validate_config_missing_required_key_raises_value_error(self, tmp_path):
        """Missing required config keys should raise ValueError."""
        config_file = tmp_path / "config.yaml"
        config_content = """
page:
  size: letter
  orientation: portrait
  margins:
    top: 0.5
    bottom: 0.5
    left: 0.5
    right: 0.5

fonts:
  family: Helvetica
  title_size: 18
  goal_line_size: 10
  quarter_label_size: 10
  month_label_size: 9
  week_number_size: 8

layout:
  quarterly_column_width: 1.25
  monthly_column_width: 1.25
  weekly_column_width: 4.5
  checkbox_size: 0.15
  row_height: 0.185

output:
  directory: output
  filename: goal_tracker_template.pdf
"""
        config_file.write_text(config_content)

        with pytest.raises(ValueError, match="Missing required config key: colors"):
            GoalTrackerConfig(str(config_file))

    @pytest.mark.parametrize(
        "week_number,expected_month",
        [
            (13, -1),
            (1, 1),
            (6, 2),
            (17, 4),
            (45, 11),
            (60, -1),
        ],
    )
    def test_get_month_for_week_mapping(self, week_number, expected_month):
        """Week-to-month mapping should include catch-up and out-of-range behavior."""
        assert LayoutManager.get_month_for_week(week_number) == expected_month

    def test_draw_line_with_dash_pattern(self):
        """Dashed line drawing should set and reset dash pattern."""
        c = Mock()
        DrawingHelper.draw_line(c, 0, 0, 100, 100, dash=[2, 2])

        c.setDash.assert_any_call([2, 2])
        c.setDash.assert_any_call([])

    def test_draw_text_right_alignment_uses_draw_right_string(self):
        """Right alignment should render with drawRightString."""
        c = Mock()
        DrawingHelper.draw_text(c, "Right", 10, 20, align="right")

        c.drawRightString.assert_called_once_with(10, 20, "Right")
        c.drawString.assert_not_called()

    def test_goal_tracker_pdf_rejects_non_string_tracker_type(self, tmp_path):
        """Non-string tracker_type should raise TypeError."""
        config_file = tmp_path / "config.yaml"
        config_content = """
page:
  size: letter
  orientation: portrait
  margins:
    top: 0.5
    bottom: 0.5
    left: 0.5
    right: 0.5

fonts:
  family: Helvetica
  title_size: 18
  goal_line_size: 10
  quarter_label_size: 10
  month_label_size: 9
  week_number_size: 8

colors:
  grid_line: [0, 0, 0]
  light_grid: [180, 180, 180]
  text: [0, 0, 0]

layout:
  quarterly_column_width: 1.25
  monthly_column_width: 1.25
  weekly_column_width: 4.5
  checkbox_size: 0.15
  row_height: 0.185

output:
  directory: output
  filename: goal_tracker_template.pdf
"""
        config_file.write_text(config_content)
        config = GoalTrackerConfig(str(config_file))

        with pytest.raises(TypeError, match="tracker_type must be a string"):
            GoalTrackerPDF(config, tracker_type=123)

    def test_goal_tracker_pdf_rejects_blank_tracker_type(self, tmp_path):
        """Blank tracker_type should raise ValueError."""
        config_file = tmp_path / "config.yaml"
        config_content = """
page:
  size: letter
  orientation: portrait
  margins:
    top: 0.5
    bottom: 0.5
    left: 0.5
    right: 0.5

fonts:
  family: Helvetica
  title_size: 18
  goal_line_size: 10
  quarter_label_size: 10
  month_label_size: 9
  week_number_size: 8

colors:
  grid_line: [0, 0, 0]
  light_grid: [180, 180, 180]
  text: [0, 0, 0]

layout:
  quarterly_column_width: 1.25
  monthly_column_width: 1.25
  weekly_column_width: 4.5
  checkbox_size: 0.15
  row_height: 0.185

output:
  directory: output
  filename: goal_tracker_template.pdf
"""
        config_file.write_text(config_content)
        config = GoalTrackerConfig(str(config_file))

        with pytest.raises(ValueError, match="tracker_type must be a non-empty string"):
            GoalTrackerPDF(config, tracker_type="   ")

    def test_draw_grid_row_stripes_branch(self, tmp_path, monkeypatch):
        """Row stripe branch should run when show_row_stripes is enabled."""
        config_file = tmp_path / "config.yaml"
        config_content = """
page:
  size: letter
  orientation: portrait
  margins:
    top: 0.5
    bottom: 0.5
    left: 0.5
    right: 0.5

fonts:
  family: Helvetica
  title_size: 18
  goal_line_size: 10
  quarter_label_size: 10
  month_label_size: 9
  week_number_size: 8

colors:
  grid_line: [0, 0, 0]
  light_grid: [180, 180, 180]
  text: [0, 0, 0]
  row_stripe: [230, 230, 230]

layout:
  quarterly_column_width: 1.25
  monthly_column_width: 1.25
  weekly_column_width: 4.5
  checkbox_size: 0.15
  row_height: 0.185
  show_row_stripes: true

output:
  directory: output
  filename: goal_tracker_template.pdf
"""
        config_file.write_text(config_content)
        config = GoalTrackerConfig(str(config_file))
        pdf = GoalTrackerPDF(config, year=2026)

        monkeypatch.setattr(DrawingHelper, "draw_line", lambda *args, **kwargs: None)
        monkeypatch.setattr(DrawingHelper, "draw_rectangle", lambda *args, **kwargs: None)

        c = Mock()
        pdf.draw_grid(c)

        assert c.rect.call_count > 0

    def test_run_tracker_cli_handles_yaml_error(self, monkeypatch, capsys):
        """CLI should exit with status 1 and message on YAML parse errors."""

        def _raise_yaml(config_path):
            raise tracker_core.yaml.YAMLError("bad yaml")

        monkeypatch.setattr(tracker_core, "GoalTrackerConfig", _raise_yaml)
        monkeypatch.setattr("sys.argv", ["goal_tracker.py"], raising=False)

        with pytest.raises(SystemExit) as exc_info:
            tracker_core.run_tracker_cli("Goal", "desc")

        assert exc_info.value.code == 1
        _, err = capsys.readouterr()
        assert "Error parsing configuration file:" in err

    def test_run_tracker_cli_handles_unexpected_error(self, monkeypatch, capsys):
        """CLI should exit with status 1 and message on unexpected errors."""

        class _ConfigStub:
            def get_output_dir(self):
                return Path("output")

            def get_output_filename(self):
                return "goal_tracker_template.pdf"

        class _BrokenPDF:
            def __init__(self, config, year=None, tracker_type="Goal"):
                pass

            def generate(self, output_path):
                raise RuntimeError("boom")

        monkeypatch.setattr(tracker_core, "GoalTrackerConfig", lambda config_path: _ConfigStub())
        monkeypatch.setattr(tracker_core, "GoalTrackerPDF", _BrokenPDF)
        monkeypatch.setattr("sys.argv", ["goal_tracker.py"], raising=False)

        with pytest.raises(SystemExit) as exc_info:
            tracker_core.run_tracker_cli("Goal", "desc")

        assert exc_info.value.code == 1
        _, err = capsys.readouterr()
        assert "Error generating PDF:" in err
