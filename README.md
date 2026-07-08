# Coverage Gap Allocator

**AceN Navadhan Hackathon 2026 — Problem 1: The Coverage Gap**

## Problem
A financial institution grew to 120 branches and 2,500+ sales officers, but despite
a 35% headcount increase, customer visits stayed flat. Officers unknowingly overlap
on the same neighborhoods while large areas get little to no coverage. Branch Managers
spend ~2 hours every morning manually planning allocations in spreadsheets.

## Solution
A lightweight allocation engine that replaces manual spreadsheet planning:

1. Clusters all customer/lead locations into geographically compact, **non-overlapping
   zones** — one per available sales officer — using KMeans.
2. Matches each zone to the officer who can reach it fastest from their home branch.
3. Generates each officer's daily visit list automatically.
4. Dashboard shows a live **before/after comparison** against today's manual approach,
   with coverage %, overlap count, and missed-customer count as concrete metrics.

### Results on the simulated dataset (400 leads, 15 officers, 5 branches)
| Metric | Manual (today) | Optimized |
|---|---|---|
| Coverage | 62% | **100%** |
| Overlapping visits | 248 | **0** |
| Customers missed | 152 | **0** |
| Avg travel distance/officer | 3.27 km | 7.52 km |

The optimized approach trades a modest increase in average travel distance for full
coverage and zero wasted duplicate visits — a trade-off explicitly surfaced in the
app rather than hidden, since a real Branch Manager would need to see both sides.

## Assumptions
- Real CRM/GPS data wasn't provided, so synthetic data (5 branches, 15 officers,
  400 customer leads with lat/long) was generated to mirror the scale and pattern
  described in the problem (see `data/generate_data.py`).
- The "manual/before" baseline simulates officers covering a fixed radius around
  their home branch independently — this reproduces the overlap-and-gap symptom
  described in the problem statement.
- This tool solves the **allocation** problem (who visits which customers). Route
  optimization *within* a zone (visit order) is a natural next step, not covered here.
- No headcount increase assumed — same 15 officers, better allocation only.

## Tech Stack
- Python, Streamlit (dashboard/UI)
- scikit-learn (KMeans clustering)
- pandas (data handling)
- pydeck (map visualization)

## How to Run
```bash
git clone https://github.com/tarwanipiyush/coverage-gap-hackathon.git
cd coverage-gap-hackathon
pip install -r requirements.txt
python data/generate_data.py   # generates mock data (already included, but re-runnable)
streamlit run app.py
```
Then open the local URL Streamlit prints (usually http://localhost:8501).

## Project Structure
```
coverage-gap-hackathon/
├── app.py                  # Streamlit dashboard (entry point)
├── core/
│   └── allocator.py        # Naive vs optimized allocation logic + metrics
├── data/
│   ├── generate_data.py    # Synthetic data generator
│   ├── branches.csv
│   ├── officers.csv
│   └── customers.csv
├── requirements.txt
└── README.md
```

## Team
DJSCE — <add your team name / member names here>
