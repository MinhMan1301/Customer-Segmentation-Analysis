from .DataLoader import DataLoader
from .TableCleaner import TableCleaner
from .Merger import Merger
from .EDA import EDA
from .CustomerSegmentation import CustomerSegmentation
from .Visualizer import Visualizer


class AttitudeAnalysis:
    """Main entry point: load -> clean -> merge -> EDA -> segmentation -> visualize."""

    def __init__(self, data_dir=None, chart_dir="charts"):
        self.loader = DataLoader(data_dir)
        self.chart_dir = chart_dir
        self.master_df = None
        self.raw_tables = None
        self.eda = None
        self.segmentation = None
        self.visualizer = None

    def run(self):
        raw = self.loader.load_all()
        self.raw_tables = raw

        cleaned = {
            "transactions": TableCleaner.clean_transactions(raw["transactions"]),
            "cards": TableCleaner.clean_cards(raw["cards"]),
            "users": TableCleaner.clean_users(raw["users"]),
            "mcc": TableCleaner.clean_mcc(raw["mcc"]),
            "fraud": TableCleaner.clean_fraud(raw["fraud"]),
        }

        self.master_df = Merger.merge_all(cleaned)
        self.eda = EDA(self.master_df)
        self.segmentation = CustomerSegmentation(self.master_df)
        self.segmentation.fit_segments()

        return self.master_df

    def print_summary(self):
        if self.master_df is None:
            self.run()

        print("=" * 60)
        print("1) MISSING VALUE REPORT (after cleaning)")
        print("=" * 60)
        print(self.eda.missing_value_report())

        print("\n" + "=" * 60)
        print("2) SPENDING OVERVIEW PER TRANSACTION")
        print("=" * 60)
        print(self.eda.spending_overview())

        print("\n" + "=" * 60)
        print("3) SPENDING BY TRANSACTION CHANNEL (Chip/Swipe/Online)")
        print("=" * 60)
        print(self.eda.spending_by_channel())

        print("\n" + "=" * 60)
        print("4) SPENDING BY CARD TYPE (Debit/Credit)")
        print("=" * 60)
        print(self.eda.spending_by_card_type())

        print("\n" + "=" * 60)
        print("5) YEARLY TREND (2010-2019)")
        print("=" * 60)
        print(self.eda.yearly_trend())

        print("\n" + "=" * 60)
        print("6) TOP MERCHANT CATEGORIES (MCC)")
        print("=" * 60)
        print(self.eda.top_mcc_categories())

        print("\n" + "=" * 60)
        print("7) CUSTOMER SEGMENT PROFILE (RFM Scoring)")
        print("=" * 60)
        print(self.segmentation.segment_profile())

    def generate_charts(self):
        if self.master_df is None:
            self.run()
        self.visualizer = Visualizer(
            self.master_df, self.segmentation.rfm_,
            output_dir=self.chart_dir,
            raw_tables=self.raw_tables,
        )
        paths = self.visualizer.generate_all(self.eda)
        print(f"Saved {len(paths)} charts to: {self.chart_dir}/")
        return paths