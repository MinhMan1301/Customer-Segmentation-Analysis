class Merger:
    """Merges the 5 tables into one master table, at transaction-level granularity
    (one row = one transaction)."""

    @staticmethod
    def merge_all(tables):
        tx = tables["transactions"]
        cards = tables["cards"]
        users = tables["users"]
        mcc = tables["mcc"]
        fraud = tables["fraud"]

        master = tx.merge(cards, on="card_id", how="left", suffixes=("", "_card"))
        master = master.merge(users, on="client_id", how="left", suffixes=("", "_user"))
        master = master.merge(mcc, on="mcc", how="left")
        master = master.merge(fraud[["id", "is_fraud"]], on="id", how="left")
        master["is_fraud"] = master["is_fraud"].fillna(False)

        return master