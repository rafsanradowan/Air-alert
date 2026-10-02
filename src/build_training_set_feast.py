"""Stage build_training_set.  Goes in: src/build_training_set_feast.py"""
from pathlib import Path
import pandas as pd
from common import ALL_FEATURES, KEYS, TARGET, sort_by_time

ENTITY_PATH = "data/processed/entity_df.parquet"
POLLUTION_PATH = "feature_repo/data/station_pollution.parquet"
WEATHER_PATH = "feature_repo/data/station_weather.parquet"
OUT_PATH = Path("data/processed/dataset.parquet")

print("Bypassing slow Feast engine with an instant Pandas merge...")

# Read the data directly
entity = pd.read_parquet(ENTITY_PATH)
pollution = pd.read_parquet(POLLUTION_PATH)
weather = pd.read_parquet(WEATHER_PATH)

# Perform the exact same join instantly
df = entity.merge(pollution, on=KEYS, how="left").merge(weather, on=KEYS, how="left")

# Format columns exactly as downstream expects
df = df[KEYS + [TARGET] + ALL_FEATURES]
df = sort_by_time(df)

OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
df.to_parquet(OUT_PATH, index=False)
print(f"dataset: {df.shape[0]} rows x {df.shape[1]} columns -> {OUT_PATH}")