import argparse
import ast
import csv

import networkx as nx
import osmnx as ox


def _load_graph(graphml_path: str) -> nx.DiGraph:
    print("loading graph")
    G = ox.load_graphml(graphml_path)
    G = ox.get_digraph(G)
    print('G nodes', len(G.nodes()))
    print('G edges', len(G.edges()))
    return G


def extract_highway_types_graphml(graphml_path: str, input_path: str, output_path: str):
    G = _load_graph(graphml_path)
    extract_highway_types_G(G, input_path, output_path)


def extract_highway_types_G(G: nx.DiGraph, input_path: str, output_path: str):
    with open(input_path, newline='', encoding='utf-8') as input_file, \
            open(output_path, 'w', newline='', encoding='utf-8') as output_file:
        fieldnames = ['TRIP_ID', 'PATH_ID', 'HIGHWAY_TYPES', 'HIGHWAY_PEAKS']
        w = csv.DictWriter(output_file, fieldnames=fieldnames, quotechar='"', quoting=csv.QUOTE_ALL)
        w.writeheader()

        input_csv = csv.DictReader(input_file, delimiter=',')
        for row in input_csv:
            trip_id = row['TRIP_ID']
            path_id = row['PATH_ID'] if 'PATH_ID' in input_csv.fieldnames else None
            path = row['NODE_PATH']
            path = ast.literal_eval(path)

            highway_types = calculate_highway_types(G, path)

            highway_peaks = calculate_highway_peaks(highway_types)
            new_row = {'TRIP_ID': trip_id, 'PATH_ID': path_id, 'HIGHWAY_TYPES': highway_types,
                       'HIGHWAY_PEAKS': highway_peaks}
            w.writerow(new_row)


def clean_highway_types(highway_types) -> str:
    allowed_types = ['motorway', 'trunk', 'primary', 'secondary', 'tertiary', 'unclassified', 'residential']
    # convert list to string
    types_string = str(highway_types)
    # check if any allowed type is found in types starting with most important
    for at in allowed_types:
        if at in types_string:
            return at

    # return least important type as default
    return allowed_types[-1]


def calculate_highway_types(G: nx.DiGraph, path: list) -> list:
    highway_types = []
    for i in range(len(path) - 1):
        edge_data = G.get_edge_data(path[i], path[i + 1])
        highway = edge_data['highway']
        # Sometimes highway is a list. we check if it contains one of the major highway types.
        # Otherwise, return first element.

        highway = clean_highway_types(highway)

        highway_types.append(highway)
    return highway_types


def calculate_highway_peaks(highway_sequence) -> int:
    highway_hierarchy = {
        'motorway': 7,
        'trunk': 6,
        'primary': 5,
        'secondary': 4,
        'tertiary': 3,
        'unclassified': 2,
        'residential': 1
    }
    # priority_sequence = list(map(highway_hierarchy.get, highway_sequence))
    priority_sequence = []
    for h in highway_sequence:
        priority_sequence.append(highway_hierarchy[h])

    # for values that are not in the map, we assume it is a very small street
    priority_sequence = [0 if v is None else v for v in priority_sequence]

    peaks = 0
    last_prio = -1
    rising = True
    for prio in priority_sequence:
        if rising and prio < last_prio:
            peaks += 1
            rising = False
        elif prio > last_prio:
            rising = True
        last_prio = prio

    return peaks


def extract_osmways_graphml(graphml_path: str, input_path: str, output_path: str):
    G = _load_graph(graphml_path)
    extract_highway_types_G(G, input_path, output_path)


def extract_osmways_G(G, input_path: str, output_path: str):
    with open(input_path, newline='', encoding='utf-8') as input_file, \
            open(output_path, 'w', newline='', encoding='utf-8') as output_file:
        fieldnames = ['TRIP_ID', 'PATH_ID', 'NUM_TURNS']
        w = csv.DictWriter(output_file, fieldnames=fieldnames, quotechar='"', quoting=csv.QUOTE_ALL)
        w.writeheader()

        input_csv = csv.DictReader(input_file, delimiter=',')
        for row in input_csv:
            trip_id = row['TRIP_ID']
            path_id = row['PATH_ID'] if 'PATH_ID' in input_csv.fieldnames else None
            path = row['NODE_PATH']
            path = ast.literal_eval(path)
            turns = calculate_turns(G, path)
            new_row = {'TRIP_ID': trip_id, 'PATH_ID': path_id, 'NUM_TURNS': turns}
            w.writerow(new_row)


def calculate_turns(G, path):
    turns = 0
    prevOsmId = -1
    for i in range(len(path) - 1):
        edge_data = G.get_edge_data(path[i], path[i + 1])
        osmid = edge_data['osmid']
        if osmid != prevOsmId:
            turns += 1
            prevOsmId = osmid

    return turns


if __name__ == "__main__":
    description = '''
    Extract highway type information on existing paths.
    Example: python util/Util.py datasets/porto/resources/osm/graph.graphml
    datasets/porto/resources/sp/shortest_paths.csv
    datasets/porto/resources/sp/highway_types.csv
    '''
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("graphml", help="Path to graphml file use.", type=str)
    parser.add_argument("input", help="Path to input file containing paths.", type=str)
    parser.add_argument("output", help="Path to output, where highway types are written.", type=str)
    args = parser.parse_args()

    extract_highway_types_graphml(args.graphml, args.input, args.output)
    # extract_osmways_graphml(args.graphml, args.input, args.output)
