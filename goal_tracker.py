"""
Goal Tracker PDF Generator

This module generates a printable annual Goal Tracker PDF that enables users to
track a single goal throughout the year with quarterly, monthly, and weekly breakdowns.
"""

import argparse
import calendar
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas


@dataclass
class PageConfig:
    """Configuration for page settings."""

    width: float
    height: float
    top_margin: float
    bottom_margin: float
    left_margin: float
    right_margin: float


@dataclass
class FontConfig:
    """Configuration for font settings."""

    family: str
    title_size: int
    goal_line_size: int
    quarter_label_size: int
    month_label_size: int
    week_number_size: int


class GoalTrackerConfig:
    """Loads and manages configuration from YAML file."""

    def __init__(self, config_path: str):
        """
        Initialize configuration from YAML file.

        Args:
            config_path: Path to the configuration YAML file

        Raises:
            FileNotFoundError: If config file is not found
            yaml.YAMLError: If config file is invalid YAML
        """
        self.config_path = Path(config_path)

        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(self.config_path) as f:
            self.config = yaml.safe_load(f)

        self._validate_config()

    def _validate_config(self) -> None:
        """Validate that required configuration keys are present."""
        required_keys = ["page", "fonts", "colors", "layout", "output"]
        for key in required_keys:
            if key not in self.config:
                raise ValueError(f"Missing required config key: {key}")

    def get_page_config(self) -> PageConfig:
        """Get page configuration."""
        page_cfg = self.config["page"]
        margins = page_cfg["margins"]

        return PageConfig(
            width=8.5 * inch,
            height=11.0 * inch,
            top_margin=margins["top"] * inch,
            bottom_margin=margins["bottom"] * inch,
            left_margin=margins["left"] * inch,
            right_margin=margins["right"] * inch,
        )

    def get_font_config(self) -> FontConfig:
        """Get font configuration."""
        fonts = self.config["fonts"]

        return FontConfig(
            family=fonts["family"],
            title_size=fonts["title_size"],
            goal_line_size=fonts["goal_line_size"],
            quarter_label_size=fonts["quarter_label_size"],
            month_label_size=fonts["month_label_size"],
            week_number_size=fonts["week_number_size"],
        )

    def get_colors(self) -> Dict[str, Tuple[int, int, int]]:
        """Get color configuration."""
        colors = self.config.get("colors", {})

        # Provide sensible fallbacks for optional color keys used by rendering
        grid_line = tuple(colors.get("grid_line", (0, 0, 0)))
        light_grid = tuple(colors.get("light_grid", (180, 180, 180)))
        text = tuple(colors.get("text", (0, 0, 0)))
        # Default week numbers to light grid (grey) if unspecified
        week_number = tuple(colors.get("week_number", light_grid))
        # Default row stripes to a very light grey if unspecified
        row_stripe = tuple(colors.get("row_stripe", (230, 230, 230)))

        return {
            "grid_line": grid_line,
            "light_grid": light_grid,
            "text": text,
            "week_number": week_number,
            "row_stripe": row_stripe,
        }

    def get_layout(self) -> Dict:
        """Get layout configuration."""
        return self.config["layout"]

    def get_output_dir(self) -> Path:
        """Get output directory path."""
        output_dir = Path(self.config["output"]["directory"])
        return output_dir

    def get_output_filename(self) -> str:
        """Get output filename."""
        return self.config["output"]["filename"]


