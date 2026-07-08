"""
Core logic for the Coverage Gap solution.

Two allocation strategies are computed so the app can show a clear
BEFORE vs AFTER comparison:

1. naive_allocation()
   Mimics today's manual process: officers are just assigned round-robin
   to the nearest branch's customer pool without any spatial balancing.
   This reproduces the real symptoms described in the problem: officers
   from the same branch overlap on the same nearby customers, while
   customers far from any branch (gap zones) get left out entirely.

2. optimized_allocation()
   Uses KMeans clustering on customer lat/lon to create N geographically
   compact, non-overlapping zones (N = number of officers), then assigns
   one zone to each officer. This guarantees:
     - every customer is covered by exactly one officer (no overlap)
     - zones are balanced by geographic proximity, not just branch proximity
     - officers are assigned to the zone closest to their home branch,
       to keep travel distance reasonable

Coverage metrics computed for both:
     - customers_covered / total_customers (%)
     - overlap_count: customers that would be visited by >1 officer
     - avg_travel_distance: mean distance from officer's home to their
       assigned customers (rough proxy for cost/efficiency)
"""

import math
import pandas as pd
from sklearn.cluster import KMeans


def haversine(lat1, lon1, lat2, lon2):
    """Approximate distance in km between two lat/lon points."""
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def load_data(data_dir):
    branches = pd.read_csv(f"{data_dir}/branches.csv")
    officers = pd.read_csv(f"{data_dir}/officers.csv")
    customers = pd.read_csv(f"{data_dir}/customers.csv")
    return branches, officers, customers


def naive_allocation(officers: pd.DataFrame, customers: pd.DataFrame, radius_km=6.0):
    """
    Simulates today's manual approach: each officer is simply told to
    cover customers "near their branch" within a fixed radius, independent
    of what other officers from the same branch are doing.
    This naturally produces overlap (multiple officers covering the same
    nearby customers) and gaps (customers outside every officer's radius
    are never covered).
    """
    assignments = {o["officer_id"]: [] for _, o in officers.iterrows()}
    coverage_count = {c["customer_id"]: 0 for _, c in customers.iterrows()}

    for _, off in officers.iterrows():
        for _, cust in customers.iterrows():
            d = haversine(off["home_lat"], off["home_lon"], cust["lat"], cust["lon"])
            if d <= radius_km:
                assignments[off["officer_id"]].append(cust["customer_id"])
                coverage_count[cust["customer_id"]] += 1

    covered = sum(1 for v in coverage_count.values() if v >= 1)
    overlapped = sum(1 for v in coverage_count.values() if v > 1)
    uncovered = sum(1 for v in coverage_count.values() if v == 0)

    avg_dist = _avg_travel_distance(officers, customers, assignments)

    return {
        "assignments": assignments,
        "coverage_count": coverage_count,
        "covered": covered,
        "overlapped": overlapped,
        "uncovered": uncovered,
        "avg_travel_km": avg_dist,
    }


def optimized_allocation(officers: pd.DataFrame, customers: pd.DataFrame, random_state=42):
    """
    KMeans-based zone allocation: creates one compact zone per officer,
    so every customer belongs to exactly one zone (no overlap, no gap),
    then matches zones to officers by proximity to minimize travel.
    """
    n_officers = len(officers)
    coords = customers[["lat", "lon"]].values

    km = KMeans(n_clusters=n_officers, random_state=random_state, n_init=10)
    labels = km.fit_predict(coords)
    customers = customers.copy()
    customers["zone"] = labels
    centroids = km.cluster_centers_

    # Match each zone centroid to the nearest still-unassigned officer
    # (simple greedy matching keeps travel distance low)
    officer_list = officers.to_dict("records")
    zone_to_officer = {}
    used_officers = set()

    zone_order = sorted(
        range(n_officers),
        key=lambda z: -sum(labels == z)  # assign largest zones first
    )

    for zone_id in zone_order:
        czlat, czlon = centroids[zone_id]
        best_officer, best_dist = None, float("inf")
        for off in officer_list:
            if off["officer_id"] in used_officers:
                continue
            d = haversine(off["home_lat"], off["home_lon"], czlat, czlon)
            if d < best_dist:
                best_dist = d
                best_officer = off
        zone_to_officer[zone_id] = best_officer["officer_id"]
        used_officers.add(best_officer["officer_id"])

    assignments = {o["officer_id"]: [] for o in officer_list}
    coverage_count = {c: 0 for c in customers["customer_id"]}
    for _, cust in customers.iterrows():
        officer_id = zone_to_officer[cust["zone"]]
        assignments[officer_id].append(cust["customer_id"])
        coverage_count[cust["customer_id"]] += 1

    covered = sum(1 for v in coverage_count.values() if v >= 1)
    overlapped = sum(1 for v in coverage_count.values() if v > 1)  # will be 0 by construction
    uncovered = sum(1 for v in coverage_count.values() if v == 0)  # will be 0 by construction

    avg_dist = _avg_travel_distance(officers, customers, assignments)

    return {
        "assignments": assignments,
        "coverage_count": coverage_count,
        "covered": covered,
        "overlapped": overlapped,
        "uncovered": uncovered,
        "avg_travel_km": avg_dist,
        "customers_with_zone": customers,  # has 'zone' column, used for map coloring
        "zone_to_officer": zone_to_officer,
    }


def _avg_travel_distance(officers, customers, assignments):
    officer_home = {o["officer_id"]: (o["home_lat"], o["home_lon"]) for _, o in officers.iterrows()}
    cust_loc = {c["customer_id"]: (c["lat"], c["lon"]) for _, c in customers.iterrows()}

    dists = []
    for officer_id, cust_ids in assignments.items():
        hlat, hlon = officer_home[officer_id]
        for cid in cust_ids:
            clat, clon = cust_loc[cid]
            dists.append(haversine(hlat, hlon, clat, clon))
    return round(sum(dists) / len(dists), 2) if dists else 0.0
