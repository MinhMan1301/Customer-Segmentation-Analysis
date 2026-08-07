from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style="whitegrid")


class Visualizer:
    def __init__(self, master_df, rfm_df=None, output_dir="charts", raw_tables=None):
        self.df = master_df
        self.rfm_df = rfm_df
        self.raw_tables = raw_tables
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _save(self, fig, name):
        path = self.output_dir / f"{name}.png"
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return path

    def plot_missing_values(self):
        na = self.df.isna().mean().sort_values(ascending=False)
        na = na[na > 0]
        fig, ax = plt.subplots(figsize=(8, 5))
        if len(na) > 0:
            sns.barplot(x=na.values, y=na.index, ax=ax, color="#4C72B0")
        ax.set_xlabel("Missing ratio")
        ax.set_title("Missing value ratio by column (after cleaning)")
        return self._save(fig, "missing_values")

    def plot_missing_values_before(self):
        if not self.raw_tables:
            raise ValueError(
                "raw_tables not provided. Pass raw_tables=... to Visualizer "
                "to plot before-cleaning missing values."
            )
        na = pd.concat({name: df.isna().mean() for name, df in self.raw_tables.items()})
        na = na[na > 0].sort_values(ascending=False)
        fig, ax = plt.subplots(figsize=(8, 5))
        if len(na) > 0:
            labels = [f"{table}.{col}" for table, col in na.index]
            sns.barplot(x=na.values, y=labels, ax=ax, color="#DD8452")
        ax.set_xlabel("Missing ratio")
        ax.set_title("Missing value ratio by column (before cleaning)")
        return self._save(fig, "missing_values_before")

    def plot_amount_distribution(self):
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.histplot(self.df["amount"], bins=50, kde=True, ax=ax, color="#4C72B0")
        ax.set_title("Transaction amount distribution")
        ax.set_xlabel("Amount ($)")
        return self._save(fig, "amount_distribution")

    def plot_spending_by_channel(self):
        fig, ax = plt.subplots(figsize=(7, 5))
        sns.boxplot(data=self.df, x="use_chip", y="amount", ax=ax)
        ax.set_title("Spending by transaction channel")
        ax.set_xlabel("")
        return self._save(fig, "spending_by_channel")

    def plot_spending_by_card_type(self):
        fig, ax = plt.subplots(figsize=(7, 5))
        sns.boxplot(data=self.df, x="card_type", y="amount", ax=ax)
        ax.set_title("Spending by card type (Debit/Credit)")
        ax.set_xlabel("")
        return self._save(fig, "spending_by_card_type")

    def plot_yearly_trend(self, eda_yearly_df):
        data = eda_yearly_df[eda_yearly_df["year"] <= 2018]

        fig, ax = plt.subplots(figsize=(9, 5))
        sns.lineplot(data=data, x="year", y="total_amount", marker="o", ax=ax)
        ax.set_title("Total transaction amount trend by year (2010-2018)")
        ax.set_xlabel("Year")
        ax.set_ylabel("Total amount ($)")
        return self._save(fig, "yearly_trend")

    def plot_top_mcc(self, eda_mcc_df):
        fig, ax = plt.subplots(figsize=(8, 6))
        data = eda_mcc_df.reset_index()
        sns.barplot(data=data, x="count", y="mcc_description", ax=ax, color="#55A868")
        ax.set_title("Top merchant categories (MCC) by transaction count")
        ax.set_xlabel("Number of transactions")
        ax.set_ylabel("")
        return self._save(fig, "top_mcc_categories")

    def plot_segment_distribution(self):
        if self.rfm_df is None or "segment" not in self.rfm_df.columns:
            raise ValueError("rfm_df with a 'segment' column is missing. Run CustomerSegmentation first.")
        fig, ax = plt.subplots(figsize=(7, 5))
        order = self.rfm_df["segment"].value_counts().index
        sns.countplot(data=self.rfm_df, y="segment", order=order, ax=ax, color="#C44E52")
        ax.set_title("Number of customers per segment")
        ax.set_xlabel("Number of customers")
        ax.set_ylabel("")
        return self._save(fig, "segment_distribution")

    def plot_segment_monetary(self):
        if self.rfm_df is None or "segment" not in self.rfm_df.columns:
            raise ValueError("rfm_df with a 'segment' column is missing. Run CustomerSegmentation first.")
        fig, ax = plt.subplots(figsize=(7, 5))
        sns.boxplot(data=self.rfm_df, x="segment", y="monetary", ax=ax)
        ax.set_title("Total spend by segment")
        ax.set_xlabel("")
        ax.tick_params(axis="x", rotation=30)
        return self._save(fig, "segment_monetary")

    def generate_all(self, eda):
        paths = []
        if self.raw_tables:
            paths.append(self.plot_missing_values_before())
        paths.append(self.plot_missing_values())
        paths += [
            self.plot_amount_distribution(),
            self.plot_spending_by_channel(),
            self.plot_spending_by_card_type(),
            self.plot_yearly_trend(eda.yearly_trend()),
            self.plot_top_mcc(eda.top_mcc_categories()),
        ]
        if self.rfm_df is not None:
            paths.append(self.plot_segment_distribution())
            paths.append(self.plot_segment_monetary())
        return paths