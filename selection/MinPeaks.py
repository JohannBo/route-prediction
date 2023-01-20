import ast
import configparser
import csv

import networkx as nx
from selection.SelectionStrategy import SelectionStrategy
from util import HighwayExtractor


class MinPeaksStrat(SelectionStrategy):

    def __init__(self, config: configparser.ConfigParser, input_method: str) -> None:
        self.result_dir_name = input_method + '-minp'
        super().__init__(config, input_method)

    def do_selection(self, G: nx.DiGraph, input_reader: csv.DictReader) -> (set, set, bool):
        min_value = None
        res_path = None
        res_edges = None

        first_path = True
        replaced = False

        for row in input_reader:
            path = ast.literal_eval(row['NODE_PATH'])

            path_edges = []
            for i in range(0, len(path) - 1):
                e = (path[i], path[i + 1])
                path_edges.append(e)

            highway_types = HighwayExtractor.calculate_highway_types(G, path)
            num_peaks = HighwayExtractor.calculate_highway_peaks(highway_types)
            if first_path:
                min_value = num_peaks
                first_path = False
                res_path = path
                res_edges = path_edges
                if min_value == 0:
                    break

            elif (min_value > 0) and (num_peaks < min_value):
                min_value = num_peaks
                res_path = path
                res_edges = path_edges
                replaced = True

            if min_value == 1:
                break

        node_set = set(res_path)
        edge_set = set(res_edges)
        return node_set, edge_set, replaced
