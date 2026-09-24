"""Create the small, committed sample dataset used by CI and staging.

The full transaction and fraud-label files are too large for Git. This script
draws a reproducible random sample of transactions (chunked, so it never
loads the whole file into memory), keeps only the fraud labels of sampled
transactions, and copies the small reference tables. Card numbers and CVVs
are removed from the sample (data minimisation).

Usage:  python scripts/make_sample.py [--fraction 0.02] [--max-rows 80000]
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "src" / "data"
DEFAULT_OUTPUT = DEFAULT_SOURCE / "sample"
TRANSACTIONS = "transactions_data_25pc.csv"
FRAUD_LABELS = "train_fraud_labels.csv"
SMALL_TABLES = ("cards_data.csv", "users_data.csv", "mcc_codes.csv")
SENSITIVE_CARD_COLUMNS = ["card_number", "cvv"]


def sample_transactions(path: Path, fraction: float, max_rows: int, seed: int,
                        chunksize: int = 250_000) -> pd.DataFrame:
    parts = [chunk.sample(frac=fraction, random_state=seed + i)
             for i, chunk in enumerate(pd.read_csv(path, chunksize=chunksize))]
    sample = pd.concat(parts, ignore_index=True)
    if len(sample) > max_rows:
        sample = sample.sample(n=max_rows, random_state=seed)
    return sample.sort_values("id").reset_index(drop=True)


def filter_labels(path: Path, ids, chunksize: int = 500_000) -> pd.DataFrame:
    wanted = set(ids)
    parts = [chunk[chunk["id"].isin(wanted)] for chunk in pd.read_csv(path, chunksize=chunksize)]
    return pd.concat(parts, ignore_index=True)


def make_sample(source: Path, output: Path, fraction: float = 0.02,
                max_rows: int = 80_000, seed: int = 42) -> dict[str, int]:
    output.mkdir(parents=True, exist_ok=True)
    transactions = sample_transactions(source / TRANSACTIONS, fraction, max_rows, seed)
    labels = filter_labels(source / FRAUD_LABELS, transactions["id"])
    transactions.to_csv(output / TRANSACTIONS, index=False)
    labels.to_csv(output / FRAUD_LABELS, index=False)

    counts = {TRANSACTIONS: len(transactions), FRAUD_LABELS: len(labels)}
    for name in SMALL_TABLES:
        table = pd.read_csv(source / name)
        if name == "cards_data.csv":
            table = table.drop(columns=SENSITIVE_CARD_COLUMNS, errors="ignore")
        table.to_csv(output / name, index=False)
        counts[name] = len(table)
    return counts


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--fraction", type=float, default=0.02)
    parser.add_argument("--max-rows", type=int, default=80_000)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    counts = make_sample(args.source, args.output, args.fraction, args.max_rows, args.seed)
    for name, rows in counts.items():
        size_mb = (args.output / name).stat().st_size / 1_048_576
        print(f"{name:<30} {rows:>10,} rows {size_mb:>8.2f} MB")
    print(f"Sample written to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
