"""Stage build_training_set.  Goes in: src/build_training_set_feast.py

Point-in-time join through the Feast OFFLINE store:
for every (station, hour) row of entity_df, fetch the features as they were at that hour.
Output: data/processed/dataset.parquet  (must equal the plain-pandas dataset).
"""
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq
from feast import FeatureStore

ENTITY_PATH = "data/processed/entity_df.parquet"
OUT_PATH = Path("data/processed/dataset.parquet")

entity_df = pd.read_parquet(ENTITY_PATH)
store = FeatureStore(repo_path="feature_repo")
service = store.get_feature_service("alert_model_v1")

df = store.get_historical_features(entity_df=entity_df, features=service).to_df()

# --- make the Feast result look exactly like the pandas dataset ---------------
# 1. Feast returns timezone-aware (UTC) timestamps; entity_df is usually naive.
#    Mixing the two later breaks the date comparison in split.py.
if entity_df["event_timestamp"].dt.tz is None:
    df["event_timestamp"] = pd.to_datetime(df["event_timestamp"], utc=True).dt.tz_localize(None)

# 2. Give each feature column the dtype it has in the source parquet.
for name in ("station_pollution", "station_weather"):
    src_dtypes = pq.read_schema(f"feature_repo/data/{name}.parquet").empty_table().to_pandas().dtypes
    for col, dtype in src_dtypes.items():
        if col in df.columns and str(dtype).startswith("float") and df[col].dtype != dtype:
            df[col] = df[col].astype(dtype)

# 3. Fixed row order and column order: entity columns first, then features.
df = df.sort_values(["event_timestamp", "station"]).reset_index(drop=True)
ordered = list(entity_df.columns) + [c for c in df.columns if c not in entity_df.columns]
df = df[ordered]

# --- sanity checks ------------------------------------------------------------
assert len(df) == len(entity_df), f"row count changed: {len(entity_df)} -> {len(df)}"
feature_cols = [c for c in df.columns if c not in entity_df.columns]
all_null = [c for c in feature_cols if df[c].isna().all()]
if all_null:
    raise SystemExit(
        f"These features came back completely empty: {all_null}\n"
        "Most likely cause: feast.ttl_days in params.yaml is too short for 2013-2017 data (use 3650)."
    )

OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
df.to_parquet(OUT_PATH, index=False)
print(f"dataset: {df.shape[0]} rows x {df.shape[1]} columns -> {OUT_PATH}")
