"""Stage feast_apply.  Goes in: src/feast_apply.py

1. Register the entity, feature views and feature service in the Feast registry.
2. (Online store only) copy the latest value per station into the online store.
   materialize() gets explicit start/end dates because the data is old (2013-2017);
   materialize_incremental() would start from "now - TTL" and miss it.
"""
import sys
from datetime import timedelta
from pathlib import Path

import pandas as pd
from feast import FeatureStore

REPO = Path("feature_repo")
sys.path.insert(0, str(REPO.resolve()))
import features as F  # noqa: E402  (feature_repo/features.py)

store = FeatureStore(repo_path=str(REPO))
store.apply([F.station, F.station_pollution, F.station_weather, F.alert_model_v1])
print("registered: entity station, views station_pollution + station_weather, service alert_model_v1")

if F.USE_ONLINE_STORE:
    ts = pd.read_parquet(REPO / "data" / "station_pollution.parquet",
                         columns=["event_timestamp"])["event_timestamp"]
    start = ts.min().to_pydatetime()
    end = (ts.max() + timedelta(hours=1)).to_pydatetime()
    store.materialize(start_date=start, end_date=end)
    print(f"materialized online store: {start} -> {end}")
else:
    print("online store disabled (USE_ONLINE_STORE = False): nothing materialized")
