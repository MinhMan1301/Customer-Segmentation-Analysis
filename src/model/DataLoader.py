from pathlib import Path
import pandas as pd


class DataLoader:
    """Responsible for locating and reading the 5 project CSV files."""

    def __init__(self, data_dir=None):
        if data_dir is None:
            # __file__ lives in model/, data lives in data/ (sibling of model/)
            data_dir = Path(__file__).resolve().parent.parent / "data"
        self.data_dir = Path(data_dir)

    def _read(self, filename):
        path = self.data_dir / filename
        if not path.exists():
            raise FileNotFoundError(
                f"File '{filename}' not found at '{path}'. "
                f"Check the path or pass a data_dir when creating DataLoader."
            )
        return pd.read_csv(path)

    def load_all(self):
        return {
            "transactions": self._read("transactions_data_25pc.csv"),
            "cards": self._read("cards_data.csv"),
            "users": self._read("users_data.csv"),
            "mcc": self._read("mcc_codes.csv"),
            "fraud": self._read("train_fraud_labels.csv"),
        }