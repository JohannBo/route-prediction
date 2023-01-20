import ast
import configparser
import csv

import networkx as nx
from selection.SelectionStrategy import SelectionStrategy


class SelectAllStrat(SelectionStrategy):

    def __init__(self, config: configparser.ConfigParser, input_method: str) -> None:
        self.result_dir_name = input_method + '-all'
        super().__init__(config, input_method)

    def do_selection(self, G: nx.DiGraph, input_reader: csv.DictReader) -> (set, set, bool):
        node_set = set()
        edge_set = set()
        for row in input_reader:
            path = ast.literal_eval(row['NODE_PATH'])

            path_edges = []
            for i in range(0, len(path) - 1):
                e = (path[i], path[i + 1])
                path_edges.append(e)

            for node in path:
                node_set.add(node)
            for edge in path_edges:
                edge_set.add(edge)

        return node_set, edge_set, False
