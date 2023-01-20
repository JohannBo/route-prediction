import configparser
import csv
import os
import time

import networkx as nx
import osmnx as ox
from Strategy import Strategy
from util import HighwayExtractor


class ResourceConstrainedStrat(Strategy):

    def __init__(self, config: configparser.ConfigParser) -> None:
        self._graphml_file_path = config['osm']['graphml_file_path']
        self._fmm_path = config['fmm']['output_path']
        self._train_file_name = config['DEFAULT']['train_file_name']
        self._output_dir_path = config['rc']['output_path']
        self._output_dir_path = os.path.join(self._output_dir_path, self._train_file_name)
        self._output_path = os.path.join(self._output_dir_path, "resource_constrained.csv")
        self._highway_path = os.path.join(self._output_dir_path, "highway_types.csv")

        self._weight = 'travel_time'
        self._duration_lower_bound = float(config['rc']['duration_lower_bound'])
        self._duration_upper_bound = float(config['rc']['duration_upper_bound'])

    def _find_paths(self, G, source, target, duration_lower_bound, duration_upper_bound):
        sp_iterator = nx.shortest_simple_paths(G, source, target, weight=self._weight)
        i = 0
        result = []

        while True:
            sp = next(sp_iterator)
            i += 1
            # duration in seconds
            duration = nx.path_weight(G, sp, self._weight)

            if len(result) > 1000:
                break
            if duration > duration_upper_bound:
                break

            if duration > duration_lower_bound:
                result.append(sp)

            if i % 1000 == 0:
                print("i:", i, " found paths: ", len(result), ' duration:', duration, ' upper bound:',
                      duration_upper_bound)

        return result

        # node_path = nx.shortest_path(G, source=source, target=target, weight=self._weight)
        # new_row = {'TRIP_ID': trip_id, 'START_NODE': start_node, 'END_NODE': end_node, 'NODE_PATH': node_path}
        # w.writerow(new_row)

    def do_algorithm(self) -> None:

        trajectory_path = os.path.join(self._fmm_path, self._train_file_name)

        if not os.path.exists(self._output_dir_path):
            print("Creating output directory: ", self._output_dir_path)
            os.makedirs(self._output_dir_path)

        print("loading graph")
        G = ox.load_graphml(self._graphml_file_path)
        G = ox.utils_graph.get_digraph(G, weight=self._weight)
        print('G nodes', len(G.nodes()))
        print('G edges', len(G.edges()))

        print("loading trajectories")
        with open(trajectory_path, newline='', encoding='utf-8') as trajectory_file, \
                open(self._output_path, 'w', newline='', encoding='utf-8') as output_file:
            trajectory_csv = csv.DictReader(trajectory_file, delimiter=',')

            fieldnames = ['TRIP_ID', 'PATH_ID', 'START_NODE', 'END_NODE', 'NODE_PATH', 'RUNTIME']
            w = csv.DictWriter(output_file, fieldnames=fieldnames, quotechar='"', quoting=csv.QUOTE_ALL)
            w.writeheader()

            for row in trajectory_csv:
                trip_id = int(row['TRIP_ID'])
                start_node = int(row['START_NODE'])
                end_node = int(row['END_NODE'])
                trajectory_duration = float(row['REAL_DURATION'])
                mapped_duration = float(row['MAPPED_DURATION'])

                # skip trajectories with very large difference between mapped and real trajectory
                if trajectory_duration / mapped_duration > 1.5:
                    print('Skipping trajectory. Difference between mapped and real duration too big.',
                          trajectory_duration / mapped_duration)
                    continue

                print('trajectory_duration', trajectory_duration)
                duration_lower_bound = trajectory_duration - (trajectory_duration * self._duration_lower_bound)
                duration_upper_bound = trajectory_duration + (trajectory_duration * self._duration_upper_bound)
                print('duration_lower_bound', duration_lower_bound)
                print('duration_upper_bound', duration_upper_bound)

                print('find_paths:', start_node, end_node, duration_lower_bound, duration_upper_bound)
                start_time = time.time()
                paths = self._find_paths(G, start_node, end_node, duration_lower_bound, duration_upper_bound)
                execution_time = (time.time() - start_time)

                # saving paths
                print('writing paths to disk.')
                path_id = 0
                for node_path in paths:
                    new_row = {'TRIP_ID': trip_id, 'PATH_ID': path_id, 'START_NODE': start_node, 'END_NODE': end_node,
                               'NODE_PATH': node_path, 'RUNTIME': execution_time}
                    w.writerow(new_row)
                    path_id += 1
                break

        HighwayExtractor.extract_highway_types_G(G, self._output_path, self._highway_path)
