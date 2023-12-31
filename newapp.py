
from flask import Flask, jsonify, render_template, request
# from flask_cors import CORS
import time

import xml.etree.ElementTree as ET
import json
import math
from typing import List, Tuple, Dict


start = time.time()

# Classes and Functions
class Node:
    def __init__(self, latitude: float, longitude: float, node_id: str):
        self.latitude = latitude
        
        self.longitude = longitude
        self.node_id = node_id

class NodeData:
    def __init__(self, lat: float, lon: float):
        self.lat = lat
        self.lon = lon

class Edge:
    def __init__(self, source: int, target: int):
        self.source = source
        self.target = target


def process_nodes(node, nodes, id_mapping, id_map, node_map):
    node_id = int(node.attrib["id"])
    latitude = float(node.attrib["lat"])
    longitude = float(node.attrib["lon"])
    new_node = Node(latitude, longitude, str(node_id))
    data_node = NodeData(latitude, longitude)
    node_map[node_id] = data_node
    nodes.append(new_node)
    id_mapping[node_id] = len(nodes) - 1

def process_ways(way, edges, id_mapping):
    prev_node_id = -1
    for nd in way.findall("nd"):
        node_id = int(nd.attrib["ref"])
        if prev_node_id != -1:
            edges.append(Edge(id_mapping[prev_node_id], id_mapping[node_id]))
        prev_node_id = node_id

def get_lat_lon_from_node_id(node_id, node_map):
    if node_id in node_map:
        node_data = node_map[node_id]
        return node_data.lat, node_data.lon
    else:
        return 0.0, 0.0  # Default values if node_id not found

def haversine_distance(source, target):
    PI = 3.14159265
    earth_radius = 6371.0  # Earth radius in kilometers

    lat1_rad = source.latitude * PI / 180.0
    lon1_rad = source.longitude * PI / 180.0
    lat2_rad = target.latitude * PI / 180.0
    lon2_rad = target.longitude * PI / 180.0

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = math.sin(dlat / 2) * math.sin(dlat / 2) + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) * math.sin(dlon / 2)

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return earth_radius * c  # Distance in kilometers

def dijkstra(graph, source, destination, num_nodes, nodes):
    if source < 0 or source >= num_nodes:
        print("Error: Invalid source index")
        return

    if destination < 0 or destination >= num_nodes:
        print("Error: Invalid destination index")
        return

    dist = [float('inf')] * num_nodes
    visited = [False] * num_nodes
    previous = [-1] * num_nodes

    dist[source] = 0

    for _ in range(num_nodes):
        min_index = -1
        min_dist = float('inf')

        for j in range(num_nodes):
            if not visited[j] and dist[j] < min_dist:
                min_dist = dist[j]
                min_index = j

        if min_index == destination:
            print(f"Shortest Distance: {dist[min_index]}")
            break
        if min_index == -1 or dist[min_index] == float('inf'):
            print("Error: No path found from source to destination")
            return jsonify({'error': 'No path found'})
        
        if min_index == -1:
            break

        visited[min_index] = True

        for k in range(num_nodes):
            if not visited[k] and graph[min_index][k] != 0 and dist[min_index] != float('inf') and dist[min_index] + graph[min_index][k] < dist[k]:
                dist[k] = dist[min_index] + graph[min_index][k]
                previous[k] = min_index

    # Reconstruct the path
    current = destination
    path = []
    while current != source:
        path.append(nodes[current].node_id)
        current = previous[current]

    path.append(nodes[source].node_id)
    path.reverse()

    return path

# def find_closest_node(nodes, latitude, longitude):
#     # print("Inside Closest Node:")
#     closest_node_id = -1
#     min_distance = float('inf')

#     for i, node in enumerate(nodes):
#         distance = haversine_distance(node, Node(latitude, longitude, ""))
#         if distance < min_distance:
#             min_distance = distance
#             closest_node_id = i

#     return closest_node_id
def find_closest_node(nodes, edges, latitude, longitude):
    print("Getting the closest Nodes .. ")
    closest_node_id = -1
    min_distance = float('inf')

    for edge in edges:
        source_node = nodes[edge.source]
        target_node = nodes[edge.target]

        # Calculate the distance from the point to the line segment formed by the edge
        distance = distance_to_edge(latitude, longitude, source_node.latitude, source_node.longitude, target_node.latitude, target_node.longitude)

        if distance < min_distance:
            min_distance = distance
            closest_node_id = edge.target  # You can choose source or target based on your requirements

    return closest_node_id

