# %%
import pandas as pd
df = pd.read_csv("revenues_per_day.csv")
print(df)

# %%
df.info()

# %%
print(df.isnull().sum())

# %%
print(df.nunique())

# %%
# Data quality checks (README section 4)
print("Duplicate id rows:", df["id"].duplicated().sum())
print("Negative revenue rows:", (df["revenue"] < 0).sum())
print("Negative theaters rows:", (df["theaters"] < 0).sum())
print("Distributor null rows:", df["distributor"].isna().sum())
print("Distributor placeholder '-' rows:", (df["distributor"] == "-").sum())

# %%
# Year coverage — supports the "10 most recent complete years" selection rule (README section 5)
year_coverage = df.copy()
year_coverage["date"] = pd.to_datetime(year_coverage["date"], format="mixed")
year_coverage["year"] = year_coverage["date"].dt.year
print(year_coverage.groupby("year")["date"].agg(min_date="min", max_date="max", rows="count"))

# %%
# analysis of one movie "I, Robot" to build KPIs framework

df["date"] = pd.to_datetime(df["date"], format="mixed")

i_robot = df[df["title"] == "I, Robot"].sort_values("date")
with pd.option_context("display.max_rows", None):
    print(i_robot)

# %%
# KPI framework derived from this example (README section 2)
opening_theaters = i_robot.iloc[0]["theaters"]
first_date = i_robot["date"].min()
total_gross = i_robot["revenue"].sum()
opening_week_gross = i_robot[i_robot["date"] < first_date + pd.Timedelta(days=7)]["revenue"].sum()
opening_week_per_theater = opening_week_gross / opening_theaters
legs_multiplier = total_gross / opening_week_gross
is_wide_release = opening_theaters >= 600

print("Opening theaters:", opening_theaters)
print("Opening week gross:", opening_week_gross)
print("Opening week per theater:", round(opening_week_per_theater, 2))
print("Total gross:", total_gross)
print("Legs multiplier:", round(legs_multiplier, 2))
print("Wide release (>= 600 theaters):", is_wide_release)

# %%
event = {
  "Title": "I, Robot",
  "Year": "2004",
  "Rated": "PG-13",
  "Released": "16 Jul 2004",
  "Runtime": "115 min",
  "Genre": "Action, Mystery, Sci-Fi",
  "Director": "Alex Proyas",
  "Writer": "Jeff Vintar, Akiva Goldsman, Isaac Asimov",
  "Actors": "Will Smith, Bridget Moynahan, Bruce Greenwood",
  "Plot": "In 2035, techno-phobic homicide detective Del Spooner of the Chicago PD heads the investigation of the apparent suicide of leading robotics scientist, Dr. Alfred Lanning. Unconvinced of the motive, Spooner's investigation into Lanning's death reveals a trail of secrets and agendas within the USR (United States Robotics) corporation and suspicions of murder. Little does he know that his investigation would lead to uncovering a larger threat to humanity.",
  "Language": "English",
  "Country": "United States, Germany",
  "Awards": "Nominated for 1 Oscar. 1 win & 15 nominations total",
  "Poster": "https://m.media-amazon.com/images/M/MV5BZDdhNTY3YTgtYmQwMC00MjM1LTgzYzMtMGM1N2E0NWM1NDlkXkEyXkFqcGc@._V1_SX300.jpg",
  "Ratings": [
    {
      "Source": "Internet Movie Database",
      "Value": "7.1/10"
    },
    {
      "Source": "Metacritic",
      "Value": "59/100"
    }
  ],
  "Metascore": "59",
  "imdbRating": "7.1",
  "imdbVotes": "611,841",
  "imdbID": "tt0343818",
  "Type": "movie",
  "DVD": "08 Jun 2004",
  "BoxOffice": "$144,801,023",
  "Production": "N/A",
  "Website": "N/A",
  "Response": "True"
}

print(event)

# %%
# Movie selection — top 95 movies by total gross per year, for the 10 most recent
# complete years in the CSV (README section 5). Movie identity = title + release
# year (year of that title's first revenue date).

movie_agg = df.copy()
movie_agg["release_year"] = movie_agg.groupby("title")["date"].transform("min").dt.year
movie_totals = (
    movie_agg.groupby(["title", "release_year"], as_index=False)["revenue"]
    .sum()
    .rename(columns={"revenue": "total_gross"})
)

# 2023 is partial in this export (through March), so it's not a complete year
complete_years = sorted(y for y in movie_totals["release_year"].unique() if y < 2023)
selected_years = complete_years[-10:]

selected_movies = (
    movie_totals[movie_totals["release_year"].isin(selected_years)]
    .sort_values(["release_year", "total_gross"], ascending=[True, False])
    .groupby("release_year")
    .head(95)
    .reset_index(drop=True)
)

print("Selected years:", selected_years)
print("Movies selected:", len(selected_movies))
print(selected_movies.groupby("release_year").size())

# %%
# Export the selected movie list — to extract from an API for assignment

selected_movies[["title", "release_year", "total_gross"]].to_csv(
    "selected_movies.csv", index=False
)
print(f"Exported {len(selected_movies)} movies to selected_movies.csv")
