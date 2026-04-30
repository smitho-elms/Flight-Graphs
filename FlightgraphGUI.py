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
                    
                    # Creates tiered layout to improve readability of indirect flights
                    fig, ax = plt.subplots(figsize=(14, 8))
                    
                    # Separates nodes into layers: origin, stopover, destination
                    all_nodes = set(graph.nodes())
                    leg1_edges = [(u, v) for u, v, d in graph.edges(data=True) if d.get('leg') == 'leg1']
                    leg2_edges = [(u, v) for u, v, d in graph.edges(data=True) if d.get('leg') == 'leg2']
                    
                    # Separates unique cities into layers
                    layer1_nodes = set(u for u, v in leg1_edges)
                    layer3_nodes = set(v for u, v in leg2_edges)
                    layer2_nodes = all_nodes - layer1_nodes - layer3_nodes
                    
                    # Create tiered positions
                    pos = {}
                    x_spacing = 1
                    y_spacing = 0.8
                    
                    # Layer 1 (Origins)
                    for i, node in enumerate(sorted(layer1_nodes)):
                        pos[node] = (0, i * y_spacing - len(layer1_nodes) * y_spacing / 2)
                    
                    # Layer 2 (Stopovers)
                    for i, node in enumerate(sorted(layer2_nodes)):
                        pos[node] = (x_spacing, i * y_spacing - len(layer2_nodes) * y_spacing / 2)
                    
                    # Layer 3 (Destinations)
                    for i, node in enumerate(sorted(layer3_nodes)):
                        pos[node] = (2 * x_spacing, i * y_spacing - len(layer3_nodes) * y_spacing / 2)
                    
                    # Adds Color coding for layers and edges
                    nx.draw_networkx_nodes(graph, pos, nodelist=layer1_nodes, 
                                          node_color='#FF6B6B', node_size=2000, 
                                          label='Origin', ax=ax)
                    nx.draw_networkx_nodes(graph, pos, nodelist=layer2_nodes,
                                          node_color='#FFA500', node_size=2000,
                                          label='Stopover', ax=ax)
                    nx.draw_networkx_nodes(graph, pos, nodelist=layer3_nodes,
                                          node_color='#4ECDC4', node_size=2000,
                                          label='Destination', ax=ax)
                    
                    # Adds color-coded edges for leg 1 and leg 2
                    nx.draw_networkx_edges(graph, pos, edgelist=leg1_edges,
                                          edge_color='#FF6B6B', width=2.5, alpha=0.7,
                                          arrowsize=20, arrowstyle='->', ax=ax, label='Leg 1')
                    nx.draw_networkx_edges(graph, pos, edgelist=leg2_edges,
                                          edge_color='#4ECDC4', width=2.5, alpha=0.7,
                                          arrowsize=20, arrowstyle='->', ax=ax, label='Leg 2')
                    
                    # Draw labels
                    nx.draw_networkx_labels(graph, pos, font_size=9, font_weight='bold', ax=ax)
                    
                    # Add edge labels for fares, separated by leg
                    leg1_labels = {(u, v): f"${d['fare']:.0f}" 
                                  for u, v, d in graph.edges(data=True) if d.get('leg') == 'leg1'}
                    leg2_labels = {(u, v): f"${d['fare']:.0f}" 
                                  for u, v, d in graph.edges(data=True) if d.get('leg') == 'leg2'}
                    
                    nx.draw_networkx_edge_labels(graph, pos, edge_labels=leg1_labels, 
                                                font_size=8, ax=ax, font_color='#FF6B6B')
                    nx.draw_networkx_edge_labels(graph, pos, edge_labels=leg2_labels,
                                                font_size=8, ax=ax, font_color='#4ECDC4')
                    
                    ax.set_title(f"Indirect Flights: {origin_indirect} → {destination_indirect}\n(Tiered Layout)", 
                                fontsize=14, fontweight='bold', pad=20)
                    ax.axis('off')
                    ax.legend(loc='upper left', fontsize=10, framealpha=0.9)
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
