"""Feast definitions for airalert.  Goes in: feature_repo/features.py"""
from datetime import timedelta
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import yaml
from feast import Entity, FeatureService, FeatureView, Field, FileSource, ValueType
from feast.types import Float32, Float64, Int64

# Set to False for an offline-only project (no online store). See Step 4, Option B.
USE_ONLINE_STORE = True

REPO = Path(__file__).resolve().parent          # .../feature_repo
DATA = REPO / "data"
NOT_FEATURES = {"station", "event_timestamp", "polluted_in_24h", "target"}


def _ttl_days() -> int:
    params = yaml.safe_load((REPO.parent / "params.yaml").read_text(encoding="utf-8"))
    return int(params["feast"]["ttl_days"])


def _feast_type(arrow_type: pa.DataType):
    if pa.types.is_floating(arrow_type):
        return Float32 if arrow_type.bit_width == 32 else Float64
    if pa.types.is_integer(arrow_type):
        return Int64
    raise ValueError(f"Unsupported column type for Feast: {arrow_type}")


def _schema(parquet_name: str):
    schema = pq.read_schema(str(DATA / parquet_name))
    return [
        Field(name=name, dtype=_feast_type(schema.field(name).type))
        for name in schema.names
        if name not in NOT_FEATURES and not name.startswith("__")
    ]


station = Entity(
    name="station",
    join_keys=["station"],
    value_type=ValueType.STRING,
    description="Air-quality monitoring station",
)

pollution_source = FileSource(
    name="station_pollution_source",
    path="data/station_pollution.parquet",
    timestamp_field="event_timestamp",
)
weather_source = FileSource(
    name="station_weather_source",
    path="data/station_weather.parquet",
    timestamp_field="event_timestamp",
)

TTL = timedelta(days=_ttl_days())

station_pollution = FeatureView(
    name="station_pollution",
    entities=[station],
    ttl=TTL,
    schema=_schema("station_pollution.parquet"),
    source=pollution_source,
    online=USE_ONLINE_STORE,
)
station_weather = FeatureView(
    name="station_weather",
    entities=[station],
    ttl=TTL,
    schema=_schema("station_weather.parquet"),
    source=weather_source,
    online=USE_ONLINE_STORE,
)

alert_model_v1 = FeatureService(
    name="alert_model_v1",
    features=[station_pollution, station_weather],
)
