import pandas as pd
import pytest

from model.CustomerSegmentation import CustomerSegmentation

SEGMENTS = {"Champions", "Loyal Customers", "Potential Loyalists", "At Risk", "Lost"}


@pytest.mark.parametrize("score, segment", [
    (12, "Champions"), (10, "Champions"), (9, "Loyal Customers"), (8, "Loyal Customers"),
    (7, "Potential Loyalists"), (6, "Potential Loyalists"), (5, "At Risk"), (4, "At Risk"),
    (3, "Lost"), (0, "Lost"), (-1, "Lost"),
])
def test_score_to_segment_thresholds(analysis, score, segment):
    assert analysis.segmentation.score_to_segment(score) == segment


def test_quantile_scores_are_inverted_for_recency():
    series = pd.Series([1, 2, 3, 4, 5, 6, 7, 8])
    low_is_good = CustomerSegmentation._score_quantile(series, ascending=True)
    high_is_good = CustomerSegmentation._score_quantile(series, ascending=False)
    assert low_is_good.iloc[0] == 4 and low_is_good.iloc[-1] == 1
    assert high_is_good.iloc[0] == 1 and high_is_good.iloc[-1] == 4


def test_quantile_score_falls_back_when_values_are_constant():
    scores = CustomerSegmentation._score_quantile(pd.Series([5, 5, 5, 5]), ascending=False)
    assert scores.between(1, 4).all()


def test_rfm_table(analysis):
    rfm = analysis.segmentation.rfm_
    assert rfm.index.is_unique
    assert (rfm["frequency"] > 0).all() and (rfm["recency"] >= 1).all()
    assert rfm["RFM_score"].between(3, 12).all()
    assert set(rfm["segment"]) <= SEGMENTS


def test_segment_profile_sorted_by_monetary(analysis):
    profile = analysis.segmentation.segment_profile()
    assert profile["avg_monetary"].is_monotonic_decreasing
    assert profile["num_customers"].sum() == len(analysis.segmentation.rfm_)


def test_segment_profile_fits_on_demand(analysis):
    fresh = CustomerSegmentation(analysis.master_df)
    assert set(fresh.segment_profile().index) <= SEGMENTS
