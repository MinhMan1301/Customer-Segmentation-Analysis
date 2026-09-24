import os
from pathlib import Path

import pandas as pd

DATA_DIR_ENV = "DATA_DIR"
DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent / "data"

FILE_NAMES = {
    "transactions": "transactions_data_25pc.csv",
    "cards": "cards_data.csv",
    "users": "users_data.csv",
    "mcc": "mcc_codes.csv",
    "fraud": "train_fraud_labels.csv",
}


class DataLoader:
    """Responsible for locating and reading the 5 project CSV files.

    The data directory is resolved in this order:
    1. the ``data_dir`` argument,
    2. the ``DATA_DIR`` environment variable (used by Docker / Jenkins),
    3. ``src/data`` next to the source code (local development).
    """

    def __init__(self, data_dir=None):
        if data_dir is None:
            data_dir = os.environ.get(DATA_DIR_ENV) or DEFAULT_DATA_DIR
        self.data_dir = Path(data_dir)

    def _read(self, filename):
        path = self.data_dir / filename
        if not path.exists():
            raise FileNotFoundError(
                f"File '{filename}' not found at '{path}'. "
                f"Check the path, set {DATA_DIR_ENV}, or pass a data_dir when creating DataLoader."
            )
        return pd.read_csv(path)

    def missing_files(self):
        """Return the expected file names that are not present in data_dir."""
        return [name for name in FILE_NAMES.values() if not (self.data_dir / name).exists()]

    def load_all(self):
        return {key: self._read(filename) for key, filename in FILE_NAMES.items()}
