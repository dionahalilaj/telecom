import json
from typing import Optional, Tuple, Dict, Any

import numpy as np
import pandas as pd

from .config import AppPaths


def load_raw(paths: AppPaths) -> pd.DataFrame:
    df = pd.read_csv(paths.raw_data)
    df["date"] = pd.to_datetime(df["date"])
    return df


def save_enriched(df: pd.DataFrame, paths: AppPaths) -> Tuple[str, str]:
    #Save enriched dataset. Tries parquet first, falls back to CSV.
    try:
        df.to_parquet(paths.enriched_parquet, index=False)
        return "parquet", str(paths.enriched_parquet)
    except Exception:
        df.to_csv(paths.enriched_csv, index=False)
        return "csv", str(paths.enriched_csv)


def load_enriched(paths: AppPaths) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    if paths.enriched_parquet.exists():
        df = pd.read_parquet(paths.enriched_parquet)
        return df, "parquet"
    if paths.enriched_csv.exists():
        df = pd.read_csv(paths.enriched_csv)
        return df, "csv"
    return None, None


def save_centers(centers: np.ndarray, k: int, paths: AppPaths) -> None:
    np.save(paths.centers_file, centers)
    paths.meta_file.write_text(json.dumps({"k": int(k)}))


def load_centers(paths: AppPaths) -> Optional[np.ndarray]:
    if not paths.centers_file.exists():
        return None
    return np.load(paths.centers_file, allow_pickle=False)


def load_meta(paths: AppPaths) -> Optional[Dict[str, Any]]:
    if not paths.meta_file.exists():
        return None
    try:
        return json.loads(paths.meta_file.read_text())
    except Exception:
        return None


def reset_artifacts(paths: AppPaths) -> None:
    for p in [
        paths.enriched_parquet,
        paths.enriched_csv,
        paths.centers_file,
        paths.meta_file,
    ]:
        if p.exists():
            p.unlink()
