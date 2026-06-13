#!/usr/bin/env python3
"""Summarize rmse_records.csv into Fig.6-style CSV tables."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from statistics import mean, pstdev


def summarize(records_csv: Path, out_csv: Path) -> None:
    rows = list(csv.DictReader(records_csv.open(encoding="utf-8")))
    grouped: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    for row in rows:
        key = (row["algorithm"], row["trajectory"], row["v_max"])
        grouped[key].append(float(row["rmse_m"]))

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", encoding="utf-8", newline="") as fp:
        writer = csv.writer(fp)
        writer.writerow(["algorithm", "trajectory", "v_max", "n_trials", "rmse_mean", "rmse_std"])
        for key in sorted(grouped.keys()):
            vals = grouped[key]
            writer.writerow([*key, len(vals), f"{mean(vals):.6f}", f"{pstdev(vals):.6f}" if len(vals) > 1 else "0"])
    print(f"[info] wrote summary: {out_csv}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--records",
        default=str(Path(__file__).resolve().parent.parent / "data" / "results" / "rmse_records.csv"),
    )
    parser.add_argument(
        "--output",
        default=str(Path(__file__).resolve().parent.parent / "data" / "results" / "fig6_summary.csv"),
    )
    args = parser.parse_args()
    records = Path(args.records)
    if not records.exists():
        raise SystemExit(f"records file not found: {records}")
    summarize(records, Path(args.output))


if __name__ == "__main__":
    main()
