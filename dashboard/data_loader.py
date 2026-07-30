import pandas as pd
import streamlit as st
import os

# Base directory for data
DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
    "data", 
    "processed"
)

@st.cache_data
def load_csv(filename):
    """Load a CSV file from the processed data directory and cache it."""
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        st.error(f"File not found: {filepath}")
        return pd.DataFrame()
    
    # We use low_memory=False to prevent dtype warnings for large files
    return pd.read_csv(filepath, low_memory=False)

@st.cache_data
def load_core_data():
    """Load and merge core dimensions and facts for the dashboard."""
    # Load Dimensions
    dim_date = load_csv("dim_date.csv")
    dim_customer = load_csv("dim_customers.csv")
    dim_product = load_csv("dim_products.csv")
    dim_channel = load_csv("dim_channels.csv")
    dim_geo = load_csv("dim_geography.csv")
    
    # Ensure DateKey is integer for joining
    dim_date['DateKey'] = pd.to_numeric(dim_date['DateKey'], errors='coerce')
    dim_date['FullDate'] = pd.to_datetime(dim_date['FullDate'])
    
    # Load Facts
    fact_orders = load_csv("fact_orders.csv")
    fact_order_lines = load_csv("fact_order_lines.csv")
    
    # Date keys in facts
    if 'OrderDateKey' in fact_orders.columns:
        fact_orders['OrderDateKey'] = pd.to_numeric(fact_orders['OrderDateKey'], errors='coerce')
    
    # Provide a unified merged order table for easier aggregations
    orders_merged = fact_orders.merge(dim_date, left_on="OrderDateKey", right_on="DateKey", how="left")
    
    if not dim_channel.empty and 'ChannelId' in orders_merged.columns:
        orders_merged = orders_merged.merge(dim_channel, on="ChannelId", how="left")
        
    return {
        "dim_date": dim_date,
        "dim_customer": dim_customer,
        "dim_product": dim_product,
        "dim_geo": dim_geo,
        "dim_channel": dim_channel,
        "fact_orders": fact_orders,
        "fact_order_lines": fact_order_lines,
        "orders_merged": orders_merged
    }

@st.cache_data
def load_retention_data():
    """Load retention specific pre-aggregated data"""
    return load_csv("cohort_retention.csv")

@st.cache_data
def load_rfm_data():
    return load_csv("rfm_segments.csv")
