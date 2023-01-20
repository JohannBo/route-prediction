import ast
import configparser
import csv
import os

import networkx as nx
from Strategy import Strategy
from fmm import FastMapMatch, Network, NetworkGraph, UBODT, FastMapMatchConfig
from shapely.geometry import LineString
from util import Util


def _get_path_duration(G, path):
    start = [path[0][0]]
    tail = list(map(lambda n: n[1], path))
    path = start + tail
    duration = nx.path_weight(G, path, 'weight_duration')
    return duration


# get (u, v) tuple for edges based on fid
def _get_nodes(G, edge_fid):
    return next(filter(lambda edge: (G.get_edge_data(*edge)['fid'] in [edge_fid]), G.edges), None)


class MapMatchingStrat(Strategy):

    def __init__(self, config: configparser.ConfigParser) -> None:
        self._osm_path = config['osm']['output_path']
        self._speed_limits_path = config['osm']['speed_limits_path']

        self._fmm_path = config['fmm']['output_path']
        self._fmm_file_name = config['DEFAULT']['train_file_name']
        self._ubodt_path = os.path.join(self._fmm_path, "ubodt.txt")
        self._train_data_path = config['fmm']['train_data_path']
        self._trajectory_interval = int(config['fmm']['trajectory_interval'])

        self._k = int(config['fmm']['k'])
        self._radius = float(config['fmm']['radius'])
        self._gps_error = float(config['fmm']['gps_error'])
        self._path_edges = os.path.join(self._fmm_path, "edges.shp")

    def _match_row(self, model, fmm_config, line):
        ls = LineString(ast.literal_eval(line))
        result = model.match_wkt(ls.wkt, fmm_config)
        return result

    def _do_mapmatching(self, model, fmm_config, input_path, output_path):

        # loading graph
        path_edges = os.path.join(self._osm_path, "edges.shp")
        path_nodes = os.path.join(self._osm_path, "nodes.shp")
        G = Util.load_graph(path_edges, path_nodes, self._speed_limits_path)

        output_path = os.path.join(output_path, self._fmm_file_name)
        input_path = os.path.join(input_path, self._fmm_file_name)

        with open(input_path, newline='', encoding='utf-8') as input_file:
            lines = len(input_file.readlines())
            print('lines: ', lines)

        with open(input_path, newline='', encoding='utf-8') as input_file, open(output_path, 'w', newline='',
                                                                                encoding='utf-8') as output_file:
            r = csv.DictReader(input_file, delimiter=',')
            fieldnames = r.fieldnames
            fieldnames.append('START_NODE')
            fieldnames.append('END_NODE')
            fieldnames.append('CPATH')
            fieldnames.append('OPATH')
            fieldnames.append('REAL_DURATION')
            fieldnames.append('MAPPED_DURATION')
            w = csv.DictWriter(output_file, fieldnames=fieldnames, quotechar='"', quoting=csv.QUOTE_ALL)
            w.writeheader()

            i = 0
            for row in r:
                i += 1
                if i % 1000 == 0:
                    print(i / lines * 100, "%")
                try:
                    row_result = self._match_row(model, fmm_config, row['POLYLINE'])

                    cpath = list(row_result.cpath)
                    opath = list(row_result.opath)
                    cpath = list(map(lambda fid: _get_nodes(G, fid), cpath))
                    opath = list(map(lambda fid: _get_nodes(G, fid), opath))

                    if len(cpath) > 1 and None not in cpath:
                        first_edge = cpath[0]
                        last_edge = cpath[-1]

                        row['START_NODE'] = first_edge[0]
                        row['END_NODE'] = last_edge[1]
                        row['CPATH'] = cpath
                        row['OPATH'] = opath

                        # determine real duration
                        poly = ast.literal_eval(row['POLYLINE'])
                        trajectory_duration = (len(poly) - 1) * self._trajectory_interval
                        row['REAL_DURATION'] = trajectory_duration

                        # determine mapped duration. based on speed limits and distance of mapped path
                        mapped_duration = _get_path_duration(G, cpath)
                        row['MAPPED_DURATION'] = mapped_duration

                        w.writerow(row)
                    else:
                        print('Missing Edges')
                except ValueError:
                    print('ValueError')
                except RuntimeError:
                    print('RuntimeError')

            print('done')

    def do_algorithm(self) -> None:
        path_edges = os.path.join(self._osm_path, "edges.shp")

        # Read network data
        print("Loading network")
        network = Network(path_edges, "fid", "u", "v")

        print("Nodes {} edges {}".format(network.get_node_count(), network.get_edge_count()))
        graph = NetworkGraph(network)

        print("Loading UBODT")
        if not os.path.exists(self._ubodt_path):
            raise FileNotFoundError(self._ubodt_path)
        ubodt = UBODT.read_ubodt_csv(self._ubodt_path)

        print("Creating model")
        model = FastMapMatch(network, graph, ubodt)

        fmm_config = FastMapMatchConfig(self._k, self._radius, self._gps_error)

        print('start mapmatching')
        self._do_mapmatching(model, fmm_config, self._train_data_path, self._fmm_path)
