import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt


def load_flight_data():
    """Load flight data from the API."""
    try:
        data = pd.read_json("https://data.transportation.gov/resource/4f3n-jbg2.json?year=2025")
        return data
    except Exception as e:
        print(f"Error loading flight data: {e}")
        return None


def find_direct_flights(data, origin_city, destination_city):
    """Find direct flights between two cities (in either direction)."""
    flights = []
    for index, row in data.iterrows():
        city1 = row['city1']
        city2 = row['city2']
        fare = row['fare']
        
        # Check forward direction (city1 -> city2)
        if origin_city.lower() in city1.lower() and destination_city.lower() in city2.lower():
            flights.append({
                'from': city1,
                'to': city2,
                'fare': fare
            })
        # Check reverse direction (city2 -> city1)
        elif destination_city.lower() in city1.lower() and origin_city.lower() in city2.lower():
            flights.append({
                'from': city1,
                'to': city2,
                'fare': fare
            })
    
    return flights


def find_indirect_flights(data, origin_city, destination_city):
    """Find indirect flights (one connection) between two cities (in either direction)."""
    flights = []
    
    # First, find all flights from origin city
    origin_flights = []
    for index1, row1 in data.iterrows():
        city1_leg1 = row1['city1']
        city2_leg1 = row1['city2']
        fare_leg1 = row1['fare']
        
        # Check forward: origin -> intermediate
        if origin_city.lower() in city1_leg1.lower():
            origin_flights.append({
                'from': city1_leg1,
                'to': city2_leg1,
                'fare': fare_leg1,
                'original_row': index1
            })
        # Check reverse: intermediate -> origin
        elif origin_city.lower() in city2_leg1.lower():
            origin_flights.append({
                'from': city2_leg1,
                'to': city1_leg1,
                'fare': fare_leg1,
                'original_row': index1
            })
    
    # Then, find connecting flights to destination
    for origin_flight in origin_flights:
        intermediate = origin_flight['to']
        
        for index2, row2 in data.iterrows():
            city1_leg2 = row2['city1']
            city2_leg2 = row2['city2']
            fare_leg2 = row2['fare']
            
            # Check forward: intermediate -> destination
            if intermediate.lower() in city1_leg2.lower() and destination_city.lower() in city2_leg2.lower():
                flights.append({
                    'leg1_from': origin_flight['from'],
                    'leg1_to': origin_flight['to'],
                    'leg1_fare': origin_flight['fare'],
                    'leg2_from': city1_leg2,
                    'leg2_to': city2_leg2,
                    'leg2_fare': fare_leg2,
                    'total_fare': origin_flight['fare'] + fare_leg2
                })
            # Check reverse: destination -> intermediate
            elif destination_city.lower() in city1_leg2.lower() and intermediate.lower() in city2_leg2.lower():
                flights.append({
                    'leg1_from': origin_flight['from'],
                    'leg1_to': origin_flight['to'],
                    'leg1_fare': origin_flight['fare'],
                    'leg2_from': city1_leg2,
                    'leg2_to': city2_leg2,
                    'leg2_fare': fare_leg2,
                    'total_fare': origin_flight['fare'] + fare_leg2
                })
    
    return flights


def build_direct_flight_graph(flights):
    G = nx.DiGraph()
    for flight in flights:
        G.add_edge(flight['from'], flight['to'], weight=flight['fare'])
    return G


def build_indirect_flight_graph(flights):
    G = nx.DiGraph()
    for flight in flights:
        G.add_edge(flight['leg1_from'], flight['leg1_to'], weight=flight['leg1_fare'])
        G.add_edge(flight['leg2_from'], flight['leg2_to'], weight=flight['leg2_fare'])
        if not G.has_edge(flight['leg1_from'], flight['leg2_to']):
            G.add_edge(flight['leg1_from'], flight['leg2_to'], weight=flight['total_fare'])
    return G


def visualize_graph(graph, origin, destination, flight_type="Direct"):
    if not graph.number_of_nodes():
        return
    
    plt.figure(figsize=(12, 8))
    pos = nx.fruchterman_reingold_layout(graph, k=0.5, iterations=100)
    
    nx.draw(graph, pos=pos, with_labels=True, node_color='lightblue', 
            node_size=1500, font_size=10, arrows=True, edge_color='gray')
    
    edge_labels = nx.get_edge_attributes(graph, "weight")
    edge_labels = {k: f'${v:.2f}' for k, v in edge_labels.items()}
    nx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_labels)
    
    plt.title(f"{flight_type} Flights from {origin} to {destination}")
    plt.axis('off')
    plt.tight_layout()
    plt.show()


def display_flights(flights, flight_type="Direct"):
    if not flights:
        return False
    
    print(f"\n{'='*60}")
    print(f"{flight_type} Flights Found: {len(flights)}")
    print(f"{'='*60}")
    
    if flight_type == "Direct":
        for i, flight in enumerate(flights, 1):
            print(f"{i}. {flight['from']} → {flight['to']}")
            print(f"   Fare: ${flight['fare']:.2f}\n")
    else:  # Indirect
        for i, flight in enumerate(flights, 1):
            print(f"{i}. {flight['leg1_from']} → {flight['leg1_to']} (${flight['leg1_fare']:.2f})")
            print(f"   then {flight['leg2_from']} → {flight['leg2_to']} (${flight['leg2_fare']:.2f})")
            print(f"   Total Fare: ${flight['total_fare']:.2f}\n")
    
    return True


def main():
    """Main program flow."""
    print("Flight Path Finder")
    print("=" * 60)
    
    # Load data
    data = load_flight_data()
    if data is None:
        print("Failed to load flight data. Exiting.")
        return
    
    # Search for direct flights
    print("\n--- DIRECT FLIGHTS SEARCH ---")
    origin = input("Enter the origin city: ").strip()
    destination = input("Enter the destination city: ").strip()
    
    direct_flights = find_direct_flights(data, origin, destination)
    if display_flights(direct_flights, "Direct"):
        graph = build_direct_flight_graph(direct_flights)
        visualize_graph(graph, origin, destination, "Direct")
    else:
        print(f"No direct flights found between {origin} and {destination}.")
    
    # Search for indirect flights
    print("\n--- INDIRECT FLIGHTS SEARCH ---")
    origin = input("Enter the origin city: ").strip()
    destination = input("Enter the destination city: ").strip()
    
    indirect_flights = find_indirect_flights(data, origin, destination)
    if display_flights(indirect_flights, "Indirect"):
        graph = build_indirect_flight_graph(indirect_flights)
        visualize_graph(graph, origin, destination, "Indirect")
    else:
        print(f"No indirect flights found between {origin} and {destination}.")


if __name__ == "__main__":
    main()