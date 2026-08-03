import pandas as pd


def clean_money_column(series):
    """Strip $ and , characters and convert to float. Invalid values become NaN."""
    cleaned = series.astype(str).str.replace(r"[\$,]", "", regex=True)
    return pd.to_numeric(cleaned, errors="coerce")


def fillna_with_mode(df, cols):
    for col in cols:
        if col not in df.columns:
            continue
        mode_val = df[col].mode()
        if not mode_val.empty:
            df[col] = df[col].fillna(mode_val[0])
    return df


def fillna_with_median(df, cols):
    for col in cols:
        if col in df.columns:
            df[col] = df[col].fillna(df[col].median())
    return df


class TableCleaner:
    """Cleans each raw table individually, before merging."""

    @staticmethod
    def clean_transactions(df):
        df = df.copy()

        # amount: strip $ , convert to float, fill missing with median
        if "amount" in df.columns:
            df["amount"] = clean_money_column(df["amount"])
            df["amount"] = df["amount"].fillna(df["amount"].median())

        # date -> real datetime (raw file includes hour:minute:second)
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df["date"] = df["date"].ffill()

        # categorical/identifier columns -> fill with mode (most frequent value)
        df = fillna_with_mode(
            df, ["zip", "merchant_state", "mcc", "use_chip", "merchant_city"]
        )

        # errors: NaN means the transaction had no error -> label explicitly
        if "errors" in df.columns:
            df["errors"] = df["errors"].fillna("No Error")
            df["is_error"] = df["errors"].ne("No Error")

        # cast id columns to string to avoid dtype mismatches during merge
        for col in ["id", "client_id", "card_id", "merchant_id", "mcc"]:
            if col in df.columns:
                df[col] = df[col].astype(str)

        return df

    @staticmethod
    def clean_cards(df):
        df = df.copy()

        if "credit_limit" in df.columns:
            df["credit_limit"] = clean_money_column(df["credit_limit"])
            df["credit_limit"] = df["credit_limit"].fillna(df["credit_limit"].median())

        # has_chip / on_dark_web -> normalize to boolean
        for col in ["has_chip", "card_on_dark_web"]:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip().str.upper().isin(
                    ["YES", "Y", "TRUE", "1"]
                )

        df = fillna_with_mode(df, ["card_brand", "card_type"])
        df = fillna_with_median(df, ["num_cards_issued", "year_pin_last_changed"])

        for col in ["id", "client_id"]:
            if col in df.columns:
                df[col] = df[col].astype(str)

        # rename to avoid a column-name clash with the transactions table after merge
        df = df.rename(columns={"id": "card_id"})
        return df

    @staticmethod
    def clean_users(df):
        df = df.copy()

        for col in ["per_capita_income", "yearly_income", "total_debt"]:
            if col in df.columns:
                df[col] = clean_money_column(df[col])
                df[col] = df[col].fillna(df[col].median())

        df = fillna_with_median(
            df, ["current_age", "retirement_age", "credit_score", "num_credit_card"]
        )
        df = fillna_with_mode(df, ["gender"])

        if "id" in df.columns:
            df["id"] = df["id"].astype(str)

        df = df.rename(columns={"id": "client_id"})
        return df

    @staticmethod
    def clean_mcc(df):
        # real file columns: "mcc_code", "merchant_category"
        df = df.copy()
        df = df.rename(columns={
            "mcc_code": "mcc",
            "merchant_category": "mcc_description",
        })
        df["mcc"] = df["mcc"].astype(str)
        return df

    @staticmethod
    def clean_fraud(df):
        # real file columns: "id", "label" with values "Yes"/"No"
        df = df.copy()
        if "id" in df.columns:
            df["id"] = df["id"].astype(str)
        if "label" in df.columns:
            df["is_fraud"] = df["label"].astype(str).str.strip().str.lower().eq("yes")
        return df