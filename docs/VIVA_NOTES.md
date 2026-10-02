# Viva notes (read these; add your own words)

## What each file does (say it in your own words)
| File | What it does |
|---|---|
| `params.yaml` | All settings in one place (threshold, windows, split date, model search size). |
| `dvc.yaml` | The pipeline: for each stage the command, inputs (deps), settings (params) and outputs (outs). |
| `dvc.lock` | Created by DVC: the exact hashes of inputs/outputs from the last run. |
| `data/raw.dvc` | Small pointer file for the raw data; the data itself lives in DVC's cache/remote, not in Git. |
| `src/common.py` | Shared paths, column lists and tiny helpers. |
| `src/prepare.py` | Reads 12 CSVs, makes every station's hourly timeline complete, builds the answer ("polluted in 24 h?") from the real readings, then fills short gaps in the inputs. |
| `src/build_features.py` | Rolling averages/maxima/changes per station and time-of-day/season features. Writes the Feast feature tables and the answer table. |
| `src/feast_apply.py` | Registers features in Feast and loads the latest values into the online store. |
| `src/build_training_set*.py` | Joins answers with features (plain pandas, or Feast point-in-time join). Same output either way. |
| `src/split.py` | Time-based split with a 24 h gap. |
| `src/train_fast.py` / `train_slow.py` | Logistic Regression / LightGBM with random search. |
| `src/evaluate.py` | Scores baselines and models on the held-out last year. |
| `src/cli.py` | Terminal commands: info, compare, backtest, predict, feast-demo. |

## DVC questions
- **Why DVC?** Git is bad at big data/model files. DVC versions them and rebuilds the pipeline reproducibly.
- **Git vs DVC?** Git stores code and small pointer files. DVC stores the large files in a cache/remote and knows the pipeline graph.
- **`dvc.yaml`, `params.yaml`, `dvc.lock`?** Pipeline definition / settings / hashes of the last run.
- **How does DVC decide what to rerun?** It hashes each stage's deps, params and command and compares with `dvc.lock`. A stage that differs (and everything after it) is stale.
- **Data changes?** The hash of `data/raw` changes, so every stage reruns. **A param changes?** Only stages that list that param, and what depends on them.
- **`dvc repro` / `status` / `dag`?** Rebuild what is stale / show what is stale / draw the stage graph.
- **`dvc push` / `pull`?** Upload / download the cached files to / from the remote. **`dvc checkout`?** Put the files back in the workspace to match the current Git commit.
- **Reproduce on another machine?** `git clone`, create venv, `pip install -r requirements.txt`, `dvc pull`, `dvc repro`.
- **Why are metrics files `cache: false`?** So Git tracks the small JSON files directly and `dvc metrics diff` can compare commits.

## Feast questions
- **Why a feature store?** One definition of the features for both training and serving, so they cannot drift apart.
- **Offline vs online store?** Offline = full history (training). Online = only the latest value per station (fast lookups for predictions). `materialize` copies offline → online.
- **Point-in-time join?** For each training row Feast returns the feature values as they were *at that hour*, never later ones, which prevents leakage.
- **Entity / FeatureView / FeatureService?** What features belong to (station) / a table of features with a timestamp / a named bundle used by training and serving.
- **Why explicit start/end in `materialize`?** The data is from 2013–2017; the "incremental" mode counts back from today.
- **Why can't the online store replay history?** It only keeps the latest value per station, so `backtest` uses the offline store/test file.

## Design questions
- **Why a time-based split and a 24 h gap?** Predicting the future must be tested on the future. The last training answers look 24 h ahead, so the gap stops them from overlapping the test period.
- **Why sort by time before cross-validation?** `TimeSeriesSplit` assumes oldest-to-newest rows; sorted by station it would split by station instead.
- **Why a complete hourly timeline and no row dropping before features?** "24 rows later" must mean "24 hours later", and rolling windows need unbroken hours.
- **Why is the answer built before filling gaps?** Filling would invent answers from made-up values.
- **Why two models?** Quick, explainable baseline vs stronger, tuned model; compare cost and quality.
- **Why no wind direction?** It is a text category and I kept the first version simple, but it matters for pollution transport (a limitation).
- **Why persistence baseline?** If a model can't beat "same as now", it adds nothing.

## Practice drills (do each twice)
1. `dvc dag`, explain each box. 2. Change one param, `dvc status`, predict, `dvc repro`. 3. `dvc params diff`, `dvc metrics diff`.
4. Delete `models/`, `dvc status`, `dvc checkout`. 5. Delete `.dvc/cache` and the data, `dvc pull`.
6. Clone to a new folder, `dvc pull`, `dvc repro` (nothing should rerun). 7. Check out an old tag, `dvc checkout`, show old metrics.
8. Edit one script, show only that stage is stale. 9. `dvc repro -f train_fast`, explain why it reran.
10. Explain why `data/raw/` is not in Git but `data/raw.dvc` is.
