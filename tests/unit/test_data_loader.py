from pathlib import Path

import pytest

from model.DataLoader import DataLoader


def test_explicit_dir_wins_over_env(data_dir, monkeypatch, tmp_path):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    assert DataLoader(data_dir).data_dir == Path(data_dir)


def test_env_dir_is_used(data_dir, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(data_dir))
    tables = DataLoader().load_all()
    assert set(tables) == {"transactions", "cards", "users", "mcc", "fraud"}
    assert all(len(df) > 0 for df in tables.values())


def test_default_dir_is_src_data(monkeypatch):
    monkeypatch.delenv("DATA_DIR", raising=False)
    assert DataLoader().data_dir.parts[-2:] == ("src", "data")


def test_missing_file_has_helpful_message(tmp_path):
    with pytest.raises(FileNotFoundError, match="transactions_data_25pc.csv"):
        DataLoader(tmp_path).load_all()
