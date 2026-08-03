import pandas as pd


class CustomerSegmentation:
    SEGMENT_MAP_THRESHOLDS = [
        (10, "Champions"),
        (8, "Loyal Customers"),
        (6, "Potential Loyalists"),
        (4, "At Risk"),
        (0, "Lost"),
    ]

    def __init__(self, master_df):
        self.df = master_df
        self.rfm_ = None

    def build_rfm(self):
        snapshot_date = self.df["date"].max() + pd.Timedelta(days=1)

        rfm = self.df.groupby("client_id").agg(
            recency=("date", lambda s: (snapshot_date - s.max()).days),
            frequency=("id", "count"),
            monetary=("amount", "sum"),
            avg_transaction=("amount", "mean"),
        )

        demo_cols = ["current_age", "yearly_income", "credit_score", "total_debt"]
        demo = self.df.groupby("client_id")[demo_cols].first()
        rfm = rfm.join(demo).dropna()

        self.rfm_ = rfm
        return rfm

    @staticmethod
    def _score_quantile(series, ascending):
        try:
            scores = pd.qcut(series, 4, labels=False, duplicates="drop") + 1
        except ValueError:
            return pd.Series(2, index=series.index)

        if ascending:
            max_score = scores.max()
            scores = max_score + 1 - scores
        return scores

    def score_to_segment(self, score):
        for threshold, label in self.SEGMENT_MAP_THRESHOLDS:
            if score >= threshold:
                return label
        return "Lost"

    def fit_segments(self):
        if self.rfm_ is None:
            self.build_rfm()

        rfm = self.rfm_.copy()
        rfm["R_score"] = self._score_quantile(rfm["recency"], ascending=True)
        rfm["F_score"] = self._score_quantile(rfm["frequency"], ascending=False)
        rfm["M_score"] = self._score_quantile(rfm["monetary"], ascending=False)
        rfm["RFM_score"] = rfm["R_score"] + rfm["F_score"] + rfm["M_score"]
        rfm["segment"] = rfm["RFM_score"].apply(self.score_to_segment)

        self.rfm_ = rfm
        return rfm

    def segment_profile(self):
        if self.rfm_ is None or "segment" not in self.rfm_.columns:
            self.fit_segments()

        profile = self.rfm_.groupby("segment").agg(
            num_customers=("recency", "count"),
            avg_recency=("recency", "mean"),
            avg_frequency=("frequency", "mean"),
            avg_monetary=("monetary", "mean"),
            avg_age=("current_age", "mean"),
            avg_income=("yearly_income", "mean"),
            avg_credit_score=("credit_score", "mean"),
        ).round(1)

        return profile.sort_values("avg_monetary", ascending=False)