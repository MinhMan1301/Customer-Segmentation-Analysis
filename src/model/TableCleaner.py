import pandas as pd


def clean_money_column(series):
    """Strip $ and , characters and convert to float.
    Also handles accounting-style negatives like "$(77.00)" -> -77.00.
    Invalid values become NaN."""
    cleaned = series.astype(str).str.strip()
    is_negative = cleaned.str.contains(r"\(.*\)", regex=True)
    cleaned = cleaned.str.replace(r"[\$,()]", "", regex=True)
    numeric = pd.to_numeric(cleaned, errors="coerce")
    numeric = numeric.mask(is_negative, -numeric)
    return numeric


def to_id_string(series):
    """Return identifiers as clean strings that are safe to use as merge keys.

    Columns that contain missing values are loaded as float64, so a plain
    ``astype(str)`` turns 5411 into "5411.0" and silently breaks the merge with
    the MCC table. Integral floats are converted back to integers first and
    missing values stay missing.
    """
    if pd.api.types.is_float_dtype(series):
        try:
            series = series.astype("Int64")
        except (TypeError, ValueError):
            pass  # genuinely fractional values: keep them as they are
    return series.astype(str).where(series.notna())


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


# Payment-card data the analysis never uses. Dropping it as early as possible
# keeps it out of the merged table, the dashboard and every exported artefact
# (data minimisation - PCI DSS: do not keep what you do not need).
SENSITIVE_CARD_COLUMNS = ["card_number", "cvv"]


class TableCleaner:
    """Cleans each raw table individually, before merging."""

    @staticmethod
    def clean_transactions(df):
        df = df.copy()

        if "amount" in df.columns:
            df["amount"] = clean_money_column(df["amount"])
            df["amount"] = df["amount"].fillna(df["amount"].median())

        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df["date"] = df["date"].ffill()

        df = fillna_with_mode(
            df, ["zip", "merchant_state", "mcc", "use_chip", "merchant_city"]
        )

        if "errors" in df.columns:
            df["errors"] = df["errors"].fillna("No Error")
            df["is_error"] = df["errors"].ne("No Error")

        for col in ["id", "client_id", "card_id", "merchant_id", "mcc"]:
            if col in df.columns:
                df[col] = to_id_string(df[col])

        return df

    @staticmethod
    def clean_cards(df):
        df = df.drop(columns=SENSITIVE_CARD_COLUMNS, errors="ignore")

        if "credit_limit" in df.columns:
            df["credit_limit"] = clean_money_column(df["credit_limit"])
            df["credit_limit"] = df["credit_limit"].fillna(df["credit_limit"].median())

        for col in ["has_chip", "card_on_dark_web"]:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip().str.upper().isin(
                    ["YES", "Y", "TRUE", "1"]
                )

        df = fillna_with_mode(df, ["card_brand", "card_type"])
        df = fillna_with_median(df, ["num_cards_issued", "year_pin_last_changed"])

        for col in ["id", "client_id"]:
            if col in df.columns:
                df[col] = to_id_string(df[col])

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
            df, ["current_age", "retirement_age", "credit_score", "num_credit_cards"]
        )
        df = fillna_with_mode(df, ["gender"])

        if "id" in df.columns:
            df["id"] = to_id_string(df["id"])

        df = df.rename(columns={"id": "client_id"})
        return df

    @staticmethod
    def clean_mcc(df):
        df = df.copy()
        df = df.rename(columns={
            "mcc_code": "mcc",
            "merchant_category": "mcc_description",
        })
        df["mcc"] = to_id_string(df["mcc"])
        return df

    @staticmethod
    def clean_fraud(df):
        df = df.copy()
        if "id" in df.columns:
            df["id"] = to_id_string(df["id"])
        if "label" in df.columns:
            df["is_fraud"] = df["label"].astype(str).str.strip().str.lower().eq("yes")
        return df
