import streamlit as st
import plotly.express as px
import pandas as pd

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_loader import load_core_data, load_retention_data, load_rfm_data

st.set_page_config(page_title="Customer Analytics", page_icon="👥", layout="wide")

st.markdown("## Customer Analytics — Retention, Value, and Churn Risk")
st.markdown("---")

with st.spinner("Loading Data..."):
    data = load_core_data()
    retention = load_retention_data()
    rfm = load_rfm_data()

dim_customer = data["dim_customer"]
if dim_customer.empty:
    st.warning("No data found to display.")
    st.stop()

# ----------------- KPIs -----------------
active = dim_customer[dim_customer['LifecycleStatus'] == 'Active'].shape[0]
at_risk = dim_customer[dim_customer['LifecycleStatus'].isin(['At Risk', 'High Risk'])].shape[0]
avg_clv = dim_customer['LifetimeRevenueAfterRefund'].mean()

col1, col2, col3 = st.columns(3)
col1.metric("Active Customers", f"{active:,.0f}")
col2.metric("At Risk Customers", f"{at_risk:,.0f}")
col3.metric("Average CLV", f"${avg_clv:,.2f}")
st.markdown("<br>", unsafe_allow_html=True)

# ----------------- CHARTS -----------------
dark_template = "plotly_dark"
c1, c2 = st.columns(2)

with c1:
    st.markdown("### Lifecycle Status Distribution")
    dist = dim_customer['LifecycleStatus'].value_counts().reset_index()
    dist.columns = ['Status', 'Count']
    fig1 = px.pie(dist, names="Status", values="Count", hole=0.4,
                  template=dark_template, color_discrete_sequence=px.colors.qualitative.Pastel)
    fig1.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig1, use_container_width=True)

with c2:
    st.markdown("### RFM Segments")
    if not rfm.empty:
        rfm_agg = rfm.groupby('RfmSegment')['CustomerId'].nunique().reset_index()
        fig2 = px.bar(rfm_agg, y="RfmSegment", x="CustomerId", orientation='h',
                      template=dark_template, color_discrete_sequence=["#D97706"])
        fig2.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("RFM data not found.")

st.markdown("### Cohort Retention")
if not retention.empty:
    # Build a pivot table for retention heat map if format allows
    try:
        pivot = retention.pivot(index="CohortMonth", columns="MonthsSinceFirstOrder", values="RetentionPercentage")
        fig3 = px.imshow(pivot, template=dark_template, color_continuous_scale="Blues", aspect="auto")
        fig3.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig3, use_container_width=True)
    except Exception as e:
        st.dataframe(retention.head())
else:
    st.info("Retention data not found.")
