import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Fix path to load data_loader
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_loader import load_core_data

st.set_page_config(page_title="Executive Overview", page_icon="📈", layout="wide")

st.markdown("## Executive Overview — Growth, Profitability, and Customer Health")
st.markdown("---")

with st.spinner("Loading Data..."):
    data = load_core_data()
    
orders_merged = data["orders_merged"]
fact_orders = data["fact_orders"]

if orders_merged.empty:
    st.warning("No data found to display.")
    st.stop()

# ----------------- FILTERS -----------------
st.sidebar.header("Filters")
# Using Year-Month strings to simplify filtering
orders_merged['YearMonth'] = orders_merged['FullDate'].dt.to_period('M').astype(str)
months = sorted(orders_merged['YearMonth'].dropna().unique())
if months:
    selected_months = st.sidebar.multiselect("Select Month(s)", months, default=months[-6:] if len(months)>6 else months)
else:
    selected_months = []

filtered_orders = orders_merged[orders_merged['YearMonth'].isin(selected_months)] if selected_months else orders_merged

# ----------------- KPIs -----------------
# Calculate metrics
revenue = filtered_orders['RevenueAfterRefund'].sum()
profit = filtered_orders['GrossProfitAfterRefund'].sum()
margin = (profit / revenue * 100) if revenue > 0 else 0
total_orders = filtered_orders['OrderId'].nunique()
active_customers = filtered_orders['CustomerId'].nunique()
aov = (revenue / total_orders) if total_orders > 0 else 0

col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Revenue", f"${revenue:,.0f}")
col2.metric("Profit", f"${profit:,.0f}")
col3.metric("Margin", f"{margin:.1f}%")
col4.metric("Orders", f"{total_orders:,.0f}")
col5.metric("Customers", f"{active_customers:,.0f}")
col6.metric("AOV", f"${aov:,.2f}")

st.markdown("<br>", unsafe_allow_html=True)

# ----------------- CHARTS -----------------
# We define a common layout template for plotly to match the dark theme
dark_template = "plotly_dark"
color_discrete_sequence = ["#2563EB", "#0F766E", "#D97706", "#7C3AED", "#DC2626"]

c1, c2 = st.columns(2)

with c1:
    st.markdown("### Revenue Trend")
    trend = orders_merged.groupby('YearMonth')['RevenueAfterRefund'].sum().reset_index()
    fig1 = px.line(trend, x="YearMonth", y="RevenueAfterRefund", markers=True,
                   template=dark_template, color_discrete_sequence=["#2563EB"])
    fig1.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", margin=dict(l=20, r=20, t=30, b=20))
    st.plotly_chart(fig1, use_container_width=True)

with c2:
    st.markdown("### Revenue by Channel")
    if 'ChannelName' in filtered_orders.columns:
        chan = filtered_orders.groupby('ChannelName')['RevenueAfterRefund'].sum().reset_index()
        fig2 = px.bar(chan, x="ChannelName", y="RevenueAfterRefund", 
                      template=dark_template, color_discrete_sequence=["#0F766E"])
        fig2.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Channel data not available in merged dataset.")

st.markdown("### Category Contribution")
if not data["fact_order_lines"].empty and not data["dim_product"].empty:
    lines = data["fact_order_lines"]
    prods = data["dim_product"]
    merged_lines = lines.merge(prods, on="ProductId", how="left")
    cat = merged_lines.groupby("CategoryName")['NetRevenue'].sum().reset_index()
    fig3 = px.bar(cat, x="NetRevenue", y="CategoryName", orientation='h',
                  template=dark_template, color_discrete_sequence=["#7C3AED"])
    fig3.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", margin=dict(l=20, r=20, t=30, b=20))
    st.plotly_chart(fig3, use_container_width=True)
