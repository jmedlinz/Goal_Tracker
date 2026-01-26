"""
Unit and integration tests for Goal Tracker PDF Generator
"""

from unittest.mock import Mock, patch

import pytest

import goal_tracker
from goal_tracker import (
    DrawingHelper,
    FontConfig,
    GoalTrackerConfig,
    GoalTrackerPDF,
    LayoutManager,
    PageConfig,
  main as goal_tracker_main,
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

    @patch("goal_tracker.canvas.Canvas")
    def test_draw_line(self, mock_canvas):
        """Test drawing a line."""
        c = Mock()
        DrawingHelper.draw_line(c, 0, 0, 100, 100)

        c.setLineWidth.assert_called()
        c.setStrokeColorRGB.assert_called()
        c.line.assert_called_with(0, 0, 100, 100)

    @patch("goal_tracker.canvas.Canvas")
    def test_draw_rectangle(self, mock_canvas):
        """Test drawing a rectangle."""
        c = Mock()
        DrawingHelper.draw_rectangle(c, 0, 0, 50, 50)

        c.setLineWidth.assert_called()
        c.setStrokeColorRGB.assert_called()
        c.rect.assert_called()

    @patch("goal_tracker.canvas.Canvas")
    def test_draw_text(self, mock_canvas):
        """Test drawing text."""
        c = Mock()
        DrawingHelper.draw_text(c, "Test", 0, 0)

        c.setFont.assert_called()
        c.setFillColorRGB.assert_called()
        c.drawString.assert_called_with(0, 0, "Test")


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
    monkeypatch.setattr(goal_tracker.GoalTrackerPDF, "generate", lambda self, output_path: None)

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
