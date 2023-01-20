import fiona
import networkx as nx
import osmnx as ox
import pandas as pd


def load_graph(path_edges, path_nodes, path_speed_limits) -> nx.MultiDiGraph:
    G = nx.DiGraph()

    with fiona.open(path_edges) as edge_features, fiona.open(path_nodes) as node_features, \
            open(path_speed_limits, newline='', encoding='utf-8') as speed_limits_file:

        speed_limits = pd.read_csv(speed_limits_file)
        # sl = speed_limits.loc[speed_limits['osm_id'] == 4256491]
        # print(type(sl))
        # print(sl)
        # print(sl['kmh'])

        for node in node_features:
            properties = node['properties']
            geometry = node['geometry']
            id = properties['osmid']
            G.add_node(id, properties=properties, geometry=geometry)

        for edge in edge_features:
            properties = edge['properties']
            geometry = edge['geometry']
            u = properties['u']
            v = properties['v']
            fid = properties['fid']
            # distance in meters
            weight_distance = properties['length']
            weight_distance = float(weight_distance)

            speed_limit = speed_limits.loc[speed_limits['source'].eq(int(u)) & speed_limits['target'].eq(int(v))]
            # TODO: if there are multiple speed limits we just take the first. is there a better solution?
            speed_limit = list(speed_limit['speed_kph'])[0]
            # speed limit in km/h convert to m/s
            speed_limit = speed_limit / 3.6

            weight_duration = weight_distance / speed_limit
            # print('u:', u)
            # print('v:', v)
            # print('osmid:', properties['osmid'])
            # print('distance:', weight_distance)
            # print('speed limit:', speed_limit)
            # print('duration:', weight_duration)
            # print()
            G.add_edge(u, v, weight_duration=weight_duration, weight_distance=weight_distance, fid=fid,
                       geometry=geometry,
                       properties=properties)
        return G


def get_furthest_node_index(G: nx.DiGraph, path: list, max_distance: float, iterator: iter) -> int:
    dist_sum = 0
    for i in iterator:
        dist = nx.path_weight(G, path[i - 1: i + 1], weight='travel_time')
        dist_sum += dist
        # print('i', i, 'p', path[i - 1: i + 1], 'dist', dist, 'dist_sum', dist_sum)
        if dist_sum > max_distance:
            break
    return i


def is_locally_optimal(G: nx.DiGraph, path: list, alpha: float) -> bool:
    if len(path) < 2:
        return None

    reference_distance = nx.path_weight(G, path, weight='travel_time')
    t_distance = reference_distance * alpha

    u_index = get_furthest_node_index(G, path, t_distance, range(1, len(path)))
    w_index = get_furthest_node_index(G, path, t_distance, range(len(path) - 1, 0, -1))

    local_path = path[u_index: w_index]
    if len(local_path) < 2:
        return None
    local_shortest_path = nx.shortest_path(G, local_path[0], local_path[-1], weight='travel_time')
    return local_shortest_path == local_path


if __name__ == "__main__":
    # test local optimality check
    graphml_path = "datasets/porto_small/resources/osm/graph.graphml"
    print("loading graph")
    G = ox.load_graphml(graphml_path)
    G = ox.get_digraph(G)
    print('G nodes', len(G.nodes()))
    print('G edges', len(G.edges()))

    path = [122549700, 111467467, 478646205, 478646306, 478645965, 2616040153, 2616040194, 5297710833, 478212483,
            5297710833, 2616040194, 2619594977, 2681392509, 2616040186, 3391598619, 478821668, 111467271, 478632189,
            1143316313, 297880608, 427067714, 285945659, 128673222, 128673223, 1788786316, 1418798470, 1418798472,
            3092543648, 2244990442, 129800102, 129800097, 1416622188]

    print(path)
    is_optimal = is_locally_optimal(G, path, 0.45)
    print(is_optimal)
