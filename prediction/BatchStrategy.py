import configparser
import csv
import os
import time
import datetime
import pandas as pd
import itertools

import networkx as nx
import osmnx as ox
from scipy.optimize import lsq_linear
import numpy as np

from Strategy import Strategy
from util import HighwayExtractor


class BatchStrat(Strategy):

    def __init__(self, config: configparser.ConfigParser, batch_size) -> None:
        method_name = 'batch-' + batch_size
        self.batch_size = batch_size
        self._graphml_file_path = config['osm']['graphml_file_path']
        self._speed_limits_path = config['osm']['speed_limits_path']
        self._fmm_path = config['fmm']['output_path']
        self._train_file_name = config['DEFAULT']['train_file_name']

        self._weight = 'travel_time'
        self._output_dir_path = config[method_name]['output_path']
        self._output_dir_path = os.path.join(self._output_dir_path, self._train_file_name)
        self._output_path = os.path.join(self._output_dir_path, "batch_paths.csv")
        self._highway_path = os.path.join(self._output_dir_path, "highway_types.csv")

    def find_batch_paths(self, g, trips):

        print("Executing batch size ",len(trips))

        result = {}

        if len(trips) == 1:
            (tripid, source, target, real_duration) = trips[0]
            result[tripid] = nx.shortest_path(g, source, target, weight=self._weight)
            return result

        resultEdges = {}
        penalizedEdges = set()

        edges_duration = nx.get_edge_attributes(g, self._weight)
        nx.set_edge_attributes(g, edges_duration, "penalized_duration")

        accessedEdges = set()
        errors = {}
        maxError = 0

        dist = -1
        spath = []

        # First path computation
        for (tripid, source, target, real_duration) in trips:
            dist, spath = nx.single_source_dijkstra(g, source, target, weight="penalized_duration")
            if tripid not in result:
                result[tripid] = []
                resultEdges[tripid] = set()

            for i in range(0, len(spath) - 1):
                accessedEdges.add((spath[i], spath[i + 1]))
                resultEdges[tripid].add((spath[i], spath[i + 1]))
            result[tripid].append(spath)
            errors[tripid] = real_duration - dist
            if (errors[tripid] > maxError):
                maxError = errors[tripid]
        accessedEdgesList = list(accessedEdges)

        prevError = 0

        while abs(sum(errors.values()) / len(errors.values()) - prevError) >= 1:

            prevError = abs(sum(errors.values()) / len(errors.values()))

            # print("Iteration 1")
            resultsLengths = []
            for (tripid, source, target, real_duration) in trips:
                resultsLengths.append(len(result[tripid]))
            # print(resultsLengths)
            # print("error = ",prevError)

            # Computing penalties
            a_matrix = []
            b_matrix = []
            for (tripid, source, target, real_duration) in trips:
                tempVector = []
                # print(resultEdges[tripid])
                for (u, v) in accessedEdgesList:
                    if (u, v) in resultEdges[tripid]:
                        tempVector.append(g.edges[u, v]['penalized_duration'])
                    else:
                        tempVector.append(0)
                a_matrix.append(tempVector)
                b_matrix.append(real_duration)

            a_matrix_rows = len(a_matrix)
            a_matrix_columns = len(a_matrix[0])

            x = lsq_linear(a_matrix, b_matrix, bounds=(1, 5))

            # Applying penalties
            for i in range(0, a_matrix_columns):
                prevWeight = g.edges[accessedEdgesList[i][0], accessedEdgesList[i][1]]['penalized_duration']
                g.edges[accessedEdgesList[i][0], accessedEdgesList[i][1]]['penalized_duration'] *= x.x[i]

            # Initiating next iteration
            errors = {}
            accessedEdges = set()

            for (tripid, source, target, real_duration) in trips:
                dist, spath = nx.single_source_dijkstra(g, source, target, weight="penalized_duration")
                if tripid not in result:
                    result[tripid] = []
                    resultEdges[tripid] = set()
                result[tripid].append(spath)
                for i in range(0, len(spath) - 1):
                    accessedEdges.add((spath[i], spath[i + 1]))
                    resultEdges[tripid].add((spath[i], spath[i + 1]))

                errors[tripid] = abs(real_duration - dist)
            accessedEdgesList = list(accessedEdges)

            print("--> ", prevError, abs(sum(errors.values()) / len(errors.values())), abs(sum(errors.values()) / len(errors.values()) - prevError))

        for (tripid, source, target, real_duration) in trips:
            result[tripid] = result[tripid][:-1]

        # print("Final")
        resultsLengths = []
        for (tripid, source, target, real_duration) in trips:
            resultsLengths.append(len(result[tripid]))
        # print(resultsLengths)
        # print("error = ",prevError)

        edges_duration = nx.get_edge_attributes(g, self._weight)
        nx.set_edge_attributes(g, edges_duration, "penalized_duration")

        return result

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
        with open(trajectory_path, newline='', encoding='utf-8') as trajectory_file:
            trajectory_csv = csv.DictReader(trajectory_file, delimiter=',')

            fieldnames = ['TRIP_ID', 'PATH_ID', 'START_NODE', 'END_NODE', 'NODE_PATH', 'RUNTIME']

            trips = []
            tripTimestamps = {}
            tripTimestampsList = []

            for row in trajectory_csv:
                trip_id = int(row['TRIP_ID'])
                start_node = int(row['START_NODE'])
                end_node = int(row['END_NODE'])
                real_duration = float(row['REAL_DURATION'])
                try:
                    tripTs = datetime.datetime.strptime(row['TIMESTAMP'], '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    tripTs = datetime.datetime.fromtimestamp(int(row['TIMESTAMP']))
                trips.append((trip_id,start_node,end_node,real_duration))
                tripTimestamps[trip_id] = tripTs
                tripTimestampsList.append(tripTs)

            data = {
                "tripid": [x[0] for x in trips],
                "timestamp": tripTimestampsList
            }
            df = pd.DataFrame(data)

            #tripSeries = df.resample('15Min', on='timestamp').tripid.apply(list)
            #tripSeries = df.resample('30Min', on='timestamp').tripid.apply(list)
            #tripSeries = df.resample('1H', on='timestamp').tripid.apply(list)
            tripSeries = df.resample(self.batch_size + 'Min', on='timestamp').tripid.apply(list)
            tripBatches = []
            for row in tripSeries.items():
                tripBatches.append(row[1])

            print("trajectories split into ",len(tripBatches),"batches.")
            for batch in tripBatches:

                batchQuery = [x for x in trips if x[0] in batch]
                recoveredTrips = self.find_batch_paths(G, batchQuery)

                for k, v in recoveredTrips.items():
                    v_prime = v
                    v_prime.sort()
                    v_prime = list(k for k, _ in itertools.groupby(v_prime))
                    trip_output_file_name = os.path.join(self._output_dir_path, str(k) + '.csv')
                    with open(trip_output_file_name, 'w', newline='', encoding='utf-8') as output_file:
                        w = csv.DictWriter(output_file, fieldnames=fieldnames, quotechar='"', quoting=csv.QUOTE_ALL)
                        w.writeheader()
                        path_id = 0
                        for node_path in v_prime:
                            new_row = {'TRIP_ID': k, 'PATH_ID': path_id, 'START_NODE': node_path[0],
                                       'END_NODE': node_path[-1], 'NODE_PATH': node_path}
                            w.writerow(new_row)
                            path_id += 1
