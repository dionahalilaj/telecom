from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppPaths:
    base_dir: Path
    data_dir: Path
    raw_data: Path
    enriched_parquet: Path
    enriched_csv: Path
    centers_file: Path
    meta_file: Path


def get_paths() -> AppPaths:
    # src/ -> project root
    base_dir = Path(__file__).resolve().parents[1]
    data_dir = base_dir / "data"
    data_dir.mkdir(exist_ok=True)

    return AppPaths(
        base_dir=base_dir,
        data_dir=data_dir,
        raw_data=data_dir / "telecom_original.csv",
        enriched_parquet=data_dir / "telecom_enriched.parquet",
        enriched_csv=data_dir / "telecom_enriched.csv",
        centers_file=data_dir / "dtw_cluster_centers.npy",
        meta_file=data_dir / "dtw_meta.json",
    )
