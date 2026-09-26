import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parent.parent
PIPELINE_DIR = Path(__file__).resolve().parent

BOX_OFFICE_CSV = ROOT_DIR / "data" / "bronze" / "box_office" / "revenues_per_day.csv"
MOVIES_INPUT_CSV = PIPELINE_DIR / "selected_movies.csv"
OMDB_BRONZE_DIR = ROOT_DIR / "data" / "bronze" / "omdb"
DUCKDB_PATH = ROOT_DIR / "data" / "warehouse.duckdb"

OMDB_API_KEY = os.getenv("OMDB_API_KEY")
OMDB_BASE_URL = "https://www.omdbapi.com/"

MOVIES_PER_YEAR = 95
YEARS_SELECTED = 10
