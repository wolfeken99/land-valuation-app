# Land Valuation App with Multi-Scenario IRR-Based Land Pricing
import streamlit as st
import numpy as np
import numpy_financial as npf
from scipy.optimize import minimize_scalar

# Core calculation function
def calculate_land_price(
    rent,
    vacancy,
    opex_ratio,
    hard_cost,
    soft_cost_ratio,
    cap_rate,
    exit_cap_rate,
    rent_growth,
    hold_years,
    equity_ratio,
    target_irr,
    lot_size_sqft,
    far,
    apt_size
):
    buildable_sqft = lot_size_sqft * far
    units = int(buildable_sqft // apt_size)
    gross_rent = rent * 12 * units
    egi = gross_rent * (1 - vacancy)
    opex = egi * opex_ratio
    noi = egi - opex
    noi_exit = noi * ((1 + rent_growth) ** hold_years)
    exit_value = noi_exit / exit_cap_rate

    hard = buildable_sqft * hard_cost
    soft = hard * soft_cost_ratio
    total_cost = hard + soft

    def irr_error(land_cost):
        total = total_cost + land_cost
        equity = total * equity_ratio
        cash_flows = [noi * ((1 + rent_growth) ** i) * equity_ratio for i in range(hold_years)]
        cash_flows[-1] += exit_value
        irr = npf.irr([-equity] + cash_flows)
        return abs(irr - target_irr)

    result = minimize_scalar(irr_error, bounds=(0, 50_000_000), method='bounded')
    land_price = result.x if result.success else 0
    return land_price, buildable_sqft, units, noi, exit_value

# Layout
st.title("🏗️ Multi-Scenario Land Valuation Tool (IRR-Based)")
st.write("Adjust assumptions for each economic scenario below. Enter a probability for each and compute a weighted expected land value.")

# Constants
lot_size_sqft = 10000
far = 3.0
apt_size = 1000

scenarios = ["Baseline", "Expansion", "Recession", "Stagflation"]
def_scenario_inputs = {
    "Baseline": dict(rent=2800, vacancy=0.05, opex=0.35, hard=300, soft=0.25, cap=0.05, exit_cap=0.05, growth=0.02, prob=0.40),
    "Expansion": dict(rent=3100, vacancy=0.03, opex=0.32, hard=290, soft=0.22, cap=0.045, exit_cap=0.045, growth=0.04, prob=0.30),
    "Recession": dict(rent=2400, vacancy=0.08, opex=0.40, hard=320, soft=0.28, cap=0.06, exit_cap=0.065, growth=0.01, prob=0.20),
    "Stagflation": dict(rent=2600, vacancy=0.07, opex=0.38, hard=350, soft=0.30, cap=0.055, exit_cap=0.06, growth=0.00, prob=0.10)
}

results = []
target_irr = st.slider("Target IRR (for all scenarios)", 0.05, 0.30, 0.18)
hold_years = st.slider("Hold Period (Years)", 5, 20, 10)
equity_ratio = st.slider("Equity Investment Ratio", 0.1, 1.0, 0.3)

st.markdown("---")

for name in scenarios:
    with st.expander(f"Scenario: {name}", expanded=True):
        col1, col2, col3 = st.columns(3)
        inputs = def_scenario_inputs[name]
        rent = col1.number_input(f"Monthly Rent per Unit - {name}", value=inputs["rent"])
        vacancy = col2.slider(f"Vacancy Rate - {name}", 0.0, 0.2, inputs["vacancy"])
        opex = col3.slider(f"Opex Ratio - {name}", 0.0, 1.0, inputs["opex"])

        col4, col5, col6 = st.columns(3)
        hard = col4.number_input(f"Hard Cost/SqFt - {name}", value=inputs["hard"])
        soft = col5.slider(f"Soft Cost Ratio - {name}", 0.0, 1.0, inputs["soft"])
        cap = col6.slider(f"Cap Rate - {name}", 0.02, 0.10, inputs["cap"])

        col7, col8, col9 = st.columns(3)
        exit_cap = col7.slider(f"Exit Cap Rate - {name}", 0.02, 0.10, inputs["exit_cap"])
        growth = col8.slider(f"Annual Rent Growth - {name}", 0.00, 0.10, inputs["growth"])
        prob = col9.slider(f"Probability - {name}", 0.0, 1.0, inputs["prob"])

        land, sqft, units, noi, exit_val = calculate_land_price(
            rent, vacancy, opex, hard, soft, cap, exit_cap, growth,
            hold_years, equity_ratio, target_irr, lot_size_sqft, far, apt_size
        )

        results.append(dict(
            Scenario=name,
            Probability=prob,
            Land_Value=land,
            Units=units,
            Buildable_SqFt=sqft,
            NOI=noi,
            Exit_Value=exit_val
        ))

st.markdown("---")
st.subheader("📊 Summary Table")
import pandas as pd
summary_df = pd.DataFrame(results)
sum_prob = summary_df["Probability"].sum()
if sum_prob > 0:
    expected_land_value = (summary_df["Land_Value"] * summary_df["Probability"]).sum()
else:
    expected_land_value = 0
summary_df["Land_Value"] = summary_df["Land_Value"].apply(lambda x: f"${x:,.0f}")
summary_df["NOI"] = summary_df["NOI"].apply(lambda x: f"${x:,.0f}")
summary_df["Exit_Value"] = summary_df["Exit_Value"].apply(lambda x: f"${x:,.0f}")
st.dataframe(summary_df)

st.subheader("📌 Probability-Weighted Land Value")
st.success(f"Expected Land Value: ${expected_land_value:,.0f}")

