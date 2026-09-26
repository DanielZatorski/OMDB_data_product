import pandas as pd

from pipeline.config import BOX_OFFICE_CSV


def extract() -> pd.DataFrame:
    """Read the full box office CSV (README section 5, pipeline step 1)."""
    df = pd.read_csv(BOX_OFFICE_CSV)
    df["date"] = pd.to_datetime(df["date"], format="mixed")
    return df
