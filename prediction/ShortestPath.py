import configparser
import csv
import os
import time

import networkx as nx
import osmnx as ox
from Strategy import Strategy
from util import HighwayExtractor


class ShortestPathStrat(Strategy):

    def __init__(self, config: configparser.ConfigParser, fastest=True) -> None:
        self._graphml_file_path = config['osm']['graphml_file_path']
        self._speed_limits_path = config['osm']['speed_limits_path']
        self._fmm_path = config['fmm']['output_path']
        self._train_file_name = config['DEFAULT']['train_file_name']
        if fastest:
            self._weight = 'travel_time'
            self._output_dir_path = config['fp']['output_path']
            self._output_dir_path = os.path.join(self._output_dir_path, self._train_file_name)
            self._output_path = os.path.join(self._output_dir_path, "fastest_paths.csv")
        else:
            self._weight = 'length'
            self._output_dir_path = config['sp']['output_path']
            self._output_dir_path = os.path.join(self._output_dir_path, self._train_file_name)
            self._output_path = os.path.join(self._output_dir_path, "shortest_paths.csv")
        self._highway_path = os.path.join(self._output_dir_path, "highway_types.csv")

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

            fieldnames = ['TRIP_ID', 'START_NODE', 'END_NODE', 'NODE_PATH', 'RUNTIME']
            w = csv.DictWriter(output_file, fieldnames=fieldnames, quotechar='"', quoting=csv.QUOTE_ALL)
            w.writeheader()

            for row in trajectory_csv:
                trip_id = int(row['TRIP_ID'])
                start_node = int(row['START_NODE'])
                end_node = int(row['END_NODE'])
                start_time = time.time()
                node_path = nx.shortest_path(G, source=start_node, target=end_node, weight=self._weight)
                execution_time = (time.time() - start_time)
                new_row = {'TRIP_ID': trip_id, 'START_NODE': start_node, 'END_NODE': end_node, 'NODE_PATH': node_path,
                           'RUNTIME': execution_time}
                w.writerow(new_row)

        HighwayExtractor.extract_highway_types_G(G, self._output_path, self._highway_path)
