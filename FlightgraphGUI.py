import streamlit as st
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from Flightgraph import (
    load_flight_data,
    find_direct_flights,
    find_indirect_flights,
    build_direct_flight_graph,
    build_indirect_flight_graph
)

# Page configuration
st.set_page_config(
    page_title="Flight Graph Finder",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title and description
st.title("✈️ Flight Graph Finder")
st.markdown("---")
st.markdown("Find direct and indirect flight routes between cities with real-time data visualization.")

# Load data
@st.cache_data
def get_flight_data():
    """Load flight data from API with caching."""
    return load_flight_data()

# Automatically load flight data
with st.spinner("Loading flight data..."):
    data = get_flight_data()
    if data is None:
        st.error("❌ Failed to load flight data. Please check your internet connection.")
        st.stop()

# Sidebar configuration
with st.sidebar:
    st.markdown("---")
    st.markdown(
        """
        ### How to use:
        1. Select search type (Direct/Indirect)
        2. Enter origin and destination cities
        3. Click search to view results and visualizations
        """
    )

# Create tabs for different search types
tab1, tab2 = st.tabs(["🛫 Direct Flights", "🔄 Indirect Flights (1 Stop)"])
    
# TAB 1: DIRECT FLIGHTS
with tab1:
    st.subheader("Find Direct Flights")
    
    col1, col2 = st.columns(2)
    with col1:
        origin_direct = st.text_input(
            "Origin City",
            placeholder="e.g., New York",
            key="origin_direct"
        ).strip()
    
    with col2:
        destination_direct = st.text_input(
            "Destination City",
            placeholder="e.g., Los Angeles",
            key="dest_direct"
        ).strip()
    
    if st.button("🔍 Search Direct Flights", use_container_width=True):
        if origin_direct and destination_direct:
            with st.spinner("Searching for direct flights..."):
                direct_flights = find_direct_flights(
                    data,
                    origin_direct,
                    destination_direct
                )
        
        if direct_flights:
            st.success(f"✅ Found {len(direct_flights)} direct flight(s)")
            
            # Display flights in a table
            flights_df = pd.DataFrame([
                {
                    'From': flight['from'],
                    'To': flight['to'],
                    'Fare': f"${flight['fare']:.2f}"
                }
                for flight in direct_flights
            ])
            
            st.dataframe(flights_df, use_container_width=True)
            
            # Visualize graph
            if len(direct_flights) > 0:
                st.subheader("Flight Network Visualization")
                try:
                    graph = build_direct_flight_graph(direct_flights)
                    
                    # Create visualization
                    fig, ax = plt.subplots(figsize=(12, 8))
                    pos = nx.fruchterman_reingold_layout(graph, k=0.5, iterations=100)
                    
                    # Draw graph
                    nx.draw(
                        graph,
                        pos=pos,
                        with_labels=True,
                        node_color='lightblue',
                        node_size=1500,
                        font_size=10,
                        arrows=True,
                        edge_color='gray',
                        ax=ax
                    )
                    
                    # Add edge labels (fares)
                    edge_labels = nx.get_edge_attributes(graph, "weight")
                    edge_labels = {k: f'${v:.2f}' for k, v in edge_labels.items()}
                    nx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_labels, ax=ax)
                    
                    ax.set_title(f"Direct Flights: {origin_direct} → {destination_direct}")
                    ax.axis('off')
                    plt.tight_layout()
                    
                    st.pyplot(fig)
                except Exception as e:
                    st.error(f"Error creating visualization: {e}")
        else:
            st.error(f"❌ No direct flights found from {origin_direct} to {destination_direct}")
    else:
        st.error("Please enter both origin and destination cities")

# TAB 2: INDIRECT FLIGHTS
with tab2:
    st.subheader("Find Indirect Flights (with 1 connection)")
    
    col1, col2 = st.columns(2)
    with col1:
        origin_indirect = st.text_input(
            "Origin City",
            placeholder="e.g., New York",
            key="origin_indirect"
        ).strip()
    
    with col2:
        destination_indirect = st.text_input(
            "Destination City",
            placeholder="e.g., Los Angeles",
            key="dest_indirect"
        ).strip()
    
    if st.button("🔍 Search Indirect Flights", use_container_width=True):
        if origin_indirect and destination_indirect:
            with st.spinner("Searching for indirect flights..."):
                indirect_flights = find_indirect_flights(
                    data,
                    origin_indirect,
                    destination_indirect
                )
        
        if indirect_flights:
            st.success(f"✅ Found {len(indirect_flights)} indirect flight route(s)")
            
            # Display flights in a table
            flights_df = pd.DataFrame([
                {
                    'Leg 1 From': flight['leg1_from'],
                    'Leg 1 To': flight['leg1_to'],
                    'Leg 1 Fare': f"${flight['leg1_fare']:.2f}",
                    'Leg 2 From': flight['leg2_from'],
                    'Leg 2 To': flight['leg2_to'],
                    'Leg 2 Fare': f"${flight['leg2_fare']:.2f}",
                    'Total Fare': f"${flight['total_fare']:.2f}"
                }
                for flight in indirect_flights
            ])
            
            st.dataframe(flights_df, use_container_width=True)
            
            # Visualize graph
            if len(indirect_flights) > 0:
                st.subheader("Flight Network Visualization")
                try:
                    graph = build_indirect_flight_graph(indirect_flights)
                    
                    # Create visualization
                    fig, ax = plt.subplots(figsize=(12, 8))
                    pos = nx.fruchterman_reingold_layout(graph, k=0.5, iterations=100)
                    
                    # Draw graph
                    nx.draw(
                        graph,
                        pos=pos,
                        with_labels=True,
                        node_color='lightgreen',
                        node_size=1500,
                        font_size=10,
                        arrows=True,
                        edge_color='gray',
                        ax=ax
                    )
                    
                    # Add edge labels (fares)
                    edge_labels = nx.get_edge_attributes(graph, "weight")
                    edge_labels = {k: f'${v:.2f}' for k, v in edge_labels.items()}
                    nx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_labels, ax=ax)
                    
                    ax.set_title(f"Indirect Flights: {origin_indirect} → {destination_indirect}")
                    ax.axis('off')
                    plt.tight_layout()
                    
                    st.pyplot(fig)
                except Exception as e:
                    st.error(f"Error creating visualization: {e}")
        else:
            st.error(f"❌ No indirect flights found from {origin_indirect} to {destination_indirect}")
    else:
        st.error("Please enter both origin and destination cities")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center'>
        <p>Flight Graph Finder • Powered by Streamlit • Data Source: Transportation.gov</p>
    </div>
    """,
    unsafe_allow_html=True
)
