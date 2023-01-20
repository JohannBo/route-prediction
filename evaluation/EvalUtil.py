import argparse
import ast
import csv
import datetime
import os
import sys

import networkx as nx
import numpy
import osmnx as ox
from sklearn.metrics import precision_score, recall_score


def calculate_groud_truth(G: nx.DiGraph, ground_truth_file):
    G_nodes = list(G.nodes)

    tripIds = []
    gt_path_vectors = {}
    gt_path_edges = {}
    gt_path_lengths = {}
    tripsTimestamps = {}
    tripsErrors = {}
    errorList = []

    with open(ground_truth_file, newline='') as csvfile:
        spamreader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
        for row in spamreader:
            lst = ast.literal_eval(row['CPATH'])
            tripId = int(row['TRIP_ID'])
            gt_path_edges[tripId] = lst
            try:
                tripsTimestamps[int(row['TRIP_ID'])] = datetime.datetime.strptime(row['TIMESTAMP'], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                tripsTimestamps[int(row['TRIP_ID'])] = datetime.datetime.fromtimestamp(int(row['TIMESTAMP']))
            # print(tripId)
            # for (a,b) in lst:
            #    print("----- ",a,b)
            #    print("----- length = ",G.edges[a,b]['length'])
            gt_path_lengths[tripId] = get_path_length(G, lst)
            gt_path_vectors[tripId] = get_path_vector_from_edges(G_nodes, lst)
            tripIds.append(tripId)
            try:
                tripsTimestamps[tripId] = datetime.datetime.strptime(row['TIMESTAMP'], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                tripsTimestamps[tripId] = datetime.datetime.fromtimestamp(int(row['TIMESTAMP']))
            dist = nx.dijkstra_path_length(G, int(row['START_NODE']), int(row['END_NODE']), weight='weight_duration')
            tripsErrors[tripId] = float(row['REAL_DURATION']) - dist
            errorList.append(abs(float(row['REAL_DURATION']) - dist))

    return tripIds, gt_path_vectors, gt_path_edges, gt_path_lengths, tripsTimestamps, tripsErrors, errorList


def get_path_vector_from_nodes(G_nodes, path_nodes):
    pv = []
    nodeSet = set(path_nodes)
    for node in G_nodes:
        if node in nodeSet:
            pv.append(1)
        else:
            pv.append(0)
    return pv


def get_path_vector_from_edges(G_nodes, path_edges):
    pv = []
    nodeSet = set()

    for (a, b) in path_edges:
        nodeSet.add(a)
        nodeSet.add(b)

    for node in G_nodes:
        if node in nodeSet:
            pv.append(1)
        else:
            pv.append(0)
    return pv


def get_path_edges(G_nodes, path_nodes):
    pe = []

    for i in range(0, len(path_nodes) - 1):
        pe.append((path_nodes[i], path_nodes[i + 1]))

    return pe


def get_path_length(G, path_edges):
    length = 0
    for (a, b) in path_edges:
        length += G.edges[a, b]['length']
    return length


def load_precisions(base_dir: str):
    csv.field_size_limit(sys.maxsize)
    precision = {}
    recall = {}
    recall_at_n = {}
    accuracy = {}

    for subdir_name in os.listdir(base_dir):
        filename = os.path.join(base_dir, subdir_name)
        with open(filename, 'r', newline='', encoding='utf-8') as input_file:
            reader = csv.DictReader(input_file, delimiter=',', quotechar='"')
            for row in reader:
                trip_id = int(row['TRIP_ID'])
                if 'NODE_SET' in row and row['NODE_SET'] == 'set()':
                    print(trip_id, 'skipping, empty node set!')
                    continue
                precision[trip_id] = float(row['PRECISION'])
                recall[trip_id] = float(row['RECALL'])
                recall_at_n[trip_id] = float(row['RECALLATN'])
                accuracy[trip_id] = float(row['ACCURACY'])
    return precision, recall, recall_at_n, accuracy


def load_node_set_size(base_dir: str):
    csv.field_size_limit(sys.maxsize)
    node_set_size = {}

    for subdir_name in os.listdir(base_dir):
        filename = os.path.join(base_dir, subdir_name)
        with open(filename, 'r', newline='', encoding='utf-8') as input_file:
            reader = csv.DictReader(input_file, delimiter=',', quotechar='"')
            for row in reader:
                trip_id = int(row['TRIP_ID'])
                if 'NODE_SET' in row and row['NODE_SET'] == 'set()':
                    print(trip_id, 'skipping, empty node set!')
                    continue
                node_set_size[trip_id] = len(ast.literal_eval(row['NODE_SET']))
    return node_set_size


def save_stat_file(file_name: str, stats: dict):
    with open(file_name, 'w', newline='', encoding='utf-8') as output_file:
        w = csv.DictWriter(output_file, fieldnames=['key', 'value'], quotechar='"', quoting=csv.QUOTE_ALL)
        w.writeheader()
        for k, v in stats.items():
            w.writerow({'key': k, 'value': v})


def load_stat_file(file_name: str) -> dict:
    with open(file_name, 'r', newline='', encoding='utf-8') as input_file:
        r = csv.DictReader(input_file, delimiter=',', quotechar='"')
        stats = {}
        for row in r:
            stats[int(row['key'])] = numpy.float64(row['value'])
        return stats


def get_stats_single_file(G, ground_truth_file, result_file) -> tuple:
    (tripIds, gt_path_vectors, gt_path_edges, gt_path_lengths, tripsTimestamps, tripsErrors,
     errorList) = calculate_groud_truth(G, ground_truth_file)
    total_rows = len(tripIds)

    G_nodes = list(G.nodes)

    precisions = {}
    recalls = {}
    recallsATn = {}
    accuracies = {}

    csv.field_size_limit(sys.maxsize)
    with open(result_file, newline='') as csvfile:
        spamreader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
        i = 0
        for row in spamreader:
            tripId = int(row['TRIP_ID'])
            print(i / total_rows * 100, '%; trip_id: ', tripId)
            i += 1
            pathNodes = ast.literal_eval(row['NODE_SET'])
            tempVector = get_path_vector_from_nodes(G_nodes, pathNodes)

            precisions[tripId] = precision_score(gt_path_vectors[tripId], tempVector)
            recalls[tripId] = recall_score(gt_path_vectors[tripId], tempVector)

            # pathLength = 0
            # intersectionLength = 0
            # for i in range(0, len(pathNodes) - 1):
            #     e = (pathNodes[i], pathNodes[i + 1])
            #     pathLength += G.edges[e[0], e[1]]['length']
            #     if e in gt_path_edges[tripId]:
            #         intersectionLength += G.edges[e[0], e[1]]['length']
            #
            # recallsATn[tripId] = intersectionLength / gt_path_lengths[tripId]
            # accuracies[tripId] = intersectionLength / max(gt_path_lengths[tripId], pathLength)
    return precisions, recalls


def get_stats_multi_file(G: list, ground_truth_dir, result_dir) -> tuple:
    precisions = {}
    recalls = {}

    for filename in os.listdir(result_dir):
        ground_truth_file = os.path.join(ground_truth_dir, filename)
        result_file = os.path.join(result_dir, filename)
        p, r = get_stats_single_file(G, ground_truth_file, result_file)
        precisions |= p
        recalls |= r

    return precisions, recalls


if __name__ == "__main__":
    pen_lopt_dir = 'datasets/porto_small/resources/pen-lopt'

    (precision, recall, recall_at_n, accuracy) = load_precisions(pen_lopt_dir)
    print(precision)
    print(recall)
    print(recall_at_n)
    print(accuracy)

    # parser = argparse.ArgumentParser()
    # parser.add_argument("graphml", help="Path to graphml file use.", type=str)
    # parser.add_argument("ground_truth_file", help="Path to ground truth file containing mapmatched paths.", type=str)
    # parser.add_argument("result_file", help="Path to result file.", type=str)
    # args = parser.parse_args()
    #
    # G = ox.load_graphml(args.graphml)
    # G = ox.get_digraph(G, weight='length')
    # # G_nodes = list(G.nodes)
    #
    # precisions, recalls = get_stats_single_file(G, args.ground_truth_file, args.result_file)
    # # precisions, recalls = get_stats_multi_file(G, args.ground_truth_file, args.result_file)
    #
    # print("-------------")
    # print("precision = ", (sum(precisions.values()) / len(precisions)))
    # print("recall = ", (sum(recalls.values()) / len(recalls)))
