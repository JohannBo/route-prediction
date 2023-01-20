from __future__ import annotations

import configparser
import csv
import os
from abc import abstractmethod

import networkx as nx
import osmnx as ox
from Strategy import Strategy
from sklearn.metrics import precision_score, recall_score

from evaluation import EvalUtil


class SelectionStrategy(Strategy):

    def __init__(self, config: configparser.ConfigParser, input_method: str) -> None:
        base_resource_path = config['DEFAULT']['base_resource_path']
        self.train_file_name = config['DEFAULT']['train_file_name']
        fmm_output_path = config['fmm']['output_path']
        input_method_output_path = config[input_method]['output_path']

        self._input_method_output_file_path = os.path.join(input_method_output_path, self.train_file_name)
        self._train_file_path = os.path.join(fmm_output_path, self.train_file_name)
        self._output_path = os.path.join(base_resource_path, self.result_dir_name)
        self._output_file_path = os.path.join(self._output_path, self.train_file_name)
        self._graphml_file_path = config['osm']['graphml_file_path']

    @abstractmethod
    def do_selection(self, G: nx.DiGraph, input_reader: csv.DictReader) -> (set, set, bool):
        pass

    def do_algorithm(self) -> None:
        G = ox.load_graphml(self._graphml_file_path)
        G = ox.get_digraph(G, weight='length')
        G_nodes = list(G.nodes)

        total_rows = sum(1 for _ in open(self._train_file_path)) - 1

        if not os.path.exists(self._output_path):
            os.makedirs(self._output_path)
        with open(self._train_file_path, newline='', encoding='utf-8') as train_file, \
                open(self._output_file_path, 'w', newline='', encoding='utf-8') as output_file:

            fieldnames = ['TRIP_ID', 'PRECISION', 'RECALL', 'RECALLATN', 'ACCURACY', 'REPLACED', 'NODE_SET']
            w = csv.DictWriter(output_file, fieldnames=fieldnames, quotechar='"',
                               quoting=csv.QUOTE_ALL)
            w.writeheader()

            train_csv = csv.DictReader(train_file, delimiter=',')
            i = 0
            for train_row in train_csv:
                trip_id = int(train_row['TRIP_ID'])
                print(i / total_rows * 100, '%; trip_id: ', trip_id)
                i += 1

                (tripIds, gt_path_vectors, gt_path_edges, gt_path_lengths, tripsTimestamps, tripsErrors,
                 errorList) = EvalUtil.calculate_groud_truth(G, self._train_file_path)

                input_path = os.path.join(self._input_method_output_file_path, str(trip_id) + '.csv')
                with open(input_path, newline='') as input_csv:
                    input_reader = csv.DictReader(input_csv, delimiter=',', quotechar='"')

                    node_set, edge_set, replaced = self.do_selection(G, input_reader)

                    tempVector = EvalUtil.get_path_vector_from_nodes(G_nodes, node_set)

                    precision = precision_score(gt_path_vectors[trip_id], tempVector)
                    recall = recall_score(gt_path_vectors[trip_id], tempVector)

                    pathLength = 0
                    intersectionLength = 0
                    for e in edge_set:
                        pathLength += G.edges[e[0], e[1]]['length']
                        if e in gt_path_edges[trip_id]:
                            intersectionLength += G.edges[e[0], e[1]]['length']

                    recall_at_n = intersectionLength / gt_path_lengths[trip_id]
                    accuracy = intersectionLength / max(gt_path_lengths[trip_id], pathLength)

                    new_row = {'TRIP_ID': trip_id, 'PRECISION': precision, 'RECALL': recall, 'RECALLATN': recall_at_n,
                               'ACCURACY': accuracy, 'REPLACED': replaced, 'NODE_SET': node_set}
                    w.writerow(new_row)
