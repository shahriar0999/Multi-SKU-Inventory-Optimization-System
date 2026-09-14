"""
simulate.py
Day-by-day inventory simulation over YEAR 2 (the held-out period), comparing:

  BEFORE (naive / common real-world practice):
    - Same rule-of-thumb for every SKU regardless of segment
    - Reorder point = 15 days x average demand
    - Order quantity = 30 days x average demand (not cost-optimized, no MOQ logic)
    - No differentiation by criticality or variability

  AFTER (optimized / what this project applies):
    - Reorder point = demand-during-lead-time + Safety Stock
    - Safety Stock uses the full formula (demand + lead-time variance),
      with the Z target set by ABC criticality (A=99%, B=95%, C=90%)
    - Order quantity = EOQ, bounded below by MOQ

Both policies use the SAME held-out demand stream per SKU, so the
comparison isolates the effect of the ordering policy itself.
"""
import numpy as np
import pandas as pd
from metrics import (safety_stock, reorder_point, economic_order_quantity,
                      actual_order_quantity, ABC_SERVICE_LEVEL, SERVICE_LEVEL_Z)

rng = np.random.default_rng(7)

ORDERING_COST = 40
HOLDING_COST_RATE = 0.22
MOQ_UNITS = 25


def simulate_sku(demand_series, lead_time, lead_time_std, avg_demand, std_demand,
                  unit_cost, rop, order_qty, start_stock):
    """Simulate one SKU for len(demand_series) days under a fixed (ROP, order_qty) policy."""
    stock = start_stock
    pending_orders = []   # list of (arrival_day, qty)
    stockout_days = 0
    stockout_episodes = 0
    in_stockout = False
    orders_placed = 0
    inventory_levels = []

    for day, demand_today in enumerate(demand_series):
        # receive any orders arriving today
        arrived_today = [q for (arr, q) in pending_orders if arr == day]
        for q in arrived_today:
            stock += q
        pending_orders = [(arr, q) for (arr, q) in pending_orders if arr != day]

        # fulfil demand (can't sell what you don't have)
        sold = min(stock, demand_today)
        stock -= sold
        unmet = demand_today - sold

        if unmet > 0:
            stockout_days += 1
            if not in_stockout:
                stockout_episodes += 1
                in_stockout = True
        else:
            in_stockout = False

        inventory_levels.append(stock)

        # check reorder point (after today's demand is applied)
        if stock <= rop and not pending_orders:
            actual_lead = max(1, int(round(rng.normal(lead_time, lead_time_std))))
            pending_orders.append((day + actual_lead, order_qty))
            orders_placed += 1

    avg_inventory = float(np.mean(inventory_levels))
    holding_cost = avg_inventory * unit_cost * HOLDING_COST_RATE * (len(demand_series) / 365)
    ordering_cost_total = orders_placed * ORDERING_COST
    service_level = 1 - (stockout_days / len(demand_series))

    return {
        "avg_inventory": avg_inventory,
        "holding_cost": holding_cost,
        "ordering_cost": ordering_cost_total,
        "total_cost": holding_cost + ordering_cost_total,
        "stockout_days": stockout_days,
        "stockout_episodes": stockout_episodes,
        "service_level": service_level,
        "orders_placed": orders_placed,
    }


def run_comparison():
    df = pd.read_csv("daily_demand.csv")
    seg = pd.read_csv("sku_segments.csv")
    year2 = df[df["day"] >= 365].copy()

    results = []
    for _, row in seg.iterrows():
        sku = row["sku"]
        demand_series = year2[year2["sku"] == sku]["demand"].values
        avg_d, std_d = row["avg_demand"], row["std_demand"]
        lt, lt_std, cost = row["lead_time"], row["lead_time_std"], row["unit_cost"]

        # ---- BEFORE: naive uniform rule ----
        naive_rop = avg_d * 15
        naive_qty = avg_d * 30
        before = simulate_sku(demand_series, lt, lt_std, avg_d, std_d, cost,
                               rop=naive_rop, order_qty=max(naive_qty, 1),
                               start_stock=naive_qty)

        # ---- AFTER: segment-driven optimized policy ----
        target_sl = ABC_SERVICE_LEVEL[row["abc"]]
        z = SERVICE_LEVEL_Z[target_sl]
        ss = safety_stock(avg_d, std_d, lt, lt_std, z)
        rop_opt = reorder_point(avg_d, lt, ss)
        eoq = economic_order_quantity(avg_d * 365, ORDERING_COST, cost * HOLDING_COST_RATE)
        qty_opt = actual_order_quantity(eoq, MOQ_UNITS)
        after = simulate_sku(demand_series, lt, lt_std, avg_d, std_d, cost,
                              rop=rop_opt, order_qty=max(qty_opt, 1),
                              start_stock=rop_opt + qty_opt)

        results.append({"sku": sku, "segment": row["segment"],
                         "before_cost": before["total_cost"], "after_cost": after["total_cost"],
                         "before_avg_inv": before["avg_inventory"], "after_avg_inv": after["avg_inventory"],
                         "before_stockout_days": before["stockout_days"], "after_stockout_days": after["stockout_days"],
                         "before_service_level": before["service_level"], "after_service_level": after["service_level"],
                         "before_orders": before["orders_placed"], "after_orders": after["orders_placed"]})

    return pd.DataFrame(results)


if __name__ == "__main__":
    res = run_comparison()
    res.to_csv("simulation_results.csv", index=False)
    print(res.round(2).to_string(index=False))