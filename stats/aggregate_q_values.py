#!/usr/bin/env python3
"""Aggregate Q_values_*.npy across experiment folders."""
from __future__ import annotations

import argparse
import json
from logging import config
import re
from pathlib import Path

import numpy as np

import configparser
import os   


config = configparser.ConfigParser()
config.read('config.ini')

experiment_name = config.get('training', 'experiment_name', fallback='default_experiment')
num_experiments = config.getint('training', 'experiments', fallback=1)
experiment_id = os.getenv("EXPERIMENT_ID", "").strip()

#experiment_folder = Path(f"exp_{experiment_name}_{experiment_id}")

def _extract_index(path: Path) -> int:
    match = re.search(r"Q_values_(\d+)\.npy$", path.name)
    return int(match.group(1)) if match else -1


def main() -> int:

    for step in num_experiments:
        experiment_folder = Path(f"exp_{experiment_name}_{step}")
        if experiment_id and experiment_folder.name != f"exp_{experiment_name}_{experiment_id}":
            continue

    # WE RESOLVE THIS LATER
    output_dir = Path(experiment_name +"aggregated_q_values")
    output_dir.mkdir(parents=True, exist_ok=True)

    summary: dict[str, list[float]] = {}

    for exp_file in experiment_folder:
        if not exp_file.is_dir():
            continue

        files = sorted(exp_file.glob("Q_values_*.npy"), key=_extract_index)
        if not files:
            print(f"Skipping {exp_file.name}: no Q_values_*.npy files found.")
            continue

        arrays = [np.load(path) for path in files]
        stacked = np.vstack(arrays)
        mean_values = stacked.mean(axis=0)

        summary[exp_file.name] = mean_values.tolist()
        np.save(output_dir / f"{exp_file.name}_Q_values_mean.npy", mean_values)

        print(f"{expfile.name}: mean shape={mean_values.shape}")

    summary_path = output_dir / "q_values_means.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"Wrote summary to {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
