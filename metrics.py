"""
metrics.py
Reusable supply-chain analytics functions.
Covers: Turnover, DIO, Safety Stock, ROP, EOQ, ABC, XYZ classification.
"""
import math
import numpy as np
import pandas as pd


# ---------- Efficiency metrics ----------

def inventory_turnover(cogs, avg_inventory):
    return cogs / avg_inventory


def days_inventory_outstanding(avg_inventory, cogs, days=365):
    return (avg_inventory / cogs) * days


# ---------- Replenishment formulas ----------

def safety_stock(avg_demand, std_demand, lead_time, std_lead_time, service_level_z):
    term1 = lead_time * (std_demand ** 2)
    term2 = (avg_demand ** 2) * (std_lead_time ** 2)
    return service_level_z * math.sqrt(term1 + term2)


def reorder_point(avg_demand, lead_time, ss):
    return (avg_demand * lead_time) + ss


def economic_order_quantity(annual_demand, ordering_cost, holding_cost):
    if annual_demand <= 0 or holding_cost <= 0:
        return 0.0
    return math.sqrt((2 * annual_demand * ordering_cost) / holding_cost)


def actual_order_quantity(eoq, moq):
    return max(eoq, moq)


# Z-score lookup for common service levels
SERVICE_LEVEL_Z = {0.90: 1.28, 0.95: 1.65, 0.975: 1.96, 0.98: 2.05, 0.99: 2.33}


# ---------- Segmentation ----------

def classify_abc(df, value_col="annual_value"):
    df = df.sort_values(value_col, ascending=False).reset_index(drop=True)
    df["cum_pct"] = (df[value_col].cumsum() / df[value_col].sum()) * 100

    def _cat(p):
        if p <= 80:
            return "A"
        elif p <= 95:
            return "B"
        return "C"

    df["abc"] = df["cum_pct"].apply(_cat)
    return df


def classify_xyz(df, cv_col="cv"):
    def _cat(cv):
        if cv <= 0.5:
            return "X"
        elif cv <= 1.0:
            return "Y"
        return "Z"

    df["xyz"] = df[cv_col].apply(_cat)
    return df


# service level target assigned by ABC criticality (A = most critical -> highest target)
ABC_SERVICE_LEVEL = {"A": 0.99, "B": 0.95, "C": 0.90}