class LayoutManager:
    """Calculates positions, dimensions, and coordinates for PDF layout."""

    WEEKS_IN_YEAR = 52
    WEEKS_PER_QUARTER = 13
    WEEKS_PER_MONTH = 4
    MONTHS_IN_YEAR = 12
    QUARTERS_IN_YEAR = 4
    CATCH_UP_WEEKS = {13, 26, 39, 52}

    def __init__(self, page_config: PageConfig, layout_config: Dict):
        """
        Initialize layout manager.

        Args:
            page_config: Page configuration
            layout_config: Layout configuration dictionary
        """
        self.page_config = page_config
        self.layout_config = layout_config
        self._calculate_dimensions()

    def _calculate_dimensions(self) -> None:
        """Calculate available space and row height."""
        self.available_width = (
            self.page_config.width - self.page_config.left_margin - self.page_config.right_margin
        )
        # Borrow a small amount of bottom margin (up to 0.1") to give the grid more vertical space
        # while retaining at least half of the configured bottom margin to avoid print issues.
        bonus_height = min(0.1 * inch, self.page_config.bottom_margin * 0.5)

        self.available_height = (
            self.page_config.height - self.page_config.top_margin - self.page_config.bottom_margin + bonus_height
        )

        # Calculate actual row height to fit all 52 weeks within margins
        header_height = 0.6 * inch
        available_for_rows = self.available_height - header_height
        self.calculated_row_height = available_for_rows / self.WEEKS_IN_YEAR

    def get_column_x_positions(self) -> Dict[str, float]:
        """Get x-coordinates for each column."""
        col_width_q = self.layout_config["quarterly_column_width"] * inch
        col_width_m = self.layout_config["monthly_column_width"] * inch
        col_width_w = self.layout_config["weekly_column_width"] * inch
        col_width_checkbox = self.layout_config["checkbox_size"] * inch

        # Calculate total grid width
        total_grid_width = col_width_q + col_width_m + col_width_w + col_width_checkbox

        # Center the grid horizontally
        x_start = (self.page_config.width - total_grid_width) / 2

        x_quarterly = x_start
        x_monthly = x_quarterly + col_width_q
        x_weekly = x_monthly + col_width_m
        x_checkbox = x_weekly + col_width_w

        return {"quarterly": x_quarterly, "monthly": x_monthly, "weekly": x_weekly, "checkbox": x_checkbox}

    def get_column_widths(self) -> Dict[str, float]:
        """Get width of each column."""
        return {
            "quarterly": self.layout_config["quarterly_column_width"] * inch,
            "monthly": self.layout_config["monthly_column_width"] * inch,
            "weekly": self.layout_config["weekly_column_width"] * inch,
            "checkbox": self.layout_config["checkbox_size"] * inch,
        }

    def get_row_height(self) -> float:
        """Get height of each week row, calculated to fit all 52 weeks within margins."""
        return self.calculated_row_height

    def get_header_height(self) -> float:
        """Get height reserved for header section."""
        # Slightly reduce header height to bring the grid closer to the subheader area
        return 0.5 * inch

    def get_week_y_position(self, week_number: int) -> float:
        """
        Get y-coordinate for a given week.

        Args:
            week_number: Week number (1-52)

        Returns:
            Y-coordinate of the week row
        """
        row_height = self.get_row_height()
        header_height = self.get_header_height()

        y = self.page_config.height - self.page_config.top_margin - header_height - (week_number - 1) * row_height
        return y

    @staticmethod
    def get_quarter_for_week(week_number: int) -> int:
        """Get quarter number (1-4) for a given week."""
        return (week_number - 1) // LayoutManager.WEEKS_PER_QUARTER + 1

    @staticmethod
    def get_month_for_week(week_number: int) -> int:
        """Get month number (1-12) for a given week, or -1 for catch-up weeks."""
        if week_number in LayoutManager.CATCH_UP_WEEKS:
            return -1  # Catch-up week

        # Map week to month
        month_mapping = {
            range(1, 5): 1,
            range(5, 9): 2,
            range(9, 13): 3,
            range(14, 18): 4,
            range(18, 22): 5,
            range(22, 26): 6,
            range(27, 31): 7,
            range(31, 35): 8,
            range(35, 39): 9,
            range(40, 44): 10,
            range(44, 48): 11,
            range(48, 52): 12,
        }

        for week_range, month in month_mapping.items():
            if week_number in week_range:
                return month

        return -1

    @staticmethod
    def is_catch_up_week(week_number: int) -> bool:
        """Check if a week is a catch-up week."""
        return week_number in LayoutManager.CATCH_UP_WEEKS

    @staticmethod
    def get_month_abbreviation(month_number: int) -> str:
        """Get 3-letter abbreviation for month."""
        abbreviations = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        return abbreviations[month_number - 1] if 1 <= month_number <= 12 else ""