def distance_to_edge(px, py, x1, y1, x2, y2):
    # Calculate the distance from point (px, py) to the line segment (x1, y1) to (x2, y2)
    dx = x2 - x1
    dy = y2 - y1

    dot_product = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)

    if dot_product < 0:
        return math.sqrt((px - x1) ** 2 + (py - y1) ** 2)
    elif dot_product <= 1:
        x = x1 + dot_product * dx
        y = y1 + dot_product * dy
        return math.sqrt((px - x) ** 2 + (py - y) ** 2)
    else:
        return math.sqrt((px - x2) ** 2 + (py - y2) ** 2)

# def is_inside_bounding_box(lat, lon):
#     bounding_box = {
#         'minlat': 28.5535000,
#         'minlon': 77.2018000,
#         'maxlat': 28.5789000,
#         'maxlon': 77.2383000
#     }

#     return bounding_box['minlat'] <= lat <= bounding_box['maxlat'] and \
#            bounding_box['minlon'] <= lon <= bounding_box['maxlon']

app = Flask(__name__)
# CORS(app)

# nodes, edges, id_mapping, node_map = load_graph_data()


@app.route('/')
def hello_world():
    return render_template('index.html')
    # return 'Hello, World!'
    


#  Route

@app.route('/process_coordinates', methods=['POST'])
def process_coordinates():
    # Get coordinates from the form
    start_lat = float(request.json.get('sourceLat'))
    start_lon = float(request.json.get('sourceLon'))
    end_lat = float(request.json.get('destLat'))
    end_lon = float(request.json.get('destLon'))
    # start_lat = 28.5745268
    # start_lon = 77.2149880
    # end_lat = 28.5741560
    # end_lon = 77.2120026

    # Load OSM file using ElementTree
    tree = ET.parse("ina_2.osm")
    root = tree.getroot()

    nodes = []
    edges = []
    id_mapping = {}
    node_map = {}


    # Process nodes and ways
    for node in root.findall(".//node"):
        process_nodes(node, nodes, id_mapping, 0, node_map)

    print("Processing Nodes...",)

    for way in root.findall(".//way"):
        process_ways(way, edges, id_mapping)

    print("Processing Ways.. ", len(edges))

    # Mapping of ways and creating an Adjacency Matrix with weighted edges
    num_nodes = len(nodes)
    adjacency_matrix = [[0] * num_nodes for _ in range(num_nodes)]

    for edge in edges:
        dist = haversine_distance(nodes[edge.source], nodes[edge.target])
        adjacency_matrix[edge.source][edge.target] = dist
        adjacency_matrix[edge.target][edge.source] = dist

    # Find the closest nodes to the provided latitude and longitude for source and destination
    closest_source_node_id = find_closest_node(nodes, edges, start_lat, start_lon)
    closest_destination_node_id = find_closest_node(nodes,edges, end_lat, end_lon)
    print("Closest Source Node:", closest_source_node_id)
    # print("Closest Node Id ", id_mapping[closest_source_node_id] )

    print("Closest Destination Node:", closest_destination_node_id)
    # print("Closest Node Id ", id_mapping[closest_destination_node_id] )


    # Run Dijkstra's algorithm
    path = dijkstra(adjacency_matrix, closest_source_node_id, closest_destination_node_id, num_nodes, nodes)


    # Process the path as needed

    # Return the result to the front end
    print("\n")
    path_lat_lon = []


    for node_id in path:
        node = int(node_id)
        lat_lon = get_lat_lon_from_node_id(node, node_map)
        latitude = lat_lon[0]
        longitude = lat_lon[1]
        path_lat_lon.append((latitude, longitude))
        # print("Path")
        print( f"Node Id : {node_id}")
    end = time.time()
    print("Execution time of the program is-" , end-start)
        
    return jsonify({'path': path_lat_lon})

def process_data_function(input_data):
    # Your data processing logic here
    return input_data.upper()



if __name__ =="__main__":
    app.run(debug = True, port=8000)



