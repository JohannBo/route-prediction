import ast
import configparser
import csv

import networkx as nx
from selection.SelectionStrategy import SelectionStrategy
from util import HighwayExtractor
from util import Util


class DiversityStrat(SelectionStrategy):

    def __init__(self, config: configparser.ConfigParser, input_method: str, similarity_threshold: float) -> None:
        self.result_dir_name = input_method + '-div-' + str(int(similarity_threshold * 100))
        self.similarity_threshold = similarity_threshold
        super().__init__(config, input_method)

    def do_selection(self, G: nx.DiGraph, input_reader: csv.DictReader) -> (set, set, bool):
        vp_path_set = []

        for row in input_reader:
            lst = ast.literal_eval(row['NODE_PATH'])

            p = [(u, v, G[u][v]['travel_time']) for u, v in zip(lst[:-1], lst[1:])]
            w = sum(G[u][v]['travel_time'] for u, v in zip(lst[:-1], lst[1:]))
            vp_path_set.append((p, w))

        node_set, edge_set = self.diversity_filtering(vp_path_set, self.similarity_threshold)
        return node_set, edge_set, None

    def pathToPathSimilarity(self, path1, path2):
        commonEdgesDuration = sum([e[2] for e in path1[0] if e in path2[0]])
        return commonEdgesDuration / min([path1[1], path2[1]])

    def diversity_filtering(self, pathEntries, sim_threshold):
        pathEntries = sorted(pathEntries, key=lambda tup: tup[1])
        vp_diverse_path_set = []
        vp_diverse_node_set = set()

        for pathEntry in pathEntries:
            if len(vp_diverse_path_set) == 0:
                vp_diverse_path_set.append(pathEntry)
                for n in pathEntry[0]:
                    vp_diverse_node_set.add(n[0])
                    vp_diverse_node_set.add(n[1])
            else:
                toBeAdded = True
                for p_in in vp_diverse_path_set:
                    if (self.pathToPathSimilarity(pathEntry, p_in) > sim_threshold):
                        toBeAdded = False
                        break
                if toBeAdded:
                    vp_diverse_path_set.append(pathEntry)
                    for n in pathEntry[0]:
                        vp_diverse_node_set.add(n[0])
                        vp_diverse_node_set.add(n[1])
            edge_set = set()
            for pathEntry in vp_diverse_path_set:
                for edge in pathEntry[0]:
                    edge_set.add((edge[0], edge[1]))
            return vp_diverse_node_set, edge_set
