"""Data contract for the committed sample in src/data/sample/.

The sample is baked into the Docker image and used by staging, so a broken or
missing sample must fail CI (REQUIRE_SAMPLE_DATA=1 in ci/test.sh).
"""
import os
from pathlib import Path

import pandas as pd
import pytest

from model.AttitudeAnalysis import AttitudeAnalysis

pytestmark = pytest.mark.integration

SAMPLE_DIR = Path(__file__).resolve().parents[2] / "src" / "data" / "sample"
REQUIRED_COLUMNS = {
    "transactions_data_25pc.csv": {"id", "date", "client_id", "card_id", "amount", "use_chip", "mcc"},
    "cards_data.csv": {"id", "client_id", "card_brand", "card_type", "has_chip", "credit_limit"},
    "users_data.csv": {"id", "current_age", "yearly_income", "total_debt", "credit_score"},
    "mcc_codes.csv": {"mcc_code", "merchant_category"},
    "train_fraud_labels.csv": {"id", "label"},
}


@pytest.fixture(scope="module")
def sample_dir():
    if not SAMPLE_DIR.exists():
        if os.getenv("REQUIRE_SAMPLE_DATA") == "1":
            pytest.fail(f"{SAMPLE_DIR} is missing - run scripts/make_sample.py and commit it")
        pytest.skip("sample dataset not generated yet")
    return SAMPLE_DIR


@pytest.mark.parametrize("file_name, columns", REQUIRED_COLUMNS.items())
def test_sample_schema(sample_dir, file_name, columns):
    header = set(pd.read_csv(sample_dir / file_name, nrows=0).columns)
    assert columns <= header


def test_sample_contains_no_card_secrets(sample_dir):
    header = set(pd.read_csv(sample_dir / "cards_data.csv", nrows=0).columns)
    assert not {"card_number", "cvv"} & header


def test_sample_runs_through_pipeline(sample_dir, tmp_path):
    analyzer = AttitudeAnalysis(data_dir=sample_dir, chart_dir=str(tmp_path))
    df = analyzer.run()
    assert len(df) == len(pd.read_csv(sample_dir / "transactions_data_25pc.csv", usecols=["id"]))
    assert df["mcc_description"].notna().mean() > 0.99
    assert df["is_fraud"].mean() < 0.05
    assert analyzer.segmentation.rfm_["segment"].nunique() >= 4
