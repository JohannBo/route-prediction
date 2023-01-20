import configparser
import csv
import itertools
import os
import time

import networkx as nx
import osmnx as ox
from Strategy import Strategy


class ViaPathsStrat(Strategy):

    def __init__(self, config: configparser.ConfigParser, fastest=True) -> None:
        self._graphml_file_path = config['osm']['graphml_file_path']
        self._speed_limits_path = config['osm']['speed_limits_path']
        self._fmm_path = config['fmm']['output_path']
        self._fmm_train_name = config['DEFAULT']['train_file_name']
        self._output_dir_path = config['vp']['output_path']
        self._output_dir_path = os.path.join(self._output_dir_path, self._fmm_train_name)

        if fastest:
            self._weight = 'travel_time'
        else:
            self._weight = 'length'

        self._duration_upper_bound = float(config['vp']['duration_upper_bound'])

    def _find_paths(self, G, source, target, duration_upper_bound):
        result = []

        forward_paths = nx.single_source_dijkstra_path(G, source, cutoff=duration_upper_bound, weight=self._weight)
        forward_set = set(forward_paths)

        G_reverse = G.reverse()
        reverse_paths = nx.single_source_dijkstra_path(G_reverse, target, cutoff=duration_upper_bound,
                                                       weight=self._weight)
        reverse_set = set(reverse_paths)

        intersection = set.intersection(forward_set, reverse_set)

        for n in intersection:
            head = forward_paths[n]
            tail = reverse_paths[n]
            tail.reverse()
            via_node = tail[0]
            tail = tail[1:]
            path = head + tail
            # check path length
            if nx.path_weight(G, path, 'travel_time') <= duration_upper_bound:
                result.append((path, via_node))

        # group by path and append list of via nodes
        result.sort()
        result = list(
            [(key, list(node for _, node in value)) for key, value in itertools.groupby(result, lambda x: x[0])])

        return result

    def do_algorithm(self) -> None:
        trajectory_path = os.path.join(self._fmm_path, self._fmm_train_name)

        if not os.path.exists(self._output_dir_path):
            print("Creating output directory: ", self._output_dir_path)
            os.makedirs(self._output_dir_path)

        print("loading graph")
        G = ox.load_graphml(self._graphml_file_path)
        G = ox.utils_graph.get_digraph(G, weight=self._weight)
        print('G nodes', len(G.nodes()))
        print('G edges', len(G.edges()))

        print("loading trajectories")
        total_rows = sum(1 for _ in open(trajectory_path)) - 1
        with open(trajectory_path, newline='', encoding='utf-8') as trajectory_file:
            trajectory_csv = csv.DictReader(trajectory_file, delimiter=',')

            fieldnames = ['TRIP_ID', 'PATH_ID', 'START_NODE', 'END_NODE', 'NODE_PATH', 'VIA_NODES', 'RUNTIME']

            i = 0
            for row in trajectory_csv:
                trip_id = int(row['TRIP_ID'])
                print(i / total_rows * 100, '%; trip_id: ', trip_id)
                i += 1
                start_node = int(row['START_NODE'])
                end_node = int(row['END_NODE'])
                trajectory_duration = float(row['REAL_DURATION'])

                duration_upper_bound = trajectory_duration + (trajectory_duration * self._duration_upper_bound)

                start_time = time.time()
                paths = self._find_paths(G, start_node, end_node, duration_upper_bound)
                execution_time = (time.time() - start_time)

                # saving paths
                trip_output_file_name = os.path.join(self._output_dir_path, str(trip_id) + '.csv')
                with open(trip_output_file_name, 'w', newline='', encoding='utf-8') as output_file:
                    w = csv.DictWriter(output_file, fieldnames=fieldnames, quotechar='"', quoting=csv.QUOTE_ALL)
                    w.writeheader()
                    path_id = 0
                    for node_path in paths:
                        (via_path, via_nodes) = node_path
                        new_row = {'TRIP_ID': trip_id, 'PATH_ID': path_id, 'START_NODE': start_node,
                                   'END_NODE': end_node, 'NODE_PATH': via_path, 'VIA_NODES': via_nodes,
                                   'RUNTIME': execution_time}
                        w.writerow(new_row)
                        path_id += 1
