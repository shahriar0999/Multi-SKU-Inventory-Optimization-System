"""
generate_data.py
Creates a synthetic but realistic 2-year daily demand dataset for 15 SKUs,
with a deliberate Pareto (80/20) value skew and mixed demand variability
(X/Y/Z) profiles, so ABC-XYZ segmentation has something real to find.
"""
import numpy as np
import pandas as pd

rng = np.random.default_rng(42)

N_DAYS = 730  # 2 years

# 15 SKUs: (name, avg_daily_demand, demand_cv_target, unit_cost, lead_time_days, lead_time_std)
SKU_DEFS = [
    ("rice_5kg",        40, 0.10, 60,   5, 1.0),   # A, X
    ("cooking_oil_1L",  30, 0.15, 90,   4, 1.0),   # A, X
    ("wheat_flour_2kg", 25, 0.20, 40,   5, 1.5),   # A, X/Y
    ("sugar_1kg",       20, 0.30, 55,   4, 1.0),   # B, Y
    ("eid_gift_pack",    3, 1.80, 800,  10, 3.0),  # A, Z (high value, wild demand)
    ("premium_perfume",  2, 1.60, 1200, 12, 4.0),  # A, Z
    ("tea_500g",        18, 0.25, 45,   6, 1.0),   # B, Y
    ("salt_1kg",         15, 0.12, 15,   4, 1.0),  # C, X
    ("spice_mix",         4, 0.90, 35,   7, 2.0),  # C, Y/Z
    ("biscuit_pack",     12, 0.35, 25,   5, 1.5),  # C, Y
    ("soap_bar",          10, 0.20, 20,  5, 1.0),  # C, X
    ("detergent_1kg",     8, 0.28, 60,   6, 1.5),  # C, Y
    ("designer_soap",      1, 1.40, 400, 15, 5.0), # B, Z
    ("baby_formula",       6, 0.45, 350, 8,  2.0), # A, Y
    ("instant_noodles",   22, 0.18, 12,  3,  1.0), # C, X
]

ORDERING_COST = 40          # BDT per order placed, assumed flat for simplicity
HOLDING_COST_RATE = 0.22    # 22% of unit cost per year (storage+capital+risk)
MOQ_UNITS = 25               # supplier-imposed minimum order, same across SKUs for simplicity


def generate():
    rows = []
    for name, avg_d, cv, cost, lt, lt_std in SKU_DEFS:
        std_d = avg_d * cv
        if cv > 1.0:
            # Z-type SKUs: mostly zero/low with occasional spikes (e.g. seasonal gift item)
            spikes = rng.random(N_DAYS) < 0.05
            base = rng.poisson(max(avg_d * 0.2, 0.1), N_DAYS)
            spike_vals = rng.poisson(avg_d * 8, N_DAYS)
            demand = np.where(spikes, spike_vals, base)
        else:
            demand = rng.normal(avg_d, std_d, N_DAYS)
            demand = np.clip(demand, 0, None).round().astype(int)

        for day, d in enumerate(demand):
            rows.append({"sku": name, "day": day, "demand": int(d),
                         "unit_cost": cost, "lead_time": lt, "lead_time_std": lt_std})

    df = pd.DataFrame(rows)
    df.to_csv("daily_demand.csv", index=False)
    return df


if __name__ == "__main__":
    df = generate()
    print(f"Generated {len(df)} rows for {df['sku'].nunique()} SKUs over {N_DAYS} days.")
    print(df.groupby("sku")["demand"].agg(["mean", "std"]).round(2))