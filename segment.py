"""
segment.py
Uses YEAR 1 of demand history to classify each SKU into ABC (value) and
XYZ (variability) buckets. YEAR 2 is held out purely for policy simulation,
so the segmentation never "peeks" at the data it will be judged on.
"""
import pandas as pd
from metrics import classify_abc, classify_xyz

df = pd.read_csv("daily_demand.csv")
year1 = df[df["day"] < 365]

summary = (
    year1.groupby("sku")
    .agg(avg_demand=("demand", "mean"),
         std_demand=("demand", "std"),
         unit_cost=("unit_cost", "first"),
         lead_time=("lead_time", "first"),
         lead_time_std=("lead_time_std", "first"))
    .reset_index()
)

summary["annual_value"] = summary["avg_demand"] * 365 * summary["unit_cost"]
summary["cv"] = summary["std_demand"] / summary["avg_demand"]

summary = classify_abc(summary, "annual_value")
summary = classify_xyz(summary, "cv")
summary["segment"] = summary["abc"] + summary["xyz"]

summary.to_csv("sku_segments.csv", index=False)

if __name__ == "__main__":
    print(summary[["sku", "annual_value", "abc", "cv", "xyz", "segment"]]
          .sort_values("annual_value", ascending=False)
          .to_string(index=False))