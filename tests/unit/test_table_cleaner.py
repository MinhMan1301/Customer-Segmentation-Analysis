import numpy as np
import pandas as pd
import pytest

from model.TableCleaner import TableCleaner, clean_money_column, fillna_with_median, fillna_with_mode, to_id_string


@pytest.mark.parametrize("raw, expected", [
    ("$1,234.50", 1234.5),
    ("$(77.00)", -77.0),
    ("-$5.25", -5.25),
    ("$0", 0.0),
])
def test_clean_money_column_parses_formats(raw, expected):
    assert clean_money_column(pd.Series([raw])).iloc[0] == pytest.approx(expected)


def test_clean_money_column_invalid_becomes_nan():
    assert np.isnan(clean_money_column(pd.Series(["not money"])).iloc[0])


def test_to_id_string_drops_float_suffix_and_keeps_missing():
    result = to_id_string(pd.Series([5411.0, np.nan, 42.0]))
    assert result.iloc[0] == "5411" and result.iloc[2] == "42"
    assert pd.isna(result.iloc[1])


def test_to_id_string_keeps_non_integral_values():
    assert to_id_string(pd.Series([1.5])).iloc[0] == "1.5"


def test_fill_helpers_skip_missing_columns():
    df = pd.DataFrame({"a": [1.0, np.nan, 3.0], "b": ["x", None, "x"]})
    df = fillna_with_median(fillna_with_mode(df, ["b", "missing"]), ["a", "missing"])
    assert df["a"].tolist() == [1.0, 2.0, 3.0]
    assert df["b"].tolist() == ["x", "x", "x"]


def test_clean_transactions(raw):
    raw["transactions"].loc[0, "amount"] = None
    tx = TableCleaner.clean_transactions(raw["transactions"])
    assert pd.api.types.is_float_dtype(tx["amount"]) and tx["amount"].notna().all()
    assert pd.api.types.is_datetime64_any_dtype(tx["date"])
    assert tx["merchant_state"].notna().all()
    assert set(tx["errors"]) >= {"No Error"}
    assert tx["is_error"].dtype == bool
    assert tx["mcc"].str.fullmatch(r"\d+").all()


def test_clean_transactions_mcc_with_missing_values_still_matches(raw):
    """Regression: float MCC codes used to become '5411.0' and break the merge."""
    tx = raw["transactions"]
    tx["mcc"] = tx["mcc"].astype(float)
    tx.loc[0, "mcc"] = np.nan
    cleaned = TableCleaner.clean_transactions(tx)
    assert not cleaned["mcc"].str.endswith(".0").any()


def test_clean_cards_removes_card_number_and_cvv(raw):
    cards = TableCleaner.clean_cards(raw["cards"])
    assert "card_number" not in cards.columns and "cvv" not in cards.columns
    assert "card_id" in cards.columns
    assert cards["has_chip"].dtype == bool
    assert pd.api.types.is_numeric_dtype(cards["credit_limit"])


def test_clean_users_fills_num_credit_cards(raw):
    """Regression: the column is 'num_credit_cards' (it was misspelled before)."""
    raw["users"].loc[0, "num_credit_cards"] = np.nan
    users = TableCleaner.clean_users(raw["users"])
    assert users["num_credit_cards"].notna().all()
    assert "client_id" in users.columns
    assert pd.api.types.is_numeric_dtype(users["yearly_income"])


def test_clean_mcc_and_fraud(raw):
    mcc = TableCleaner.clean_mcc(raw["mcc"])
    assert list(mcc.columns) == ["mcc", "mcc_description"]
    fraud = TableCleaner.clean_fraud(raw["fraud"])
    assert fraud["is_fraud"].dtype == bool
    assert fraud["is_fraud"].sum() == (raw["fraud"]["label"] == "Yes").sum()
