import streamlit as st
import plotly.express as px
import pandas as pd

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_loader import load_core_data

st.set_page_config(page_title="Sales Performance", page_icon="🛍️", layout="wide")

st.markdown("## Sales Performance — Trend, Channel, and Regional Drivers")
st.markdown("---")

with st.spinner("Loading Data..."):
    data = load_core_data()
    
orders_merged = data["orders_merged"]
if orders_merged.empty:
    st.warning("No data found to display.")
    st.stop()

# ----------------- FILTERS -----------------
st.sidebar.header("Filters")
regions = sorted(orders_merged['Region'].dropna().unique()) if 'Region' in orders_merged.columns else []
if regions:
    selected_region = st.sidebar.multiselect("Select Region", regions)
    if selected_region:
        orders_merged = orders_merged[orders_merged['Region'].isin(selected_region)]

orders_merged['YearMonth'] = orders_merged['FullDate'].dt.to_period('M').astype(str)

# ----------------- CHARTS -----------------
dark_template = "plotly_dark"

st.markdown("### Regional Channel Performance")
if 'Region' in orders_merged.columns and 'ChannelName' in orders_merged.columns:
    region_channel = orders_merged.groupby(['Region', 'ChannelName'])['RevenueAfterRefund'].sum().reset_index()
    fig1 = px.bar(region_channel, x="Region", y="RevenueAfterRefund", color="ChannelName", barmode="group",
                  template=dark_template, color_discrete_sequence=px.colors.qualitative.Prism)
    fig1.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig1, use_container_width=True)
else:
    st.info("Region or Channel data missing.")

st.markdown("### Daily Sales Trend (Last 30 Days)")
daily = orders_merged.groupby('FullDate')['RevenueAfterRefund'].sum().reset_index().tail(30)
fig2 = px.area(daily, x="FullDate", y="RevenueAfterRefund", template=dark_template,
               color_discrete_sequence=["#2563EB"])
fig2.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
st.plotly_chart(fig2, use_container_width=True)

st.markdown("### Detailed Monthly Table")
monthly = orders_merged.groupby('YearMonth').agg(
    Revenue=('RevenueAfterRefund', 'sum'),
    Orders=('OrderId', 'nunique')
).reset_index().sort_values('YearMonth', ascending=False)
st.dataframe(monthly, use_container_width=True)
