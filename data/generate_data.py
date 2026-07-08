"""
Generates synthetic (mock) data for the Coverage Gap problem.

ASSUMPTION (per hackathon rule c): Real customer/officer GPS data was not
provided, so we simulate a realistic city-scale scenario:
  - 5 branches spread across a metro area
  - 15 sales officers (3 per branch)
  - 400 customer leads scattered around the branches, with some leads
    deliberately placed in "gap" zones far from any branch, and dense
    overlapping clusters near a couple of branches (mirrors the real
    problem: over-served neighborhoods + under-served ones)

Run:
    python data/generate_data.py

Produces:
    data/branches.csv
    data/officers.csv
    data/customers.csv
"""

import csv
import random
import os

random.seed(42)

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# Rough bounding box loosely modeled on a metro area (lat/long degrees)
CENTER_LAT, CENTER_LON = 19.0760, 72.8777  # Mumbai-ish, purely illustrative
SPREAD = 0.35  # degrees ~ covers a multi-district metro region

BRANCH_NAMES = ["North Branch", "East Branch", "South Branch", "West Branch", "Central Branch"]
OFFICERS_PER_BRANCH = 3
NUM_CUSTOMERS = 400


def make_branches():
    branches = []
    # Spread 5 branches roughly around the center so coverage overlaps are realistic
    offsets = [(-0.18, -0.10), (0.15, 0.12), (-0.12, 0.16), (0.14, -0.14), (0.0, 0.0)]
    for name, (dlat, dlon) in zip(BRANCH_NAMES, offsets):
        branches.append({
            "branch_id": f"B{len(branches)+1}",
            "branch_name": name,
            "lat": round(CENTER_LAT + dlat, 6),
            "lon": round(CENTER_LON + dlon, 6),
        })
    return branches


def make_officers(branches):
    officers = []
    oid = 1
    for b in branches:
        for i in range(OFFICERS_PER_BRANCH):
            officers.append({
                "officer_id": f"O{oid}",
                "officer_name": f"Officer {oid}",
                "branch_id": b["branch_id"],
                "home_lat": b["lat"],
                "home_lon": b["lon"],
            })
            oid += 1
    return officers


def make_customers(branches):
    customers = []
    # 70% of leads cluster (with noise) near existing branches -> mirrors
    # "many officers unknowingly visiting the same neighborhoods"
    # 30% are scattered in gap zones far from any branch -> mirrors
    # "large areas receive little to no coverage"
    for i in range(1, NUM_CUSTOMERS + 1):
        if random.random() < 0.7:
            b = random.choice(branches)
            lat = b["lat"] + random.gauss(0, 0.03)
            lon = b["lon"] + random.gauss(0, 0.03)
        else:
            lat = CENTER_LAT + random.uniform(-SPREAD, SPREAD)
            lon = CENTER_LON + random.uniform(-SPREAD, SPREAD)
        customers.append({
            "customer_id": f"C{i}",
            "lat": round(lat, 6),
            "lon": round(lon, 6),
            "priority": random.choice(["High", "Medium", "Low"]),
        })
    return customers


def write_csv(path, rows, fieldnames):
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    branches = make_branches()
    officers = make_officers(branches)
    customers = make_customers(branches)

    write_csv(os.path.join(OUT_DIR, "branches.csv"), branches,
               ["branch_id", "branch_name", "lat", "lon"])
    write_csv(os.path.join(OUT_DIR, "officers.csv"), officers,
               ["officer_id", "officer_name", "branch_id", "home_lat", "home_lon"])
    write_csv(os.path.join(OUT_DIR, "customers.csv"), customers,
               ["customer_id", "lat", "lon", "priority"])

    print(f"Generated {len(branches)} branches, {len(officers)} officers, {len(customers)} customers.")
    print(f"Files written to: {OUT_DIR}")


if __name__ == "__main__":
    main()