class DrawingHelper:
    """Utility functions for drawing lines, boxes, and text."""

    @staticmethod
    def draw_line(
        c: canvas.Canvas,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        stroke_width: float = 0.5,
        color: Tuple[int, int, int] = (0, 0, 0),
        dash: List[int] = None,
    ) -> None:
        """
        Draw a line on the canvas.

        Args:
            c: Canvas object
            x1, y1: Starting coordinates
            x2, y2: Ending coordinates
            stroke_width: Line width in points
            color: RGB color tuple
            dash: Dash pattern as list [on, off] in points
        """
        c.setLineWidth(stroke_width)
        c.setStrokeColorRGB(*[x / 255 for x in color])
        if dash:
            c.setDash(dash)
        c.line(x1, y1, x2, y2)
        if dash:
            c.setDash([])  # Reset to solid
        c.setStrokeColorRGB(0, 0, 0)  # Reset to black

    @staticmethod
    def draw_rectangle(
        c: canvas.Canvas,
        x: float,
        y: float,
        width: float,
        height: float,
        stroke_width: float = 1,
        color: Tuple[int, int, int] = (0, 0, 0),
    ) -> None:
        """
        Draw a rectangle outline on the canvas.

        Args:
            c: Canvas object
            x, y: Bottom-left corner coordinates
            width, height: Rectangle dimensions
            stroke_width: Line width in points
            color: RGB color tuple
        """
        c.setLineWidth(stroke_width)
        c.setStrokeColorRGB(*[x / 255 for x in color])
        c.rect(x, y, width, height, fill=0)
        c.setStrokeColorRGB(0, 0, 0)  # Reset to black

    @staticmethod
    def draw_text(
        c: canvas.Canvas,
        text: str,
        x: float,
        y: float,
        font: str = "Helvetica",
        size: int = 10,
        color: Tuple[int, int, int] = (0, 0, 0),
        align: str = "left",
    ) -> None:
        """
        Draw text on the canvas.

        Args:
            c: Canvas object
            text: Text to draw
            x, y: Coordinates
            font: Font family
            size: Font size in points
            color: RGB color tuple
            align: Text alignment ('left' or 'right')
        """
        c.setFont(font, size)
        c.setFillColorRGB(*[x / 255 for x in color])
        if align == "right":
            c.drawRightString(x, y, text)
        else:
            c.drawString(x, y, text)
        c.setFillColorRGB(0, 0, 0)  # Reset to black


