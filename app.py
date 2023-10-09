import streamlit as st
from libs.tools import *
from libs.graph_route import plot_graph_route
import networkx as nx
import osmnx as ox
from datetime import datetime
from network import Network
from network.algorithms.eulerian import hierholzer
# from network.network.algorithms.eulerian import hierholzer
from libs.tools import *
from libs.gpx_formatter import TEMPLATE, TRACE_POINT

import geopandas as gpd

# Configuration
ox.config(use_cache=True, log_console=True)
CUSTOM_FILTER = (
    '["highway"]["area"!~"yes"]["highway"!~"bridleway|bus_guideway|bus_stop|construction|cycleway|elevator|footway|'
    'motorway|motorway_junction|motorway_link|escalator|proposed|construction|platform|raceway|rest_area|'
    'path|service"]["access"!~"customers|no|private"]["public_transport"!~"platform"]'
    '["fee"!~"yes"]["foot"!~"no"]["service"!~"drive-through|driveway|parking_aisle"]["toll"!~"yes"]'
)

def compute_route(location):
    # https://github.com/matejker/everystreet/issues/6
    org_graph = ox.graph_from_place(location, custom_filter=CUSTOM_FILTER)


    # Simplifying the original directed multi-graph to undirected, so we can go both ways in one way streets
    graph = ox.utils_graph.get_undirected(org_graph)
    fig, ax = ox.plot_graph(graph, node_zorder=2, node_color="k", bgcolor="w")


    # Finds the odd degree nodes and minimal matching
    odd_degree_nodes = get_odd_degree_nodes(graph)
    pair_weights = get_shortest_distance_for_odd_degrees(graph, odd_degree_nodes)
    matched_edges_with_weights = min_matching(pair_weights)

    # List all edges of the extended graph including original edges and edges from minimal matching
    single_edges = [(u, v) for u, v, k in graph.edges]
    added_edges = get_shortest_paths(graph, matched_edges_with_weights)
    edges = map_osmnx_edges2integers(graph, single_edges + added_edges)

    # Finds the Eulerian path
    network = Network(len(graph.nodes), edges, weighted=True)
    eulerian_path = hierholzer(network)
    converted_eulerian_path = convert_integer_path2osmnx_nodes(eulerian_path, graph.nodes())
    double_edge_heap = get_double_edge_heap(org_graph)

    # Finds the final path with edge IDs
    final_path = convert_path(graph, converted_eulerian_path, double_edge_heap)
    coordinates_path = convert_final_path_to_coordinates(org_graph, final_path)

    if nx.is_weakly_connected(org_graph):
        center_nodes = nx.center(org_graph.to_undirected())
    else:
        center_nodes = nx.center(org_graph)
        
    center_node = org_graph.nodes[center_nodes[0]]  


    trace_points = "\n\t\t\t".join([TRACE_POINT.format(
        lat=lat, lon=lon, id=i, timestamp=datetime.now().isoformat()
    ) for i, (lat, lon) in enumerate(coordinates_path)])

    gpx_payload = TEMPLATE.format(
        name="Name your everystreet route",
        trace_points=trace_points,
        center_lat=center_node["y"],
        center_lon=center_node["x"]
    )

    # with open("gpx_output.gpx", "w") as f:
    #     f.write(gpx_payload)
    return gpx_payload, fig

# Streamlit Interface
st.title("EveryStreet Route Calculator")

location = st.text_input("Enter a location:", "The Grange, Edinburgh, Scotland")

if st.button('Compute Route'):
    gpx_payload, route_fig = compute_route(location)
    
    # Display the result figure
    st.pyplot(route_fig)
    
    # Provide the gpx_payload for download (if desired)
    st.text_area("GPX Output:", gpx_payload)
    # ... maybe add a download button or other UI elements as needed
    
    # Assuming gpx_payload contains the content of your GPX file

    st.download_button(
        label="Download GPX file",
        data=gpx_payload.encode(),
        file_name="gpx_output.gpx",
        mime="application/gpx+xml"
)

