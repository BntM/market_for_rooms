import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
if __name__ == "__main__" and __package__ is None:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from market_simulator import RoomMarketSimulator
else:
    from .market_simulator import RoomMarketSimulator

st.set_page_config(page_title="Enterprise Market Playground", layout="wide")

st.title("🏛️ Enterprise Pricing Playground")
st.markdown("""
Use this dashboard to simulate agent behaviors and tune your market parameters **before** launching to real students.
""")

# Sidebar Controls
st.sidebar.header("Market Parameters")
base_price = st.sidebar.slider("Base Room Price (Tokens)", 5, 50, 10)
token_drip = st.sidebar.slider("Daily Token Allocation", 0, 20, 5)
num_agents = st.sidebar.number_input("Number of Student Agents", 50, 500, 100)

st.sidebar.subheader("Location Multipliers")
w_library = st.sidebar.slider("Library", 0.5, 3.0, 1.3)
w_student_center = st.sidebar.slider("Student Center", 0.5, 3.0, 1.2)
w_engineering = st.sidebar.slider("Engineering Hall", 0.5, 3.0, 1.1)

st.sidebar.subheader("Capacity Multipliers")
w_small = st.sidebar.slider("Small (2 person)", 0.5, 3.0, 1.0)
w_medium = st.sidebar.slider("Medium (4 person)", 0.5, 3.0, 1.4)
w_large = st.sidebar.slider("Large (10 person)", 0.5, 3.0, 2.5)

# Run Simulation
if st.button("🚀 Run Market Simulation"):
    sim = RoomMarketSimulator(base_price=base_price)
    sim.setup_rooms(num_rooms=40)
    sim.setup_agents(num_agents=num_agents)
    
    weights = {
        "location": {
            "Library": w_library,
            "Student Center": w_student_center,
            "Engineering Hall": w_engineering
        },
        "capacity": {
            "2": w_small,
            "4": w_medium,
            "10": w_large
        }
    }
    
    with st.spinner("Simulating students..."):
        df = sim.run_simulation(days=14, weights=weights, token_drip=token_drip)
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Bookings", len(df))
    col2.metric("Avg Price Paid", f"{df['price_paid'].mean():.2f} ₮")
    col3.metric("Total Token Volume", f"{df['price_paid'].sum():.0f} ₮")
    col4.metric("Market Efficiency", f"{(len(df)/(40*14))*100:.1f}%")

    # Visualizations
    st.subheader("Booking Trends over 14-Day Cycle")
    
    # 1. Price vs TTE
    fig_price = px.scatter(df, x="tte", y="price_paid", color="agent_type", 
                          title="Price Paid vs. Days Until Slot (Airline Curve Test)",
                          labels={"tte": "Days Remaining", "price_paid": "Price (Tokens)"})
    st.plotly_chart(fig_price, use_container_width=True)
    
    # 2. Daily Occupancy
    daily_stats = df.groupby('day').size().reset_index(name='bookings')
    fig_occupancy = px.bar(daily_stats, x='day', y='bookings', title="Daily Booking Volume")
    st.plotly_chart(fig_occupancy, use_container_width=True)
    
    # 3. Agent Segment Analysis
    col_a, col_b = st.columns(2)
    
    agent_stats = df.groupby('agent_type')['price_paid'].mean().reset_index()
    fig_agent = px.pie(df, names='agent_type', title="Market Share by Agent Type")
    col_a.plotly_chart(fig_agent, use_container_width=True)
    
    fig_box = px.box(df, x="agent_type", y="price_paid", title="Price Tolerance by Agent Segment")
    col_b.plotly_chart(fig_box, use_container_width=True)

    # Raw Data
    with st.expander("View Simulation Logs"):
        st.dataframe(df)

else:
    st.info("Adjust the parameters in the sidebar and click 'Run' to see how your pricing strategy performs.")
    
    # Show theoretical curve
    st.subheader("Theoretical Price Curve (Visualized)")
    tte_range = list(range(0, 15))
    theoretical_prices = []
    for tte in tte_range:
        # Dummy room for visualization
        room = {"location": "Library", "capacity": 4}
        weights = {"location": {"Library": 1.0}, "capacity": {"4": 1.0}}
        price = RoomMarketSimulator(base_price=10).calculate_price(room, tte, weights, 0.5)
        theoretical_prices.append(price)
        
    fig_theory = px.line(x=tte_range, y=theoretical_prices, 
                        title="Your U-Curve Configuration (Base Room)",
                        labels={"x": "Days Remaining (TTE)", "y": "Price (Tokens)"})
    fig_theory.update_traces(line_color='#FF4B4B')
    st.plotly_chart(fig_theory, use_container_width=True)
