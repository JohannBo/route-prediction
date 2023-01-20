import ast
import configparser
import csv
import os

import osmnx as ox
from Strategy import Strategy
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

from evaluation import EvalUtil


class SinglePathEvaluatorStrat(Strategy):

    def __init__(self, config: configparser.ConfigParser, method: str) -> None:
        self._method = method
        self._input_method_name = config[method]['input_method_name']
        self._input_file_name = config[method]['input_file_name']
        self._graphml_file_path = config['osm']['graphml_file_path']

        self._ground_truth_file = os.path.join(config['fmm']['output_path'], config['fmm']['train_file_name'])
        self._result_file = os.path.join(config[self._input_method_name]['output_path'],
                                         config['fmm']['train_file_name'],
                                         config[method]['input_file_name'])
        self._output_path = config[method]['output_path']
        self._output_file_path = os.path.join(config[method]['output_path'], config['fmm']['train_file_name'])

    def do_algorithm(self) -> None:
        G = ox.load_graphml(self._graphml_file_path)
        G = ox.get_digraph(G, weight='length')
        G_nodes = list(G.nodes)

        path_vectors = {}
        accuracies = {}
        precisions = {}
        recalls = {}
        recall_at_ns = {}

        (tripIds, gt_path_vectors, gt_path_edges, gt_path_lengths, tripsTimestamps, tripsErrors,
         errorList) = EvalUtil.calculate_groud_truth(G, self._ground_truth_file)
        total_rows = len(tripIds)

        with open(self._result_file, newline='') as csvfile:
            spamreader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
            i = 0
            for row in spamreader:
                tripId = int(row['TRIP_ID'])
                print(i / total_rows * 100, '%; trip_id: ', tripId)
                i += 1
                pathNodes = ast.literal_eval(row['NODE_PATH'])
                node_set = set()
                for n in pathNodes:
                    node_set.add(n)

                # print(tripId, len(node_set), node_set)
                path_vectors[tripId] = []

                for node in G_nodes:
                    if node in node_set:
                        path_vectors[tripId].append(1)
                    else:
                        path_vectors[tripId].append(0)

                precision = precision_score(gt_path_vectors[tripId], path_vectors[tripId])
                recall = recall_score(gt_path_vectors[tripId], path_vectors[tripId])

                pathLength = 0
                intersectionLength = 0
                for node_i in range(0, len(pathNodes) - 1):
                    e = (pathNodes[node_i], pathNodes[node_i + 1])
                    pathLength += G.edges[e[0], e[1]]['length']
                    if e in gt_path_edges[tripId]:
                        intersectionLength += G.edges[e[0], e[1]]['length']

                recall_at_n = intersectionLength / gt_path_lengths[tripId]
                accuracy = intersectionLength / max(gt_path_lengths[tripId], pathLength)

                precisions[tripId] = precision
                recalls[tripId] = recall
                recall_at_ns[tripId] = recall_at_n
                accuracies[tripId] = accuracy

        if not os.path.exists(self._output_path):
            print("Creating output directory: ", self._output_path)
            os.makedirs(self._output_path)
        with open(self._output_file_path, 'w', newline='', encoding='utf-8') as output_file:
            fieldnames = ['TRIP_ID', 'PRECISION', 'RECALL', 'RECALLATN', 'ACCURACY']
            w = csv.DictWriter(output_file, fieldnames=fieldnames, quotechar='"', quoting=csv.QUOTE_ALL)
            w.writeheader()

            for tripId in tripIds:
                new_row = {'TRIP_ID': tripId, 'PRECISION': precisions[tripId], 'RECALL': recalls[tripId],
                           'RECALLATN': recall_at_ns[tripId], 'ACCURACY': accuracies[tripId]}
                w.writerow(new_row)

        print(self._method)
        print("-------------")
        print("precision = ", (sum(precisions.values()) / len(precisions)))
        print("recall = ", (sum(recalls.values()) / len(recalls)))
        print("recall@n = ", (sum(recall_at_ns.values()) / len(recall_at_ns)))
        print("accuracy = ", (sum(accuracies.values()) / len(accuracies)))
