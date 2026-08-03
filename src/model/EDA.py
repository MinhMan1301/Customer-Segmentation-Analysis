class EDA:
    """Functions that directly answer the project's guiding questions."""

    def __init__(self, master_df):
        self.df = master_df

    def missing_value_report(self):
        """Check the missing-value ratio for each column."""
        na = self.df.isna().mean().sort_values(ascending=False)
        return na[na > 0].rename("pct_missing").to_frame()

    def spending_overview(self):
        """How much customers spend per transaction."""
        return self.df["amount"].describe()

    def spending_by_channel(self):
        """Which transaction channel customers prefer (Chip/Swipe/Online)."""
        return (
            self.df.groupby("use_chip")["amount"]
            .agg(["count", "mean", "sum"])
            .sort_values("count", ascending=False)
        )

    def spending_by_card_type(self):
        """Whether customers prefer paying upfront (Debit/Prepaid) or later (Credit)."""
        return (
            self.df.groupby("card_type")["amount"]
            .agg(["count", "mean", "sum"])
            .sort_values("count", ascending=False)
        )

    def yearly_trend(self):
        """How spending trends changed year over year (2010-2019)."""
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