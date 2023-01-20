import ast
import configparser
import csv

import networkx as nx
from selection.SelectionStrategy import SelectionStrategy
from util import HighwayExtractor


class SkylineStrat(SelectionStrategy):

    def __init__(self, config: configparser.ConfigParser, input_method: str) -> None:
        self.result_dir_name = input_method + '-skyline'
        super().__init__(config, input_method)

    def do_selection(self, G: nx.DiGraph, input_reader: csv.DictReader) -> (set, set, bool):
        path_list = []
        for row in input_reader:
            path = ast.literal_eval(row['NODE_PATH'])
            distance = nx.path_weight(G, path, 'travel_time')
            highway_types = HighwayExtractor.calculate_highway_types(G, path)
            num_peaks = HighwayExtractor.calculate_highway_peaks(highway_types)
            path_tuple = (path, distance, num_peaks)
            path_list.append(path_tuple)

        path_list.sort(key=lambda y: y[1])

        min_value = None
        # res_path = []
        node_set = None
        edge_set = None

        first_path = True
        replaced = False

        for path in path_list:

            path_edges = []
            for i in range(0, len(path[0]) - 1):
                e = (path[0][i], path[0][i + 1])
                path_edges.append(e)

            if first_path:
                first_path = False
                min_value = path[2]
                # res_path.append(path[0])
                node_set = set(path[0])
                edge_set = set(path_edges)
            elif path[2] < min_value:
                min_value = path[2]
                replaced = True
                # res_path.append(path[0])
                for node in path[0]:
                    node_set.add(node)
                for edge in path_edges:
                    edge_set.add(edge)

        return node_set, edge_set, replaced
