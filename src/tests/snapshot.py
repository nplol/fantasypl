"""
Snapshot helpers: normalize analyzer return values to JSON,
write/read snapshot files, and diff with deepdiff for readable failures.
"""
import json
import os
from typing import Any

from deepdiff import DeepDiff
from pydantic import BaseModel

SNAPSHOT_DIR = os.path.join(os.path.dirname(__file__), "snapshots")


def _normalize(obj: Any) -> Any:
    """Recursively turn Pydantic models / nested containers into JSON-safe data."""
    if isinstance(obj, BaseModel):
        return _normalize(obj.dict())
    if isinstance(obj, dict):
        return {k: _normalize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_normalize(x) for x in obj]
    if isinstance(obj, (set, frozenset)):
        # Sets have non-deterministic iteration order; sort for stable snapshots.
        return sorted(_normalize(x) for x in obj)
    if isinstance(obj, float):
        # Avoid 0.6666666666666666 vs 0.6666666666666667 noise across runs.
        return round(obj, 10)
    return obj


def snapshot_path(season: str, method_name: str) -> str:
    return os.path.join(SNAPSHOT_DIR, season, f"{method_name}.json")


def load_snapshot(season: str, method_name: str):
    path = snapshot_path(season, method_name)
    with open(path, "r") as f:
        return json.load(f)


def write_snapshot(season: str, method_name: str, data: Any) -> str:
    path = snapshot_path(season, method_name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        # default=str catches datetime; sort_keys keeps diffs stable.
        json.dump(_normalize(data), f, indent=2, sort_keys=True, default=str)
        f.write("\n")
    return path


def assert_matches_snapshot(season: str, method_name: str, actual: Any, *, update: bool):
    """
    If `update` is True, overwrite the snapshot.
    Otherwise compare; on mismatch raise with a deepdiff summary.
    """
    normalized = _normalize(actual)
    # Round-trip through JSON so comparison matches what's on disk
    # (tuples vs lists, datetime str, etc.).
    normalized = json.loads(json.dumps(normalized, sort_keys=True, default=str))

    if update:
        write_snapshot(season, method_name, normalized)
        return

    path = snapshot_path(season, method_name)
    if not os.path.exists(path):
        raise AssertionError(
            f"No snapshot for {season}/{method_name}. "
            f"Run with --update-snapshots to create it."
        )

    expected = load_snapshot(season, method_name)
    diff = DeepDiff(expected, normalized, ignore_order=False)
    if diff:
        raise AssertionError(
            f"Snapshot mismatch for {season}/{method_name}:\n{diff.pretty()}\n"
            f"If this change is intentional, run with --update-snapshots."
        )
