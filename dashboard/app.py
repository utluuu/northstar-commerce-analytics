import streamlit as st

st.set_page_config(
    page_title="Northstar Commerce Analytics",
    page_icon="⭐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom premium CSS injection
st.markdown("""
<style>
    /* Dark Premium Theme CSS */
    :root {
        --primary: #2563EB;
        --profit: #0F766E;
        --attention: #D97706;
        --bg-color: #0F172A;
        --card-bg: #1E293B;
        --text-main: #F8FAFC;
        --text-muted: #94A3B8;
    }
    
    /* Background and typography */
    .stApp {
        background-color: var(--bg-color);
        color: var(--text-main);
        font-family: 'Inter', 'Segoe UI', Roboto, sans-serif;
    }
    
    /* Hide top header and footer for app feel */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Metric Cards Glassmorphism */
    div[data-testid="metric-container"] {
        background-color: var(--card-bg);
        border: 1px solid rgba(255,255,255,0.1);
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        border-color: rgba(255,255,255,0.2);
    }
    
    /* Adjust text colors inside metrics */
    div[data-testid="stMetricValue"] {
        color: var(--text-main);
        font-size: 2.2rem;
        font-weight: 700;
    }
    div[data-testid="stMetricLabel"] {
        color: var(--text-muted);
        font-size: 1rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Chart Containers */
    div[data-testid="stPlotlyChart"] {
        background-color: var(--card-bg);
        border: 1px solid rgba(255,255,255,0.05);
        border-radius: 12px;
        padding: 10px;
    }

    h1, h2, h3 {
        color: var(--text-main) !important;
    }
    
    hr {
        border-color: rgba(255,255,255,0.1);
    }
</style>
""", unsafe_allow_html=True)

st.title("⭐ Northstar Commerce Analytics")
st.markdown("Welcome to the **Premium Analytical Dashboard**. Please select a page from the sidebar to begin.")

# Navigation is handled natively if files are in the `pages/` directory.
