import duckdb

from bronze_pipeline.config import DUCKDB_PATH

if __name__ == "__main__":
    con = duckdb.connect(str(DUCKDB_PATH))
    con.execute("CALL start_ui()")
    input("Press Enter to close...")