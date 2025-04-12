import streamlit as st
import pandas as pd
import plotly.express as px
from run_election import run_election

# Set page config
st.set_page_config(layout="wide", page_title="MacNamara Election Simulator")

# Title
st.title("MacNamara Election Simulator")

# Create sidebar controls
with st.sidebar:
    st.header("Primary Vote Settings")  # Renamed section

    # Removed Prahran-specific sliders and logic

    # Primary vote controls for MacNamara
    alp_primary = st.slider(
        "ALP Primary", min_value=0.0, max_value=100.0, value=31.8, step=0.1
    )
    lib_primary = st.slider(
        "LIB Primary", min_value=0.0, max_value=100.0, value=29.0, step=0.1
    )
    grn_primary = st.slider(
        "GRN Primary", min_value=0.0, max_value=100.0, value=29.7, step=0.1
    )

    # Calculate OTH as remainder
    oth_primary = 100.0 - (alp_primary + lib_primary + grn_primary)
    # Ensure OTH doesn't go negative if sliders exceed 100
    oth_primary = max(0.0, oth_primary)
    st.metric("OTH Primary (Calculated)", f"{oth_primary:.1f}%")

    # Placeholder for future preference flow sliders
    st.header("Preference Flows")
    # alp_to_grn = st.slider(
        # "% ALP to GRN", min_value=0, max_value=100, value=65
    # )  # guess from prahran
    # ind_to_grn = st.slider("% of IND to GRN", min_value=0, max_value=100, value=50)

    pref_flows = {"OTH_to_ALP": 18, "OTH_to_GRN": 33, "OTH_to_LIB": 49}
    pref_flows["ALP_to_GRN"] = 83  # 83% at prahran 2022
    pref_flows["ALP_to_LIB"] = 100 - pref_flows["ALP_to_GRN"]
    pref_flows["LIB_to_GRN"] = 29 # 29% at Melbourne 2022
    pref_flows["LIB_to_ALP"] = 100 - pref_flows["LIB_to_GRN"]
    pref_flows["GRN_to_ALP"] = 88
    pref_flows["GRN_to_LIB"] = 100 - pref_flows["GRN_to_ALP"]

    st.markdown("## Micros and Independents")
    ind_to_grn = st.slider(
        "% of IND to GRN", min_value=0, max_value=100, value=pref_flows["OTH_to_GRN"]
    )
    ind_to_alp = st.slider(
        "% of IND to ALP", min_value=0, max_value=100, value=pref_flows["OTH_to_ALP"]
    )
    st.markdown(f"% of IND to LIB: {100 - ind_to_grn - ind_to_alp:.1f}%")

    st.markdown("## ALP preferences (83% to GRN in 2022 Prahran)")
    alp_to_grn = st.slider(
        "% of ALP to GRN", min_value=0, max_value=100, value=pref_flows["ALP_to_GRN"]
    )
    st.markdown(f"% of ALP to LIB: {100 - alp_to_grn:.1f}%")

    st.markdown("## GRN preferences (88% to ALP in 2022 MacNamara)")
    grn_to_alp = st.slider(
        "% of GRN to ALP", min_value=0, max_value=100, value=pref_flows["GRN_to_ALP"]
    )
    st.markdown(f"% of GRN to LIB: {100 - grn_to_alp:.1f}%")

    st.markdown("## LIB preferences (29% to GRN in 2022 Melbourne)")
    lib_to_grn = st.slider(
        "% of LIB to GRN", min_value=0, max_value=100, value=pref_flows["LIB_to_GRN"]
    )
    st.markdown(f"% of LIB to ALP: {100 - lib_to_grn:.1f}%")

 
  
# Create two columns for the plots
col1, col2 = st.columns(2)

# Define color scheme
color_map = {
    "ALP": "red",
    "GRN": "green",
    "LIB": "blue",
    "OTH": "grey",  # Changed IND to OTH
}

# Primary vote visualization
with col1:
    # st.subheader("Primary Votes")

    primary_data = pd.DataFrame(
        {
            "Party": ["ALP", "LIB", "GRN", "OTH"],  # Updated parties
            "Votes": [
                alp_primary,
                lib_primary,
                grn_primary,
                oth_primary,
            ],  # Updated votes
        }
    )

    fig_primary = px.bar(
        primary_data,
        x="Party",
        y="Votes",
        title="Primary Vote Share",
        labels={"Votes": "Percentage (%)"},
        color="Party",
        color_discrete_map=color_map,
    )
    st.plotly_chart(fig_primary, use_container_width=True)

# Placeholder call to run_election - needs adjustment based on run_election.py changes
# For now, passing the main primaries and placeholder flows
result = run_election(alp_primary, lib_primary, grn_primary, {
    "ALP_to_GRN": alp_to_grn,
    "ALP_to_LIB": 100 - alp_to_grn,
    "LIB_to_GRN": lib_to_grn,
    "LIB_to_ALP": 100 - lib_to_grn,
    "GRN_to_ALP": grn_to_alp,
    "GRN_to_LIB": 100 - grn_to_alp,
    "OTH_to_GRN": ind_to_grn,
    "OTH_to_ALP": ind_to_alp,
    "OTH_to_LIB": 100 - ind_to_grn - ind_to_alp,
})

# Determine TPP candidates and results from the simulation output
if not result:  # Handle case where run_election might return empty
    st.error("Election simulation failed.")
    st.stop()

tpp_candidates = list(result.keys())
tpp_values = list(result.values())
# Two-party preferred visualization
with col2:
    # st.subheader("Two-Party Preferred")

    tpp_data = pd.DataFrame({"Party": tpp_candidates, "Votes": tpp_values})

    fig_tpp = px.bar(
        tpp_data,
        x="Party",
        y="Votes",
        title="Two-Party Preferred Result",
        labels={"Votes": "Percentage (%)"},
        color="Party",
        color_discrete_map=color_map,
    )
    # Increase font size of axes
    fig_tpp.update_layout(
        xaxis_title_font=dict(size=18), yaxis_title_font=dict(size=18)
    )
    # Add a horizontal line at 50%
    fig_tpp.add_hline(y=50, line_dash="dash", line_color="red")
    st.plotly_chart(fig_tpp, use_container_width=True)

st.html(
    "<a href='https://poliq.au'><img src='https://poliq.au/wp-content/uploads/2024/03/poliq_wide_w.png' alt='Poliq' width='33%'></a>"
)
