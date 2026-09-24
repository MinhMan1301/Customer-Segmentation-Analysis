"""Synthetic raw tables that mimic the formats of the project's five CSV files.

The real transaction and fraud-label files are too large for Git, so unit and
integration tests never depend on them. Instead we generate a small, seeded
dataset with the same columns and the same "messy" formats (``$`` money
strings, ``YES``/``NO`` flags, missing merchant fields for online payments...).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

FILE_NAMES = {
    "transactions": "transactions_data_25pc.csv",
    "cards": "cards_data.csv",
    "users": "users_data.csv",
    "mcc": "mcc_codes.csv",
    "fraud": "train_fraud_labels.csv",
}

MCC_CATEGORIES = {
    5411: "Grocery Stores, Supermarkets",
    5812: "Eating Places and Restaurants",
    5541: "Service Stations",
    4829: "Money Transfer",
    5300: "Wholesale Clubs",
}
CHANNELS = ["Chip Transaction", "Swipe Transaction", "Online Transaction"]


def _money(values):
    return [f"${int(v)}" for v in values]


def make_raw_tables(n_clients: int = 30, seed: int = 7) -> dict[str, pd.DataFrame]:
    """Return the five raw tables, keyed like ``DataLoader.load_all()``."""
    rng = np.random.default_rng(seed)
    client_ids = np.arange(1000, 1000 + n_clients)

    users = pd.DataFrame({
        "id": client_ids,
        "current_age": rng.integers(18, 85, n_clients),
        "retirement_age": rng.integers(60, 70, n_clients),
        "birth_year": 2019 - rng.integers(18, 85, n_clients),
        "birth_month": rng.integers(1, 13, n_clients),
        "gender": rng.choice(["Female", "Male"], n_clients),
        "address": [f"{i} Test Street" for i in range(n_clients)],
        "latitude": rng.uniform(25, 48, n_clients).round(2),
        "longitude": rng.uniform(-122, -70, n_clients).round(2),
        "per_capita_income": _money(rng.integers(15_000, 60_000, n_clients)),
        "yearly_income": _money(rng.integers(20_000, 150_000, n_clients)),
        "total_debt": _money(rng.integers(0, 250_000, n_clients)),
        "credit_score": rng.integers(480, 850, n_clients),
        "num_credit_cards": rng.integers(1, 8, n_clients),
    })

    card_rows, card_id = [], 5000
    for cid in client_ids:
        for _ in range(int(rng.integers(1, 3))):
            card_rows.append({
                "id": card_id,
                "client_id": int(cid),
                "card_brand": str(rng.choice(["Visa", "Mastercard", "Amex", "Discover"])),
                "card_type": str(rng.choice(["Debit", "Credit", "Debit (Prepaid)"])),
                "card_number": int(rng.integers(4_000_000_000_000_000, 4_999_999_999_999_999)),
                "expires": f"{int(rng.integers(1, 13)):02d}/20{int(rng.integers(20, 30))}",
                "cvv": int(rng.integers(100, 1000)),
                "has_chip": str(rng.choice(["YES", "NO"])),
                "num_cards_issued": int(rng.integers(1, 3)),
                "credit_limit": f"${int(rng.integers(500, 30_000))}",
                "acct_open_date": f"{int(rng.integers(1, 13)):02d}/20{int(rng.integers(0, 19)):02d}",
                "year_pin_last_changed": int(rng.integers(2005, 2020)),
                "card_on_dark_web": "No",
            })
            card_id += 1
    cards = pd.DataFrame(card_rows)

    # Clients get different activity levels and "last seen" dates so that the
    # RFM quartiles (and therefore all five segments) are meaningful.
    tx_rows, tx_id = [], 7_000_000
    start = pd.Timestamp("2012-01-01")
    span_days = (pd.Timestamp("2019-10-31") - start).days
    for cid in client_ids:
        client_cards = cards.loc[cards["client_id"] == cid, "id"].to_numpy()
        last_active = span_days - int(rng.integers(0, 900))
        for _ in range(int(rng.integers(3, 40))):
            ts = start + pd.Timedelta(days=int(rng.integers(0, last_active)),
                                      minutes=int(rng.integers(0, 1440)))
            channel = str(rng.choice(CHANNELS, p=[0.55, 0.30, 0.15]))
            online = channel == "Online Transaction"
            amount = round(float(rng.gamma(2.0, 30.0)), 2)
            if rng.random() < 0.05:  # refunds are negative amounts
                amount = -amount
            tx_rows.append({
                "id": tx_id,
                "date": ts.strftime("%Y-%m-%d %H:%M:%S"),
                "client_id": int(cid),
                "card_id": int(rng.choice(client_cards)),
                "amount": f"${amount:.2f}",
                "use_chip": channel,
                "merchant_id": int(rng.integers(10_000, 99_999)),
                "merchant_city": "ONLINE" if online else str(rng.choice(["Austin", "Denver", "Miami"])),
                "merchant_state": np.nan if online else str(rng.choice(["TX", "CO", "FL"])),
                "zip": np.nan if online else float(rng.integers(10_000, 99_999)),
                "mcc": int(rng.choice(list(MCC_CATEGORIES))),
                "errors": "Insufficient Balance" if rng.random() < 0.03 else np.nan,
            })
            tx_id += 1
    transactions = pd.DataFrame(tx_rows)

    mcc = pd.DataFrame({
        "mcc_code": list(MCC_CATEGORIES),
        "merchant_category": list(MCC_CATEGORIES.values()),
    })

    labelled_ids = transactions["id"].sample(frac=0.8, random_state=seed).to_numpy()
    fraud = pd.DataFrame({
        "id": labelled_ids,
        "label": np.where(rng.random(len(labelled_ids)) < 0.03, "Yes", "No"),
    })

    return {"transactions": transactions, "cards": cards, "users": users, "mcc": mcc, "fraud": fraud}


def write_dataset(directory, tables: dict[str, pd.DataFrame] | None = None) -> Path:
    """Write the raw tables as CSV files with the names DataLoader expects."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    tables = tables if tables is not None else make_raw_tables()
    for key, file_name in FILE_NAMES.items():
        tables[key].to_csv(directory / file_name, index=False)
    return directory
