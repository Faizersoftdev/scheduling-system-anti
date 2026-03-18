"""
Configuration constants for the Scheduling Automation Program.
SLTCFPDI - Southern Luzon Technological College Foundation Pioduran Incorporated
"""
import os

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
DATABASE_PATH = os.path.join(DATA_DIR, "scheduling.db")
LOGO_PATH = os.path.join(ASSETS_DIR, "SLLOGO.png")

# School Info
SCHOOL_NAME = "SLTCFPDI"
SCHOOL_FULL_NAME = "Southern Luzon Technological College Foundation Pioduran Incorporated"
APP_TITLE = f"Scheduling Automation Program — {SCHOOL_NAME}"

# Window
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 800
WINDOW_MIN_WIDTH = 1024
WINDOW_MIN_HEIGHT = 700

# Design Colors (from Stitch designs)
COLOR_PRIMARY = "#1152d4"
COLOR_PRIMARY_DARK = "#0d3fa3"
COLOR_PRIMARY_LIGHT = "#e8eefb"
COLOR_BG_LIGHT = "#f6f6f8"
COLOR_BG_DARK = "#101622"
COLOR_WHITE = "#ffffff"
COLOR_TEXT_DARK = "#1e293b"  # slate-800
COLOR_TEXT_SECONDARY = "#64748b"  # slate-500
COLOR_BORDER = "#e2e8f0"  # slate-200
COLOR_SUCCESS = "#22c55e"
COLOR_DANGER = "#ef4444"
COLOR_WARNING = "#f59e0b"

# Scheduling Constants
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
DAY_ABBREVS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
START_HOUR = 8   # 8:00 AM
END_HOUR = 17    # 5:00 PM (last slot starts at 4 PM)
SLOT_DURATION = 1  # 1 hour per slot
