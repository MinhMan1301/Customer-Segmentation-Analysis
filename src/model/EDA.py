class EDA:
    """Functions that directly answer the project's guiding questions."""

    def __init__(self, master_df):
        self.df = master_df

    def missing_value_report(self):
        na = self.df.isna().mean().sort_values(ascending=False)
        return na[na > 0].rename("pct_missing").to_frame()

    def spending_overview(self):
        return self.df["amount"].describe()

    def spending_by_channel(self):
        return (
            self.df.groupby("use_chip")["amount"]
            .agg(["count", "mean", "sum"])
            .sort_values("count", ascending=False)
        )

    def spending_by_card_type(self):
        return (
            self.df.groupby("card_type")["amount"]
            .agg(["count", "mean", "sum"])
            .sort_values("count", ascending=False)
        )

    def yearly_trend(self):
        tmp = self.df.copy()
        tmp["year"] = tmp["date"].dt.year
        return (
            tmp.groupby("year")["amount"]
            .agg(total_amount="sum", avg_amount="mean", num_transactions="count")
            .reset_index()
        )

    def top_mcc_categories(self, n=10):
        return (
            self.df.groupby("mcc_description")["amount"]
            .agg(["count", "sum"])
            .sort_values("count", ascending=False)
            .head(n)
        )