class GoalTrackerPDF:
    """Generates the Goal Tracker PDF with all layout logic."""

    def __init__(self, config: GoalTrackerConfig, year: Optional[int] = None):
        """
        Initialize PDF generator.

        Args:
            config: GoalTrackerConfig instance
            year: Year to display in the header; defaults to current year
        """
        self.config = config
        self.page_config = config.get_page_config()
        self.font_config = config.get_font_config()
        self.colors = config.get_colors()
        self.layout_config = config.get_layout()
        self.layout = LayoutManager(self.page_config, self.layout_config)
        self.year = year if year is not None else datetime.now().year

    def generate(self, output_path: str) -> None:
        """
        Generate the PDF file.

        Args:
            output_path: Path where the PDF should be saved
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        c = canvas.Canvas(str(output_path), pagesize=(self.page_config.width, self.page_config.height))

        # Draw all sections
        self.draw_header(c)
        self.draw_grid(c)
        self.draw_quarterly_column(c)
        self.draw_monthly_column(c)
        self.draw_weekly_column(c)
        self.draw_checkbox_column(c)

        c.save()

    def draw_header(self, c: canvas.Canvas) -> None:
        """
        Render header section with title and goal lines.

        Args:
            c: Canvas object
        """
        # Define header area
        header_top_y = self.page_config.height - self.page_config.top_margin
        header_height = self.layout.get_header_height()
        header_top_y - header_height

        # Get grid boundaries for alignment
        col_positions = self.layout.get_column_x_positions()
        col_widths = self.layout.get_column_widths()
        grid_left = col_positions["quarterly"]
        grid_right = col_positions["checkbox"] + col_widths["checkbox"]
        grid_width = grid_right - grid_left

        # Allocate space: left 40% for Title/Date, right 60% for Goal
        left_w = grid_width * 0.4
        right_x = grid_left + left_w
        grid_width - left_w
        pad_x = 0.1 * inch

        # Left: Title aligned to grid left (include year in title)
        title_y = header_top_y - 0.10 * inch
        DrawingHelper.draw_text(
            c,
            f"Goal Tracker for {self.year}",
            grid_left + pad_x,
            title_y,
            font="Helvetica-Bold",
            size=self.font_config.goal_line_size,
            color=self.colors["text"],
        )

        # Right: Goal label and two lines, aligned to grid right
        goal_label_y = title_y
        DrawingHelper.draw_text(
            c,
            "Goal:",
            right_x + pad_x,
            goal_label_y,
            font=self.font_config.family,
            size=self.font_config.goal_line_size,
            color=self.colors["text"],
        )
        goal_line_start = right_x + pad_x + 0.6 * inch
        goal_line_end = grid_right - pad_x  # Align to grid right
        # Align the first input line with the Goal label baseline
        line1_y = goal_label_y
        # Second line below for additional goal detail with extra spacing between lines
        line_spacing = 0.05 * inch
        line2_y = title_y - 0.15 * inch - line_spacing
        DrawingHelper.draw_line(
            c, goal_line_start, line1_y, goal_line_end, line1_y, stroke_width=0.5, color=self.colors["text"]
        )
        DrawingHelper.draw_line(
            c, goal_line_start, line2_y, goal_line_end, line2_y, stroke_width=0.5, color=self.colors["text"]
        )

    def draw_grid(self, c: canvas.Canvas) -> None:
        """
        Render grid lines and borders.

        Args:
            c: Canvas object
        """
        col_positions = self.layout.get_column_x_positions()
        col_widths = self.layout.get_column_widths()
        row_height = self.layout.get_row_height()
        header_height = self.layout.get_header_height()
        layout_config = self.config.get_layout()

        # Top of content area
        y_top = self.page_config.height - self.page_config.top_margin - header_height

        # Bottom of content area
        y_bottom = self.page_config.bottom_margin

        # Calculate right edge of content
        x_right = col_positions["checkbox"] + col_widths["checkbox"]

        # Draw row stripes if enabled
        if layout_config.get("show_row_stripes", False):
            stripe_color_rgb = [x / 255 for x in self.colors["row_stripe"]]

            for week in range(1, self.layout.WEEKS_IN_YEAR + 1):
                y = self.layout.get_week_y_position(week)

                # Skip shading on quarterly column

                # Shade alternating months (2, 4, 6, 8, 10, 12)
                month = self.layout.get_month_for_week(week)
                if month > 0 and month % 2 == 0:  # Even months only
                    c.setFillColorRGB(*stripe_color_rgb)
                    c.rect(
                        col_positions["monthly"],
                        y - row_height,
                        col_widths["monthly"],
                        row_height,
                        fill=1,
                        stroke=0,
                    )
                    c.setFillColorRGB(0, 0, 0)

                # Shade alternating weeks (2, 4, 6, 8, etc.)
                if week % 2 == 0:  # Even weeks
                    c.setFillColorRGB(*stripe_color_rgb)
                    c.rect(
                        col_positions["weekly"], y - row_height, col_widths["weekly"], row_height, fill=1, stroke=0
                    )
                    c.setFillColorRGB(0, 0, 0)

        # Get weekly line weight from config
        weekly_line_weight = layout_config.get("weekly_line_weight", 0.5)

        # Draw horizontal lines for each week
        for week in range(1, self.layout.WEEKS_IN_YEAR + 1):
            y = self.layout.get_week_y_position(week)

            # Draw thin line at bottom of row (subtract row height)
            line_y = y - row_height
            line_start = col_positions["weekly"] + 0.1 * inch
            # Apply 1/8" trim on the left for all weekly lines
            line_start += 0.125 * inch
            # Shorten the left side by an additional ~0.1" to keep day numbers off the line
            line_start += 0.1 * inch

            # Base right boundary with prior adjustments
            line_end = (
                col_positions["checkbox"] + col_widths["checkbox"] - 0.05 * inch - 0.125 * inch + 0.0625 * inch
            )
            # Apply an additional 1/8" trim on the right for all weekly lines
            line_end -= 0.125 * inch
            DrawingHelper.draw_line(
                c,
                line_start,
                line_y,
                line_end,
                line_y,
                stroke_width=weekly_line_weight,
                color=self.colors["text"],  # Dark/black line
            )

        # Draw quarter boxes
        for quarter_num in range(1, self.layout.QUARTERS_IN_YEAR + 1):
            start_week = (quarter_num - 1) * self.layout.WEEKS_PER_QUARTER + 1
            end_week = start_week + self.layout.WEEKS_PER_QUARTER - 1

            # Top of the quarter (top of first week row)
            y_top = self.layout.get_week_y_position(start_week)

            # Bottom of the quarter (bottom of last week row)
            y_bottom = self.layout.get_week_y_position(end_week) - row_height

            # Left edge (quarterly column start) and right edge (right side of checkbox column)
            x_left = col_positions["quarterly"]
            x_right = col_positions["checkbox"] + col_widths["checkbox"]

            # Draw the box outline
            DrawingHelper.draw_rectangle(
                c,
                x_left,
                y_bottom,
                x_right - x_left,
                y_top - y_bottom,
                stroke_width=1.0,
                color=self.colors["grid_line"],
            )

        # Draw month boxes
        # Build month structure like in draw_monthly_column
        month_lines = {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: [], 8: [], 9: [], 10: [], 11: [], 12: []}

        current_month = 1
        month_week_count = 0

        for week in range(1, self.layout.WEEKS_IN_YEAR + 1):
            if self.layout.is_catch_up_week(week):
                continue

            month_week_count += 1

            if month_week_count > self.layout.WEEKS_PER_MONTH:
                current_month += 1
                month_week_count = 1

            month_lines[current_month].append(week)

        # Draw boxes for each month
        for month_num in range(1, self.layout.MONTHS_IN_YEAR + 1):
            weeks = month_lines[month_num]
            if not weeks:
                continue

            first_week = weeks[0]
            last_week = weeks[-1]

            # Top of the month (top of first week row)
            y_top = self.layout.get_week_y_position(first_week)

            # Bottom of the month (bottom of last week row)
            y_bottom = self.layout.get_week_y_position(last_week) - row_height

            # Left edge (monthly column start) and right edge (right side of checkbox column)
            x_left = col_positions["monthly"]
            x_right = col_positions["checkbox"] + col_widths["checkbox"]

            # Draw the box outline
            DrawingHelper.draw_rectangle(
                c,
                x_left,
                y_bottom,
                x_right - x_left,
                y_top - y_bottom,
                stroke_width=0.75,
                color=self.colors["grid_line"],
            )

    def draw_quarterly_column(self, c: canvas.Canvas) -> None:
        """
        Render quarterly goals column.

        Args:
            c: Canvas object
        """
        col_x = self.layout.get_column_x_positions()["quarterly"]
        col_width = self.layout.get_column_widths()["quarterly"]
        row_height = self.layout.get_row_height()
        layout_config = self.config.get_layout()
        label_padding_y = layout_config.get("label_padding_y", 0.07) * inch

        quarters = ["Q1", "Q2", "Q3", "Q4"]
        lines_per_quarter = 6

        for quarter_num in range(1, self.layout.QUARTERS_IN_YEAR + 1):
            start_week = (quarter_num - 1) * self.layout.WEEKS_PER_QUARTER + 1
            y_start = self.layout.get_week_y_position(start_week)

            # Draw quarter label with label padding below the grey line
            y_label = y_start - row_height / 2 - label_padding_y
            DrawingHelper.draw_text(
                c,
                quarters[quarter_num - 1],
                col_x + 0.1 * inch,
                y_label,
                font=self.font_config.family,
                size=self.font_config.quarter_label_size,
                color=self.colors["text"],
            )

            # Draw lines for writing goals (6 lines per quarter, skip first)
            y = y_start - row_height
            for line_num in range(lines_per_quarter):
                if line_num == 0:  # Skip the first line under the label
                    y -= row_height
                    continue
                line_x_start = col_x + 0.05 * inch
                line_x_end = col_x + col_width - 0.05 * inch
                DrawingHelper.draw_line(
                    c, line_x_start, y, line_x_end, y, stroke_width=0.5, color=self.colors["text"]
                )
                y -= row_height

    def draw_monthly_column(self, c: canvas.Canvas) -> None:
        """
        Render monthly goals column with catch-up week handling.

        Args:
            c: Canvas object
        """
        col_x = self.layout.get_column_x_positions()["monthly"]
        col_width = self.layout.get_column_widths()["monthly"]
        row_height = self.layout.get_row_height()
        layout_config = self.config.get_layout()
        label_padding_y = layout_config.get("label_padding_y", 0.07) * inch

        month_lines = {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: [], 8: [], 9: [], 10: [], 11: [], 12: []}

        # Track weeks for each month
        current_month = 1
        month_week_count = 0

        for week in range(1, self.layout.WEEKS_IN_YEAR + 1):
            if self.layout.is_catch_up_week(week):
                continue

            month_week_count += 1

            if month_week_count > self.layout.WEEKS_PER_MONTH:
                current_month += 1
                month_week_count = 1

            month_lines[current_month].append(week)

        # Draw month labels and lines
        for month_num in range(1, self.layout.MONTHS_IN_YEAR + 1):
            weeks = month_lines[month_num]
            if not weeks:
                continue

            first_week = weeks[0]
            y_start = self.layout.get_week_y_position(first_week)

            # Draw month label with label padding below the grey line
            month_abbrev = self.layout.get_month_abbreviation(month_num)
            y_label = y_start - row_height / 2 - label_padding_y
            DrawingHelper.draw_text(
                c,
                month_abbrev,
                col_x + 0.1 * inch,
                y_label,
                font=self.font_config.family,
                size=self.font_config.month_label_size,
                color=self.colors["text"],
            )

            # Draw lines for writing goals
            y = y_start - row_height
            for _ in weeks:
                line_x_start = col_x + 0.05 * inch
                line_x_end = col_x + col_width - 0.05 * inch
                DrawingHelper.draw_line(
                    c, line_x_start, y, line_x_end, y, stroke_width=0.5, color=self.colors["text"]
                )
                y -= row_height

    def draw_weekly_column(self, c: canvas.Canvas) -> None:
        """
        Render weekly goals column.

        Args:
            c: Canvas object
        """
        col_x = self.layout.get_column_x_positions()["weekly"]
        col_width = self.layout.get_column_widths()["weekly"]
        row_height = self.layout.get_row_height()
        layout_config = self.config.get_layout()
        label_padding_y = layout_config.get("label_padding_y", 0.07) * inch

        # Find the Monday of ISO week 1 for the given year
        # ISO week 1 is the week containing the first Thursday (or Jan 4)
        jan4 = datetime(self.year, 1, 4)
        # Find the Monday of the week containing Jan 4
        days_since_monday = jan4.weekday()  # 0=Monday, 6=Sunday
        iso_week1_monday = jan4 - timedelta(days=days_since_monday)
        # Determine if the ISO year has 53 weeks (ISO last week check via Dec 28)
        has_iso_53 = datetime(self.year, 12, 28).isocalendar()[1] == 53
        start_iso_week = 2 if has_iso_53 else 1

        for row_index in range(1, self.layout.WEEKS_IN_YEAR + 1):
            y = self.layout.get_week_y_position(row_index)

            # Calculate actual date range for this ISO week (Monday to Friday)
            iso_week_num = start_iso_week + row_index - 1
            week_monday = iso_week1_monday + timedelta(days=(iso_week_num - 1) * 7)
            week_friday = week_monday + timedelta(days=4)

            # Format the date range with just day numbers
            day_range = f"{week_monday.day}-{week_friday.day}"

            # Draw only the day range, centered within a narrow band near the column start
            week_text = f"{day_range}"
            week_text_width = c.stringWidth(week_text, self.font_config.family, self.font_config.week_number_size - 1)
            band_start = col_x + 0.03 * inch
            band_width = 0.25 * inch
            text_x = band_start + (band_width - week_text_width) / 2
            y_text = y - row_height / 2 - label_padding_y

            DrawingHelper.draw_text(
                c,
                week_text,
                text_x,
                y_text,
                font=self.font_config.family,
                size=self.font_config.week_number_size - 1,
                color=self.colors["week_number"],
                align="left",
            )

            # Catch-up messaging in weekly column
            # Keep catch-up markers tied to the row positions (13, 26, 39, 52)
            if self.layout.is_catch_up_week(row_index):
                quarter = self.layout.get_quarter_for_week(row_index)
                if quarter == 4:
                    catch_up_text = "Close out Q4. Set next year's goals."
                elif quarter == 1:
                    catch_up_text = "Close out Q1. Set Q2 goals."
                else:
                    catch_up_text = f"Close out Q{quarter}. Set Q{quarter + 1} goals."

                # Place message starting just to the right of the day range (~0.40" after day numbers)
                message_x = col_x + 0.43 * inch
                DrawingHelper.draw_text(
                    c,
                    catch_up_text,
                    message_x,
                    y_text,
                    font=self.font_config.family + "-Oblique",
                    size=self.font_config.week_number_size,
                    color=self.colors["week_number"],
                    align="left",
                )

    def draw_checkbox_column(self, c: canvas.Canvas) -> None:
        """
        Render checkbox column.

        Args:
            c: Canvas object
        """
        col_x = self.layout.get_column_x_positions()["checkbox"]
        checkbox_size = self.layout.get_column_widths()["checkbox"]
        row_height = self.layout.get_row_height()

        for week in range(1, self.layout.WEEKS_IN_YEAR + 1):
            y = self.layout.get_week_y_position(week)

            # Center checkbox in column
            box_x = col_x + (checkbox_size - self.layout_config["checkbox_size"] * inch) / 2
            box_y = y - row_height / 2 - self.layout_config["checkbox_size"] * inch / 2

            # Draw checkbox square
            DrawingHelper.draw_rectangle(
                c,
                box_x,
                box_y,
                self.layout_config["checkbox_size"] * inch,
                self.layout_config["checkbox_size"] * inch,
                stroke_width=1,
                color=self.colors["text"],
            )


def main() -> None:
    """Main entry point for the Goal Tracker PDF generator."""
    parser = argparse.ArgumentParser(description="Generate a printable annual Goal Tracker PDF")
    parser.add_argument(
        "--config", default="config.yaml", help="Path to configuration file (default: config.yaml)"
    )
    parser.add_argument("--output", default=None, help="Output PDF filename (default: from config.yaml)")
    parser.add_argument("year", nargs="?", type=int, help="Year to display in the header (default: current year)")

    args = parser.parse_args()

    year = args.year if args.year is not None else datetime.now().year

    try:
        # Load configuration
        config = GoalTrackerConfig(args.config)

        # Determine output path
        if args.output:
            output_path = args.output
        else:
            output_dir = config.get_output_dir()
            output_filename = config.get_output_filename()
            output_path = output_dir / output_filename

        # Inform user if using ISO week 2-53 alignment
        try:
            if datetime(year, 12, 28).isocalendar()[1] == 53:
                print("Note: For better alignment, starting at ISO week 2.")
        except Exception:
            pass

        # Generate PDF
        pdf_generator = GoalTrackerPDF(config, year=year)
        pdf_generator.generate(str(output_path))

        print(f"✓ PDF generated successfully: {output_path}")

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing configuration file: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error generating PDF: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
