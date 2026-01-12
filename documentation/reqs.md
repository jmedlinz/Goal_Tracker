# Goal Tracker PDF Generator - Requirements & Specification

## Project Overview

This project creates a printable annual Goal Tracker PDF that enables users to track a single goal throughout the year. The PDF is designed to be printed and filled out manually, providing a physical, visual representation of goal progress across quarterly, monthly, and weekly timelines.

### Purpose
- Track one primary goal through the entire year
- Provide hierarchical goal breakdown: Quarterly → Monthly → Weekly
- Enable manual tracking and reflection
- Create a printable, printer-friendly document

---

## Output Specifications

### PDF Format
- **Paper Size**: US Letter (8.5" × 11")
- **Orientation**: Portrait only
- **Color Scheme**: Black/White/Greyscale (optimized for monochrome printing)
- **Compatibility**: Must work with common PDF viewers (Adobe Reader, Preview, Chrome, Firefox) and standard printers

---

## Page Layout & Structure

### Header Section
Located at the top of the page:
1. **Title**: "Goal Tracker" (bold, same font size as Goal label for compactness)
2. **Date**: Subheader below the title with label "Date:" and a horizontal line for user input
3. **Goal**: Placed to the right of Title/Date, with label "Goal:" and two horizontal lines for writing
4. **Header Spacing**: Compact header; no separator line under the header

### Column Structure
The page contains 4 columns from left to right:

1. **Quarterly Goals Column** (narrow)
2. **Monthly Goals Column** (narrow, same width as Quarterly)
3. **Weekly Goals Column** (wider, to accommodate more text)
4. **Checkbox Column** (narrow, for weekly completion tracking)

### Column Width Guidelines
- Quarterly and Monthly columns: **Equal width** (1.75 inches each)
- Weekly column: **Wider** (3.5 inches)
- Checkbox column: **Narrow** (0.15 inches for square checkboxes)

---

## Row Structure & Vertical Alignment

### Overview
- **Total Rows**: 52 (one per week of the year)
- **Quarters**: 4 quarters × 13 weeks each = 52 weeks
- **Months**: 12 months × 4 weeks each = 48 weeks (+ 4 catch-up weeks)

### Quarterly Goals Section (Column 1)

**Structure**:
- 4 quarters: Q1, Q2, Q3, Q4
### Column Width Guidelines
- Quarterly and Monthly columns: **Equal width** (approximately 1.75 inches each)
- Weekly column: **Wider** (approximately 3.5 inches)
- Checkbox column: **Narrow** (approximately 0.15 inches for square checkboxes)
**Implementation Details**:
- First row of each quarter: Print quarter label ("Q1", "Q2", "Q3", "Q4")
- Rows 1-6 of each quarter: Horizontal lines for user to write goals
- Rows 7-13: Blank (aligned with weeks 7-13 of that quarter)

**Quarter Mapping**:
- Q3: Weeks 27-39
- Q4: Weeks 40-52

### Monthly Goals Section (Column 2)

**Structure**:
- 12 months (Jan-Dec)
- Each month spans **4 weeks vertically**
- Each month has a horizontal line on every row for writing

**Special Case - Catch-up Weeks**:
- Every 13th week is a "catch-up week" with **no month label, no lines, and no text** in the Monthly column
- Weekly column shows an italic guidance message: e.g., "Close out Q1. Set Q2 goals." and for Q4 "Close out Q4. Set next year's goals."
- Catch-up weeks occur at: Week 13, Week 26, Week 39, Week 52
- The monthly column should show **completely blank space** (empty, no gridlines, no labels) for these weeks
  quarterly_column_width: 1.75
  monthly_column_width: 1.75
  weekly_column_width: 3.5
- Jan: Weeks 1-4
- Feb: Weeks 5-8
- Mar: Weeks 9-12
- *(Week 13: Catch-up week)*
- Apr: Weeks 14-17
- May: Weeks 18-21
- Jun: Weeks 22-25
- *(Week 26: Catch-up week)*
- Jul: Weeks 27-30
- Aug: Weeks 31-34
- Sep: Weeks 35-38
- *(Week 39: Catch-up week)*
- Oct: Weeks 40-43
- Nov: Weeks 44-47
- Dec: Weeks 48-51
- *(Week 52: Catch-up week)*

### Weekly Goals Section (Column 3)

**Structure**:
- 52 rows (one per week)
- Each row contains:
  - Week number (1-52)

**Implementation Details**:
- Format: `[1-52]: ` (right-aligned)
- Week numbers are sequential from 1 to 52 (grey, 8pt)
- All 52 weeks are present, including catch-up weeks (13, 26, 39, 52)
- Thin horizontal writing lines at the bottom of each row, trimmed on both sides for aesthetics

### Checkbox Column (Column 4)

