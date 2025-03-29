 # Land Valuation Streamlit App – Solve for Land Price to Meet Target IRR
import streamlit as st
import numpy as np
import numpy_financial as npf
from scipy.optimize import minimize_scalar

def calculate_irr_based_land_value(
    lot_size_sqft,
    far,
    apartment_size_sqft,
    rent_per_unit_monthly,
    vacancy_rate,
    opex_ratio,
    hard_cost_per_sqft,
    soft_cost_ratio,
    cap_rate,
    hold_years,
    annual_rent_growth,
    exit_cap_rate,
    equity_ratio,
    target_irr
):
    buildable_sqft = lot_size_sqft * far
    num_units = int(buildable_sqft // apartment_size_sqft)
    hard_costs = buildable_sqft * hard_cost_per_sqft
    soft_costs = hard_costs * soft_cost_ratio
    total_construction_costs = hard_costs + soft_costs

    gross_rent_annual = rent_per_unit_monthly * 12 * num_units
    effective_gross_income = gross_rent_annual * (1 - vacancy_rate)
    operating_expenses = effective_gross_income * opex_ratio
    noi = effective_gross_income - operating_expenses

    noi_exit = noi * ((1 + annual_rent_growth) ** hold_years)
    exit_value = noi_exit / exit_cap_rate

    def irr_error(land_cost):
        total_costs = total_construction_costs + land_cost
        equity_investment = total_costs * equity_ratio
        annual_cash_flows = [0] * hold_years
        for i in range(hold_years):
            noi_year = noi * ((1 + annual_rent_growth) ** i)
            cash_flow = noi_year * equity_ratio
            annual_cash_flows[i] = cash_flow
        annual_cash_flows[-1] += exit_value
        irr = npf.irr([-equity_investment] + annual_cash_flows)
        return abs(irr - target_irr)

    result = minimize_scalar(irr_error, bounds=(0, 50_000_000), method='bounded')
    best_land_price = result.x
    achieved_irr = target_irr if result.success else None

    stabilized_value = noi / cap_rate

    return {
        "Buildable SqFt": buildable_sqft,
        "Number of Units": num_units,
        "Hard Costs": hard_costs,
        "Soft Costs": soft_costs,
        "Total Construction Costs": total_construction_costs,
        "NOI (Year 1)": noi,
        "Exit Value": exit_value,
        "Land Price to Achieve Target IRR": best_land_price,
        "Achieved IRR": achieved_irr,
        "Stabilized Value": stabilized_value,
        "Total Project Cost": total_construction_costs + best_land_price
    }

st.title("🧮 Land Price Estimator Based on Target IRR")

st.sidebar.header("Input Assumptions")
lot_size_sqft = st.sidebar.number_input("Lot Size (sqft)", value=10000)
far = st.sidebar.number_input("FAR (Floor Area Ratio)", value=3.0)
apartment_size_sqft = st.sidebar.number_input("Avg Apartment Size (sqft)", value=1000)
rent_per_unit_monthly = st.sidebar.number_input("Monthly Rent per Unit ($)", value=2800)
vacancy_rate = st.sidebar.slider("Vacancy Rate (%)", 0.0, 0.2, 0.05)
opex_ratio = st.sidebar.slider("Operating Expenses (% of EGI)", 0.0, 1.0, 0.35)
hard_cost_per_sqft = st.sidebar.number_input("Hard Cost per SqFt ($)", value=300)
soft_cost_ratio = st.sidebar.slider("Soft Costs (% of Hard Costs)", 0.0, 1.0, 0.25)
cap_rate = st.sidebar.slider("Cap Rate (%)", 0.02, 0.10, 0.05)
hold_years = st.sidebar.number_input("Hold Period (Years)", value=10)
annual_rent_growth = st.sidebar.slider("Annual Rent Growth (%)", 0.00, 0.10, 0.02)
exit_cap_rate = st.sidebar.slider("Exit Cap Rate (%)", 0.02, 0.10, 0.05)
equity_ratio = st.sidebar.slider("Equity Investment Ratio", 0.1, 1.0, 0.3)
target_irr = st.sidebar.slider("Target IRR (%)", 0.05, 0.30, 0.18)

# Auto-run calculation
results = calculate_irr_based_land_value(
    lot_size_sqft,
    far,
    apartment_size_sqft,
    rent_per_unit_monthly,
    vacancy_rate,
    opex_ratio,
    hard_cost_per_sqft,
    soft_cost_ratio,
    cap_rate,
    hold_years,
    annual_rent_growth,
    exit_cap_rate,
    equity_ratio,
    target_irr
)

st.subheader("📊 Results")
for key, value in results.items():
    if "IRR" in key:
        st.write(f"**{key}:** {value * 100:.2f}%")
    elif "Land Price" in key and isinstance(value, float):
        st.write(f"**{key}:** ${value:,.2f}")
    elif isinstance(value, float):
        st.write(f"**{key}:** ${value:,.2f}")
    else:
        st.write(f"**{key}:** {value}")
