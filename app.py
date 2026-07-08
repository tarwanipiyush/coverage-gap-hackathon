"""
Coverage Gap Allocator - Streamlit demo app.

Run with:
    streamlit run app.py

Shows a side-by-side BEFORE (manual/naive) vs AFTER (optimized) comparison
of how sales officers are assigned to customer visits, addressing the
"Coverage Gap" problem statement.
"""

import streamlit as st
import pandas as pd
import pydeck as pdk

from core.allocator import load_data, naive_allocation, optimized_allocation

st.set_page_config(page_title="Coverage Gap Allocator", layout="wide")

DATA_DIR = "data"

# Distinct colors per zone for the optimized map (RGB)
ZONE_COLORS = [
    [230, 25, 75], [60, 180, 75], [0, 130, 200], [245, 130, 48],
    [145, 30, 180], [70, 240, 240], [240, 50, 230], [210, 245, 60],
    [250, 190, 212], [0, 128, 128], [220, 190, 255], [170, 110, 40],
    [255, 250, 200], [128, 0, 0], [170, 255, 195],
]


@st.cache_data
def get_data():
    return load_data(DATA_DIR)


@st.cache_data
def compute_allocations(_officers, _customers):
    naive = naive_allocation(_officers, _customers)
    optimized = optimized_allocation(_officers, _customers)
    return naive, optimized


def build_naive_map(customers, coverage_count, branches):
    df = customers.copy()
    df["visits"] = df["customer_id"].map(coverage_count)

    def color(v):
        if v == 0:
            return [200, 200, 200]  # gray = missed
        if v > 1:
            return [230, 25, 75]    # red = overlap (over-served)
        return [60, 180, 75]        # green = covered once (ideal)

    df["color"] = df["visits"].apply(color)

    layer = pdk.Layer(
        "ScatterplotLayer", data=df,
        get_position="[lon, lat]", get_fill_color="color",
        get_radius=180, pickable=True,
    )
    branch_layer = pdk.Layer(
        "ScatterplotLayer", data=branches,
        get_position="[lon, lat]", get_fill_color="[0,0,0]",
        get_radius=400, pickable=True,
    )
    view = pdk.ViewState(latitude=customers["lat"].mean(), longitude=customers["lon"].mean(), zoom=9)
    return pdk.Deck(layers=[layer, branch_layer], initial_view_state=view,
                     tooltip={"text": "{customer_id}\nVisits: {visits}"})


def build_optimized_map(customers_with_zone, branches):
    df = customers_with_zone.copy()
    df["color"] = df["zone"].apply(lambda z: ZONE_COLORS[z % len(ZONE_COLORS)])

    layer = pdk.Layer(
        "ScatterplotLayer", data=df,
        get_position="[lon, lat]", get_fill_color="color",
        get_radius=180, pickable=True,
    )
    branch_layer = pdk.Layer(
        "ScatterplotLayer", data=branches,
        get_position="[lon, lat]", get_fill_color="[0,0,0]",
        get_radius=400, pickable=True,
    )
    view = pdk.ViewState(latitude=customers_with_zone["lat"].mean(),
                          longitude=customers_with_zone["lon"].mean(), zoom=9)
    return pdk.Deck(layers=[layer, branch_layer], initial_view_state=view,
                     tooltip={"text": "{customer_id}\nZone: {zone}"})


def main():
    st.title("🗺️ Coverage Gap Allocator")
    st.caption(
        "Problem: 2,500+ sales officers, 120 branches — despite a 35% headcount increase, "
        "customer visits stayed flat because officers unknowingly overlap on the same "
        "neighborhoods while other areas get skipped. This tool auto-generates balanced, "
        "non-overlapping daily coverage zones so Branch Managers stop doing this by hand."
    )

    branches, officers, customers = get_data()
    naive, optimized = compute_allocations(officers, customers)

    total = len(customers)

    st.subheader("Impact Summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Coverage %", f"{optimized['covered']/total*100:.0f}%",
               delta=f"+{(optimized['covered']-naive['covered'])/total*100:.0f} pts vs manual")
    c2.metric("Overlapping visits", optimized["overlapped"],
               delta=f"{optimized['overlapped']-naive['overlapped']}", delta_color="inverse")
    c3.metric("Customers missed", optimized["uncovered"],
               delta=f"{optimized['uncovered']-naive['uncovered']}", delta_color="inverse")
    c4.metric("Avg travel distance", f"{optimized['avg_travel_km']} km",
               delta=f"{optimized['avg_travel_km']-naive['avg_travel_km']:+.2f} km", delta_color="inverse")

    st.divider()

    left, right = st.columns(2)
    with left:
        st.markdown("### ❌ Before — Manual Assignment (today)")
        st.caption("Gray = never visited · Red = visited by 2+ officers (wasted effort) · Green = visited once")
        st.pydeck_chart(build_naive_map(customers, naive["coverage_count"], branches))

    with right:
        st.markdown("### ✅ After — Optimized Zones (this tool)")
        st.caption("Each color = one officer's exclusive daily zone. No overlap, no gaps.")
        st.pydeck_chart(build_optimized_map(optimized["customers_with_zone"], branches))

    st.divider()
    st.subheader("Daily Visit List (per officer)")
    officer_choice = st.selectbox("Select an officer to view their optimized visit list",
                                    officers["officer_id"] + " — " + officers["officer_name"])
    officer_id = officer_choice.split(" — ")[0]
    visit_list = optimized["assignments"][officer_id]
    st.write(f"**{len(visit_list)} customers assigned to {officer_id} today:**")
    st.dataframe(customers[customers["customer_id"].isin(visit_list)][["customer_id", "priority"]],
                 use_container_width='stretch', hide_index=True)

    with st.expander("Assumptions made for this demo"):
        st.markdown(
            "- Real CRM lead/customer GPS coordinates were not provided, so synthetic data "
            "(5 branches, 15 officers, 400 customer leads) was generated to simulate the scale "
            "and geographic pattern described in the problem statement.\n"
            "- 'Before' numbers simulate today's manual process as officers covering a fixed "
            "radius around their home branch, independently — reproducing the overlap/gap "
            "pattern described in the problem.\n"
            "- 'After' zones are generated with KMeans clustering (one cluster per officer), "
            "then matched to the closest officer by travel distance. In production this would "
            "run daily against live CRM data and account for officer leave, priority leads, "
            "and branch capacity.\n"
            "- This is a scheduling/allocation engine, not a routing engine — it decides *who* "
            "visits *which customers*, not the optimal order/route within a zone (a logical next step)."
        )


if __name__ == "__main__":
    main()