**Structure**:
- 52 checkbox squares (one per week)
- Each checkbox aligned with its corresponding week row

**Implementation Details**:
- Checkboxes must be **perfect squares** (e.g., 0.15" × 0.15")
- Simple empty square border for users to mark manually
- Vertically centered with each week row

---

## Design Specifications

### Typography

**Fonts**:
- Use **Helvetica** or **Arial** (sans-serif) for clarity and printability
- Font sizes:
  - Header title ("Goal Tracker"): 14pt, bold
  - Goal input lines: 10-12pt
  - Quarter labels (Q1, Q2, etc.): 9-10pt, bold
  - Month abbreviations: 8-9pt, bold
  - Week numbers: 8-9pt
  - General text/lines: 8pt

### Spacing & Layout

**Margins**:
- Top: 0.3 inches
- Bottom: 0.3 inches
- Left: 0.3 inches
- Right: 0.3 inches
**Grid Alignment**:
- Grid is horizontally centered on the page

**Row Height**:
- Each week row: Approximately 0.175-0.20 inches (calculated to fit 52 rows + header within page height)
- Ensure consistent spacing for visual alignment

**Line Spacing**:
- Adequate space between weekly rows for legible handwriting
- Horizontal lines for writing should be visible but not overwhelming

### Visual Elements

**Lines & Borders**:
- Horizontal lines for writing: Thin, black lines (≈0.3pt stroke)
- Column separators: No vertical separators in minimal mode
- Quarter/month boundaries: minimal styling; no dotted lines
- Boxes: A box outlines each quarter (spanning all columns) and each month (spanning monthly, weekly, and checkbox columns)

**Grid/Table**:
- Use a subtle grid structure to keep columns and rows aligned
- Light grey borders around each cell (optional, for clarity)

**Checkboxes**:
- Simple square outline: 1pt black stroke
- Size: 0.15" × 0.15" (or similar to maintain square aspect ratio)

---

## Technical Requirements

### Python Implementation

**Language & Environment**:
- Python 3.10+
- Use **Poetry** for dependency and environment management
  - Create poetry environment locally (not globally)
  - Include `poetry.toml` to configure local virtual environments

**Required Libraries**:
- **ReportLab**: PDF generation (similar to habit_tracker reference)
- **PyYAML**: Configuration file management
- Other standard libraries as needed (pathlib, argparse, etc.)

**Code Quality**:
- Modular design with clear separation of concerns
- Well-documented code (docstrings for all classes and functions)
- Type hints where appropriate
- Error handling for:
  - File I/O operations
  - PDF generation failures
  - Invalid configuration
  - Missing dependencies

### Project Structure

```
Goal_Tracker/
├── goal_tracker.py          # Main script
├── config.yaml              # Configuration file (fonts, spacing, layout)
├── pyproject.toml           # Poetry dependencies
├── poetry.toml              # Poetry configuration (local venv)
├── poetry.lock              # Locked dependencies
├── README.md                # Project documentation
├── LICENSE                  # License file
├── .gitignore              # Git ignore file
├── documentation/
│   └── reqs.md             # This file
├── tests/
│   └── test_goal_tracker.py  # Unit tests
└── output/                  # Generated PDFs (created at runtime)
```

### Configuration File (config.yaml)

Should include settings for:
- **Page settings**: size, orientation, margins
- **Font settings**: family, sizes for different elements
- **Colors**: RGB values for grid lines, text, etc.
- **Layout dimensions**: column widths, row heights, spacing
- **Output settings**: default filename, directory

Example structure (current defaults):
```yaml
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
  title_size: 14
  goal_line_size: 10
  quarter_label_size: 10
  month_label_size: 9
  week_number_size: 8

colors:
  grid_line: [0, 0, 0]        # Black
  light_grid: [180, 180, 180]  # Light grey
  text: [0, 0, 0]              # Black

layout:
  quarterly_column_width: 1.75
  monthly_column_width: 1.75
  weekly_column_width: 3.5
  checkbox_size: 0.15
  row_height: 0.185

output:
  directory: "output"
  filename: "goal_tracker_template.pdf"
```

### Code Modules

**Main Classes**:
1. **GoalTrackerConfig**: Loads and manages configuration from YAML
2. **GoalTrackerPDF**: Generates the PDF with all layout logic
3. **LayoutManager**: Calculates positions, dimensions, and coordinates
4. **DrawingHelper**: Utility functions for drawing lines, boxes, text

**Main Functions**:
1. `generate_pdf()`: Main entry point to create the PDF
2. `draw_header()`: Renders header section with title and goal lines
3. `draw_quarterly_column()`: Renders quarterly goals column
4. `draw_monthly_column()`: Renders monthly goals column with catch-up logic
5. `draw_weekly_column()`: Renders weekly goals column
6. `draw_checkbox_column()`: Renders checkbox column
7. `draw_grid()`: Renders grid lines and borders

