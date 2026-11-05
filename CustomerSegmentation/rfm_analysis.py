from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "orders.csv"
OUTPUT_DIR = BASE_DIR / "outputs"

def calculate_rfm(analysis_date="2026-10-28"):
    """Calculate customer-level RFM values and rule-based segments."""
    orders = pd.read_csv(DATA_FILE, parse_dates=["order_date"])
    required = {"customer_code", "order_id", "order_date", "order_status", "quantity", "unit_price"}
    missing = required - set(orders.columns)
    if missing:
        raise ValueError(f"Missing required CSV columns: {sorted(missing)}")

    orders["order_status"] = orders["order_status"].astype(str).str.strip().str.lower()
    orders = orders.loc[orders["order_status"].eq("completed")].copy()
    orders["quantity"] = pd.to_numeric(orders["quantity"], errors="raise")
    orders["unit_price"] = pd.to_numeric(orders["unit_price"], errors="raise")
    if (orders["quantity"] <= 0).any() or (orders["unit_price"] < 0).any():
        raise ValueError("Quantity must be positive and unit_price cannot be negative.")

    orders["line_value"] = orders["quantity"] * orders["unit_price"]
    as_of = pd.Timestamp(analysis_date)

    # Count distinct orders, not item rows; aggregate spend across order items.
    rfm = orders.groupby("customer_code", as_index=False).agg(
        LastPurchase=("order_date", "max"),
        Frequency=("order_id", "nunique"),
        Monetary=("line_value", "sum"),
    )
    rfm["Recency"] = (as_of - rfm["LastPurchase"]).dt.days
    if (rfm["Recency"] < 0).any():
        raise ValueError("Analysis date is earlier than at least one purchase date.")

    def assign_segment(row):
        if row["Recency"] <= 30 and row["Frequency"] >= 3 and row["Monetary"] >= 2000:
            return "High-Value Active"
        if row["Recency"] > 90:
            return "At Risk / Inactive"
        if row["Frequency"] == 1:
            return "New or One-Time"
        return "Regular / Developing"

    rfm["Segment"] = rfm.apply(assign_segment, axis=1)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rfm.to_csv(OUTPUT_DIR / "rfm_table.csv", index=False)

    profiles = rfm.groupby("Segment", as_index=False).agg(
        CustomerCount=("customer_code", "count"),
        AverageRecency=("Recency", "mean"),
        AverageFrequency=("Frequency", "mean"),
        AverageSpending=("Monetary", "mean"),
        TotalSpending=("Monetary", "sum"),
    ).round(2)
    profiles.to_csv(OUTPUT_DIR / "segment_profiles.csv", index=False)

    print("\n=== RFM TABLE ===")
    print(rfm.to_string(index=False))
    print("\n=== RULE-BASED SEGMENT PROFILES ===")
    print(profiles.to_string(index=False))
    return rfm, profiles

if __name__ == "__main__":
    calculate_rfm()
