import dash
from dash import dcc, html, Input, Output
import datetime
import logging
import os
import sys
import argparse

# Import data fetching utilities
import database_utils
from database_utils import fetch_store_names

# Configure logging to screen and file
# Parse command line arguments for database location
parser = argparse.ArgumentParser(description="MLX Enterprise Analysis Dashboard")
parser.add_argument(
    "--database",
    default=database_utils.DB_PATH,
    help="Path to the SQLite database file",
)
parser.add_argument(
    "--log-level",
    type=int,
    choices=[0, 1, 2, 3],
    default=1,
    help="Set logging level: 0=ERROR, 1=WARNING, 2=INFO, 3=DEBUG (default: 1)",
)
args, _ = parser.parse_known_args()

# Update the database path in the utility module
database_utils.DB_PATH = os.path.abspath(args.database)
database_utils.DB_NAME = os.path.basename(args.database)

# Map numeric log level to logging constants
LOG_LEVEL_MAP = {
    0: logging.ERROR,
    1: logging.WARNING,
    2: logging.INFO,
    3: logging.DEBUG,
}
target_log_level = LOG_LEVEL_MAP.get(args.log_level, logging.WARNING)

# Configure logging to screen and file
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "log")
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=target_log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - L%(lineno)d - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "store_analysis.log")),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)
logger.info(f"\n\n####################### START #########################\n\n")
logger.info(f"Using database at: {database_utils.DB_PATH}")

# Initialize the Dash app
app = dash.Dash(__name__, use_pages=True, suppress_callback_exceptions=True)

app.layout = html.Div(
    style={"backgroundColor": "#111111", "minHeight": "100vh"},
    children=[
        # Fixed Header Section: Contains Title, Filters, and Tabs
        html.Div(
            style={
                "position": "fixed",
                "top": "0",
                "left": "0",
                "width": "100%",
                "zIndex": "1000",
                "backgroundColor": "#111111",
                "padding": "20px 20px 0 20px",
                "borderBottom": "1px solid #333333",
            },
            children=[
                html.H1(
                    children="Store Analysis Dashboard",
                    style={
                        "textAlign": "center",
                        "color": "#7FDBFF",
                        "fontFamily": "Arial",
                        "marginTop": "0",
                    },
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Label(
                                    "Select Store:",
                                    style={"color": "#7FDBFF", "marginRight": "10px"},
                                ),
                                dcc.Dropdown(
                                    id="store-id-dropdown",
                                    options=[{"label": "All Stores", "value": "All"}]
                                    + [
                                        {"label": str(name), "value": name}
                                        for name in fetch_store_names()
                                    ],
                                    value="All",
                                    style={
                                        "width": "300px",
                                        "display": "inline-block",
                                        "verticalAlign": "middle",
                                    },
                                ),
                            ],
                            style={"marginRight": "40px"},
                        ),
                        html.Div(
                            [
                                html.Label(
                                    "Select Date Range:",
                                    style={"color": "#7FDBFF", "marginRight": "10px"},
                                ),
                                dcc.DatePickerRange(
                                    id="date-range-picker",
                                    start_date_placeholder_text="Start Date",
                                    end_date_placeholder_text="End Date",
                                    start_date=datetime.date(2021, 9, 1),
                                    end_date=datetime.date.today(),
                                    style={
                                        "color": "#7FDBFF",
                                        "backgroundColor": "#222222",
                                        "border": "1px solid #333333",
                                        "borderRadius": "5px",
                                        "padding": "5px",
                                        "display": "inline-block",
                                        "verticalAlign": "middle",
                                    },
                                ),
                            ]
                        ),
                        html.Div(
                            [
                                html.Label(
                                    "Select Account Type:",
                                    style={"color": "#7FDBFF", "marginRight": "10px"},
                                ),
                                dcc.Dropdown(
                                    id="account-type-dropdown",
                                    options=[
                                        {"label": "All Accounts", "value": "All"},
                                        {"label": "Commercial", "value": "Commercial"},
                                        {"label": "Retail", "value": "Retail"},
                                    ],
                                    value="All",
                                    style={
                                        "width": "200px",
                                        "display": "inline-block",
                                        "verticalAlign": "middle",
                                    },
                                ),
                            ],
                            style={"marginLeft": "40px"},
                        ),
                    ],
                    style={
                        "display": "flex",
                        "justifyContent": "center",
                        "alignItems": "center",
                        "marginBottom": "20px",
                    },
                ),
                html.Div(
                    [
                        dcc.Link(
                            page["name"],
                            href=page["relative_path"],
                            style={
                                "color": "#7FDBFF",
                                "padding": "10px 20px",
                                "marginRight": "10px",
                                "textDecoration": "none",
                                "border": "1px solid #333333",
                                "borderRadius": "5px",
                                "backgroundColor": "#222222",
                            },
                        )
                        for page in dash.page_registry.values()
                    ],
                    style={
                        "display": "flex",
                        "justifyContent": "center",
                        "marginBottom": "10px",
                    },
                ),
            ],
        ),
        # Scrollable Content Sections
        html.Div(
            style={"padding": "220px 20px 20px 20px"}, children=[dash.page_container]
        ),
    ],
)

if __name__ == "__main__":
    app.run(debug=True)
