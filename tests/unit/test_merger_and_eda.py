import pandas as pd

from model.Merger import Merger
from model.TableCleaner import TableCleaner


def _cleaned(raw):
    return {
        "transactions": TableCleaner.clean_transactions(raw["transactions"]),
        "cards": TableCleaner.clean_cards(raw["cards"]),
        "users": TableCleaner.clean_users(raw["users"]),
        "mcc": TableCleaner.clean_mcc(raw["mcc"]),
        "fraud": TableCleaner.clean_fraud(raw["fraud"]),
    }


def test_merge_keeps_one_row_per_transaction(raw):
    master = Merger.merge_all(_cleaned(raw))
    assert len(master) == len(raw["transactions"])
    assert master["is_fraud"].dtype == bool
    assert master["mcc_description"].notna().all()
    assert master["card_type"].notna().all() and master["yearly_income"].notna().all()


def test_unlabelled_transactions_are_not_fraud(raw):
    raw["fraud"] = raw["fraud"].iloc[:0]
    master = Merger.merge_all(_cleaned(raw))
    assert not master["is_fraud"].any()


def test_eda_reports(analysis):
    eda = analysis.eda
    report = eda.missing_value_report()
    assert (report["pct_missing"] > 0).all()
    assert eda.spending_overview()["count"] == len(analysis.master_df)
    by_channel = eda.spending_by_channel()
    assert by_channel["count"].sum() == len(analysis.master_df)
    assert set(eda.spending_by_card_type().index) <= {"Debit", "Credit", "Debit (Prepaid)"}
    trend = eda.yearly_trend()
    assert list(trend.columns) == ["year", "total_amount", "avg_amount", "num_transactions"]
    assert trend["year"].is_monotonic_increasing
    assert len(eda.top_mcc_categories(n=3)) == 3


def test_yearly_trend_does_not_mutate_master(analysis):
    before = analysis.master_df.columns.tolist()
    analysis.eda.yearly_trend()
    assert analysis.master_df.columns.tolist() == before
    assert isinstance(analysis.master_df, pd.DataFrame)