---

## Usage & Execution

### Installation

```bash
# Clone the repository
cd Goal_Tracker

# Install dependencies using Poetry
poetry install

# Activate the virtual environment
poetry shell
```

### Running the Generator

```bash
# Generate PDF with default settings
poetry run python goal_tracker.py

# Generate PDF with custom config
poetry run python goal_tracker.py --config custom_config.yaml

# Specify output filename
poetry run python goal_tracker.py --output my_goal_tracker.pdf
```

### Command-line Arguments

- `--config`: Path to configuration file (default: `config.yaml`)
- `--output`: Output PDF filename (default: from config.yaml)
- `--help`: Show help message

---

## README Requirements

The README.md file should include:

1. **Project Overview**: Brief description of the Goal Tracker PDF generator
2. **Features**: List of key features (annual tracking, quarterly/monthly/weekly breakdown, printable)
3. **Installation**:
   - Prerequisites (Python 3.10+, Poetry)
   - Step-by-step installation instructions
4. **Usage**:
   - How to generate the PDF
   - Command-line options
   - How to customize via config.yaml
5. **Project Structure**: Brief overview of files and folders
6. **Configuration**: How to modify settings
7. **Development**:
   - Running tests
   - Contributing guidelines (if applicable)
8. **License**: Link to LICENSE file
9. **Example Output**: Description or screenshot of generated PDF

---

## Testing Requirements

### Unit Tests
- Test configuration loading
- Test layout calculations (row heights, column widths, positions)
- Test month/week/quarter mappings
- Test catch-up week logic
- Test PDF generation (mock/stub the actual PDF output)

### Integration Tests
- Generate a sample PDF and verify it's created successfully
- Verify PDF is valid and openable in PDF readers

### Manual Testing
- Print the PDF on a physical printer
- Verify all text is readable
- Verify lines are aligned and usable for handwriting
- Verify checkboxes are the correct size
- Verify layout fits on one page without cutoff

---

## Reference: Habit Tracker Comparison

This project uses the Habit Tracker repository as a structural and design reference:

**Similarities**:
- Uses ReportLab for PDF generation
- Uses YAML for configuration
- Uses Poetry for dependency management
- Modular, well-documented code
- Clean, printable design

**Differences**:
- Goal Tracker is for **annual** tracking (52 weeks), Habit Tracker is for **monthly** tracking (28-31 days)
- Goal Tracker has **hierarchical structure** (Quarterly → Monthly → Weekly), Habit Tracker has daily habits
- Goal Tracker uses **columns** for different time periods, Habit Tracker uses rows for different habits
- Goal Tracker is a **blank template**, Habit Tracker requires habits input file

---

## Success Criteria

The project is successful when:

1. ✅ A single-page PDF is generated that fits on US Letter paper
2. ✅ All 52 weeks are present with checkboxes
3. ✅ Quarterly section shows Q1-Q4 with 6 lines each
4. ✅ Monthly section shows Jan-Dec with proper 4-week alignment and catch-up weeks (13, 26, 39, 52) are blank
5. ✅ Weekly section shows weeks 1-52 with thin horizontal lines for writing
6. ✅ Layout is clean, readable, and printable in black/white
7. ✅ Code is modular, documented, and includes error handling
8. ✅ Poetry environment works correctly
9. ✅ README provides clear installation and usage instructions
10. ✅ Generated PDF is compatible with common PDF viewers and printers

---

## Deliverables

1. **goal_tracker.py**: Main Python script
2. **config.yaml**: Configuration file
3. **pyproject.toml**: Poetry dependencies
4. **poetry.toml**: Poetry local configuration
5. **README.md**: Project documentation
6. **LICENSE**: Open source license (if applicable)
7. **tests/**: Unit and integration tests
8. **output/goal_tracker_template.pdf**: Sample generated PDF

---

## Notes & Considerations

- **Generic Year Design**: Do not include specific year dates (2025, 2026, etc.) to keep the PDF reusable
- **Catch-up Weeks**: Ensure weeks 13, 26, 39, 52 have blank monthly sections but still have week numbers and checkboxes
- **Print Testing**: Always test the final PDF by printing on a physical printer to verify alignment and readability
- **Font Availability**: Use common fonts (Helvetica, Arial) that are universally available
- **PDF Compatibility**: Test with multiple PDF readers (Adobe, Preview, Chrome, Firefox)

---

## Future Enhancements (Optional)

Ideas for future versions:
- Add an optional "Year" field in the header
- Include a notes/reflection section at the bottom
- Add optional color themes (while maintaining print-friendly design)
- Generate quarterly or monthly versions (instead of annual)
- Add progress indicators or visual graphs
- Support A4 paper size in addition to Letter
