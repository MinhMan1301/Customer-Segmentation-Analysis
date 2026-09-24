import pytest

from model.Visualizer import Visualizer

EXPECTED_CHARTS = {
    "missing_values_before", "missing_values", "amount_distribution", "spending_by_channel",
    "spending_by_card_type", "yearly_trend", "top_mcc_categories", "segment_distribution", "segment_monetary",
}


def test_generate_charts_writes_all_pngs(analysis):
    paths = analysis.generate_charts()
    assert {p.stem for p in paths} == EXPECTED_CHARTS
    assert all(p.exists() and p.stat().st_size > 1000 for p in paths)


def test_before_cleaning_plot_requires_raw_tables(analysis, tmp_path):
    with pytest.raises(ValueError, match="raw_tables"):
        Visualizer(analysis.master_df, output_dir=tmp_path).plot_missing_values_before()


def test_segment_plots_require_rfm(analysis, tmp_path):
    viz = Visualizer(analysis.master_df, output_dir=tmp_path)
    with pytest.raises(ValueError):
        viz.plot_segment_distribution()
    with pytest.raises(ValueError):
        viz.plot_segment_monetary()
    # Without optional inputs only the 6 core charts are produced.
    assert len(viz.generate_all(analysis.eda)) == 6
