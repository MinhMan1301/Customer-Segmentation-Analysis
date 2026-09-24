import pytest

pytestmark = pytest.mark.integration


def test_full_pipeline_on_synthetic_data(analysis):
    df = analysis.master_df
    assert len(df) > 0
    assert {"amount", "date", "client_id", "card_type", "mcc_description", "is_fraud"} <= set(df.columns)
    assert not {"card_number", "cvv"} & set(df.columns)
    assert df["amount"].notna().all()
    assert analysis.segmentation.rfm_["segment"].nunique() >= 3


def test_print_summary_covers_all_questions(analysis, capsys):
    analysis.print_summary()
    out = capsys.readouterr().out
    for heading in ("MISSING VALUE REPORT", "SPENDING OVERVIEW", "TRANSACTION CHANNEL", "CARD TYPE",
                    "YEARLY TREND", "MERCHANT CATEGORIES", "CUSTOMER SEGMENT PROFILE"):
        assert heading in out


def test_lazy_entry_points_run_the_pipeline(data_dir, tmp_path):
    from model.AttitudeAnalysis import AttitudeAnalysis

    lazy = AttitudeAnalysis(data_dir=data_dir, chart_dir=str(tmp_path))
    assert len(lazy.generate_charts()) == 9
    assert lazy.master_df is not None
