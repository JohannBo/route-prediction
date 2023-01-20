import ast
import csv
import os

import geopandas as gpd
from fmm import FastMapMatch, Network, NetworkGraph, UBODTGenAlgorithm, UBODT, FastMapMatchConfig
from shapely.geometry import LineString

from Strategy import Strategy
import configparser


class UbodtGeneratorStrat(Strategy):

    def __init__(self, config: configparser.ConfigParser) -> None:
        self._osm_path = config['osm']['output_path']
        self._fmm_path = config['fmm']['output_path']
        self._path_edges = os.path.join(self._osm_path, "edges.shp")
        self._ubodt_path = os.path.join(self._fmm_path, "ubodt.txt")

    def do_algorithm(self) -> None:
        if not os.path.exists(self._fmm_path):
            print("Creating output directory: ", self._fmm_path)
            os.makedirs(self._fmm_path)

        ### Read network data
        print("Opening network")
        network = Network(self._path_edges, "fid", "u", "v")
        # print("Nodes {} edges {}".format(network.get_node_count(), network.get_edge_count()))
        graph = NetworkGraph(network)

        ### Precompute an UBODT table
        print("Generating UBODT")
        ubodt_gen = UBODTGenAlgorithm(network, graph)
        status = ubodt_gen.generate_ubodt(self._ubodt_path, 0.02, binary=False, use_omp=True)
        print("Status: ", status)
