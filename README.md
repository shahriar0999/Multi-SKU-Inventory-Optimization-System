# Multi-SKU-Inventory-Optimization-System

A Python project that simulates and compares two inventory replenishment strategies across fifteen SKUs and two years of demand history, quantifying the real-world impact of moving from a uniform, rule-of-thumb policy to a data-driven, segment-specific one.

## Overview

Most small and mid-sized retailers manage inventory the same way for every product: a fixed reorder threshold and a fixed order quantity, regardless of how valuable or how unpredictable a product actually is. This project asks a simple question: what happens if replenishment decisions are instead driven by each product's value and demand variability, using the standard inventory management formulas (Safety Stock, Reorder Point, Economic Order Quantity, ABC and XYZ classification)?

To answer this, the project generates two years of realistic daily demand data for fifteen SKUs, classifies each SKU using ABC-XYZ analysis based on the first year, and then simulates both the naive policy and the optimized policy day by day over the second (held-out) year. Because both policies are run against the exact same demand stream, the comparison isolates the effect of the policy itself rather than differences in the underlying data.

## Result Summary

Applying the optimized, segment-aware policy instead of the naive uniform policy produced the following changes over the one-year simulation period, aggregated across all fifteen SKUs.

| Metric | Naive Policy (Before) | Optimized Policy (After) | Change |
|---|---|---|---|
| Total inventory cost (holding plus ordering) | 85,145 | 55,446 | down 34.9 percent |
| Average on-hand inventory (units, all SKUs) | 5,409 | 2,124 | down 60.7 percent |
| Total stockout days (all SKUs, one year) | 32 | 9 | down 71.9 percent |
| Overall service level | 99.42 percent | 99.84 percent | up 0.42 points |

These four numbers together tell a coherent story: the optimized policy did not simply cut costs at the expense of availability, and it did not simply hold more stock to avoid stockouts. It held less inventory overall while stocking out less often, because the buffer was placed where the data showed it was actually needed rather than spread evenly across every product.

One result is worth calling out honestly rather than hiding. For the two highest-value, most unpredictable SKUs in the dataset, the optimized policy actually increased holding cost compared to the naive policy, while sharply reducing stockout days. The naive policy appeared cheaper for these two products only because it was under-stocking them and missing sales during their most valuable selling periods, a cost that is not captured in a holding-and-ordering cost model alone. The optimized policy correctly identified these as the products deserving the most protection, which is the entire point of combining value-based and variability-based segmentation.

| SKU (segment) | Cost Before | Cost After | Stockout Days Before | Stockout Days After |
|---|---|---|---|---|
| Premium perfume (high value, highly variable) | 6,683 | 10,744 | 17 | 0 |
| Seasonal gift package (high value, highly variable) | 7,153 | 8,240 | 8 | 3 |

The full per-SKU breakdown for all fifteen products is available in simulation_results.csv.

## Methodology

The project is organized into four sequential steps, each in its own file.

Data generation produces two years of daily demand for fifteen SKUs, deliberately constructed so that a small number of products account for most of the annual sales value, following the Pareto pattern commonly seen in real inventory data, while demand variability differs sharply across products, from steady staples to spiky seasonal items.

Segmentation uses only the first year of data to classify each SKU along two independent dimensions. ABC classification ranks products by their contribution to total annual value. XYZ classification ranks products by their coefficient of variation, a measure of how unpredictable demand is relative to its average. Combining the two produces nine possible segments, such as high-value and predictable, or high-value and highly unpredictable, each of which warrants a different inventory strategy.

Policy design translates each segment into concrete replenishment parameters using standard formulas. Safety stock accounts for uncertainty in both demand and lead time, with the target service level set higher for more critical (A-category) products. The reorder point combines expected demand during lead time with that safety stock. Order quantity is set using the economic order quantity formula, bounded below by a minimum order quantity constraint that a supplier might impose.

Simulation runs both policies, day by day, over the second year of demand, which was never used during segmentation or parameter calculation. Each day the simulation receives any inventory that was ordered previously, fulfills as much of that day's demand as current stock allows, records whether a stockout occurred, and checks whether the reorder point has been crossed. If it has, and no order is currently in transit, a new order is placed with a randomly varying lead time to reflect real supplier uncertainty.

## Repository Structure

generate_data.py creates the synthetic two-year demand dataset and writes it to a csv file.

segment.py reads the first year of that data and produces ABC and XYZ classifications for each SKU.

metrics.py contains the reusable inventory formulas used throughout the project, including safety stock, reorder point, economic order quantity, and the classification functions.

simulate.py runs the day-by-day simulation for both the naive and optimized policies over the held-out second year and writes the comparison results to a csv file.

REPORT.md contains the full write-up of the methodology and results in more detail than this readme.

## Running the Project

The three scripts are meant to be run in order from the project directory.

```
python generate_data.py
python segment.py
python simulate.py
```

The first script writes daily_demand.csv. The second reads that file and writes sku_segments.csv. The third reads both files and writes simulation_results.csv, printing a per-SKU comparison table to the console.

## Limitations

The demand data used here is synthetic rather than drawn from a real point-of-sale or ERP system, so the specific percentages should be read as a demonstration of methodology rather than a guaranteed result on any particular business's data. The cost model includes holding and ordering costs but does not include the cost of a lost sale during a stockout, which is why the trade-off on the two highest-variability SKUs looks like a cost increase rather than the net benefit it likely represents in practice. The minimum order quantity is held constant across all SKUs for simplicity, and lead time variability is modeled as normally distributed, both of which would be refined with access to real supplier data.

## Skills Demonstrated

This project applies core inventory management concepts, including inventory turnover, safety stock, reorder point, economic order quantity, minimum order quantity, and ABC-XYZ segmentation, and implements each of them as tested, reusable Python functions rather than one-off calculations. It also demonstrates a discrete-event simulation approach to evaluating a business policy, a train-test style separation between the data used to design a policy and the data used to evaluate it, and a willingness to report a result that complicates the headline numbers rather than a purely favorable summary.