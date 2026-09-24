import gzip
import hashlib

import package_dataset
import make_sample
import serve
from data_factory import write_dataset


def test_make_sample_limits_rows_and_scrubs_card_data(tmp_path):
    source = write_dataset(tmp_path / "full")
    counts = make_sample.make_sample(source, tmp_path / "sample", fraction=0.5, max_rows=100, seed=1)
    import pandas as pd

    tx = pd.read_csv(tmp_path / "sample" / make_sample.TRANSACTIONS)
    labels = pd.read_csv(tmp_path / "sample" / make_sample.FRAUD_LABELS)
    cards = pd.read_csv(tmp_path / "sample" / "cards_data.csv")
    assert len(tx) == counts[make_sample.TRANSACTIONS] <= 100
    assert set(labels["id"]) <= set(tx["id"])
    assert not {"card_number", "cvv"} & set(cards.columns)


def test_make_sample_cli(tmp_path, capsys):
    source = write_dataset(tmp_path / "full")
    assert make_sample.main(["--source", str(source), "--output", str(tmp_path / "s"), "--fraction", "0.1"]) == 0
    assert "Sample written" in capsys.readouterr().out


def test_package_dataset_is_reproducible_and_verifiable(tmp_path):
    source = write_dataset(tmp_path / "full")
    manifest = tmp_path / "dataset.sha256"
    first = package_dataset.package(source, tmp_path / "dist", manifest)
    second = package_dataset.package(source, tmp_path / "dist2", tmp_path / "again.sha256")
    assert first == second  # fixed gzip mtime -> identical checksums
    for line in manifest.read_text().splitlines():
        digest, name = line.split("  ")
        path = tmp_path / "dist" / name if name.endswith(".gz") else source / name
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
    gz = tmp_path / "dist" / "train_fraud_labels.csv.gz"
    assert gzip.decompress(gz.read_bytes()) == (source / "train_fraud_labels.csv").read_bytes()


def test_package_dataset_cli(tmp_path, capsys):
    source = write_dataset(tmp_path / "full")
    args = ["--source", str(source), "--dist", str(tmp_path / "d"), "--manifest", str(tmp_path / "m.sha256")]
    assert package_dataset.main(args) == 0
    assert "Upload" in capsys.readouterr().out


def test_serve_starts_exporter_then_streamlit(monkeypatch):
    import streamlit.web.cli as stcli

    calls = []
    monkeypatch.setattr(serve.telemetry, "start_metrics_server", lambda: calls.append("metrics"))
    monkeypatch.setattr(stcli, "main", lambda: calls.append(list(__import__("sys").argv)) or 0)
    assert serve.main(["--server.port=8501"]) == 0
    assert calls[0] == "metrics"
    assert calls[1][:2] == ["streamlit", "run"] and calls[1][2].endswith("app.py")
    assert calls[1][3:] == ["--server.port=8501"]
