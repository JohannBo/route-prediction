import configparser
import csv
import os
import time

import networkx as nx
import osmnx as ox
from Strategy import Strategy


class PenaltyStrat(Strategy):

    def __init__(self, config: configparser.ConfigParser, fastest=True) -> None:
        self._graphml_file_path = config['osm']['graphml_file_path']
        self._speed_limits_path = config['osm']['speed_limits_path']
        self._fmm_path = config['fmm']['output_path']
        self._fmm_train_name = config['DEFAULT']['train_file_name']
        self._output_dir_path = config['pen']['output_path']
        self._output_dir_path = os.path.join(self._output_dir_path, self._fmm_train_name)

        if fastest:
            self._weight = 'travel_time'
        else:
            self._weight = 'length'

    def find_multiple_paths_distr(self, g, source, target, trajectory_duration):
        result = []
        penalized_edges = set()
        edges_duration = nx.get_edge_attributes(g, "travel_time")
        nx.set_edge_attributes(g, edges_duration, "penalized_duration")
        dist, spath = nx.single_source_dijkstra(g, source, target, weight="penalized_duration")
        result.append(spath)
        error = trajectory_duration - dist

        prevError = -1
        while abs(error) > 1 and error != prevError:
            validDist = dist
            nonPenalizedDist = 0
            for i in range(0, len(spath) - 1):
                if (spath[i], spath[i + 1]) in penalized_edges:
                    validDist -= g.edges[spath[i], spath[i + 1]]['penalized_duration']
                    nonPenalizedDist += g.edges[spath[i], spath[i + 1]]['penalized_duration']

            for i in range(0, len(spath) - 1):
                if (spath[i], spath[i + 1]) not in penalized_edges:
                    penalty = (g.edges[spath[i], spath[i + 1]]['penalized_duration'] / validDist) * error
                    g.edges[spath[i], spath[i + 1]]['penalized_duration'] += penalty
                    penalized_edges.add((spath[i], spath[i + 1]))

            dist, spath = nx.single_source_dijkstra(g, source, target, weight="penalized_duration")
            result.append(spath)
            prevError = error
            error = trajectory_duration - dist

        edges_duration = nx.get_edge_attributes(g, "travel_time")
        nx.set_edge_attributes(g, edges_duration, "penalized_duration")

        result.append(spath)

        return result

    def do_algorithm(self) -> None:
        trajectory_path = os.path.join(self._fmm_path, self._fmm_train_name)

        if not os.path.exists(self._output_dir_path):
            print("Creating output directory: ", self._output_dir_path)
            os.makedirs(self._output_dir_path)

        print("loading graph")
        G = ox.load_graphml(self._graphml_file_path)
        G = ox.get_digraph(G, weight=self._weight)
        print('G nodes', len(G.nodes()))
        print('G edges', len(G.edges()))

        print("loading trajectories")
        total_rows = sum(1 for _ in open(trajectory_path)) - 1
        with open(trajectory_path, newline='', encoding='utf-8') as trajectory_file:
            trajectory_csv = csv.DictReader(trajectory_file, delimiter=',')

            fieldnames = ['TRIP_ID', 'PATH_ID', 'START_NODE', 'END_NODE', 'NODE_PATH', 'RUNTIME']

            i = 0
            for row in trajectory_csv:
                trip_id = int(row['TRIP_ID'])
                print(i / total_rows * 100, '%; trip_id: ', trip_id)
                i += 1
                start_node = int(row['START_NODE'])
                end_node = int(row['END_NODE'])
                trajectory_duration = float(row['REAL_DURATION'])

                start_time = time.time()
                paths = self.find_multiple_paths_distr(G, start_node, end_node, trajectory_duration)
                execution_time = (time.time() - start_time)

                # saving paths
                trip_output_file_name = os.path.join(self._output_dir_path, str(trip_id) + '.csv')
                with open(trip_output_file_name, 'w', newline='', encoding='utf-8') as output_file:
                    w = csv.DictWriter(output_file, fieldnames=fieldnames, quotechar='"', quoting=csv.QUOTE_ALL)
                    w.writeheader()
                    path_id = 0
                    for node_path in paths:
                        new_row = {'TRIP_ID': trip_id, 'PATH_ID': path_id, 'START_NODE': start_node,
                                   'END_NODE': end_node, 'NODE_PATH': node_path, 'RUNTIME': execution_time}
                        w.writerow(new_row)
                        path_id += 1
