import pandas as pd
import os


class AttitudeAnalysis:
    def __init__(self, path=None):
        if path is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            path = os.path.join(base_dir, '..', 'data', 'transactions_data_25pc.csv')
        self.df = pd.read_csv(path)

    def data_cleaning(self):
        # remove $ & convert to float
        self.df["amount"] = (
            self.df["amount"]
            .replace(r'[\$,]', '', regex=True)
            .astype(float)
        )
        self.df["amount"] = self.df["amount"].fillna(self.df["amount"].median())

        # handling for values that suitable for famous values
        cols_popular = ["zip", "merchant_state", "mcc", "use_chip", "merchant_city"]
        for col in cols_popular:
            self.df[col] = self.df[col].fillna(self.df[col].mode()[0])

        # handling date misssing value
        self.df["date"] = self.df["date"].ffill()

        return self.df

    def run_analysis(self):
        self.df = self.data_cleaning()
        return self.df