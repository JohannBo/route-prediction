from __future__ import annotations

import configparser
import os

import networkx as nx
import numpy as np
import osmnx as ox
import pandas as pd
from Strategy import Strategy


class OsmDownloaderStrat(Strategy):

    def __init__(self, config: configparser.ConfigParser) -> None:
        self._place = config['osm']['place']
        self._path = config['osm']['output_path']
        self._speed_limits_path = config['osm']['speed_limits_path']
        self._cache_path = config['osm']['cache_path']
        self._graphml_file_path = config['osm']['graphml_file_path']

    def _stringify_nonnumeric_cols(self, gdf):
        for col in (c for c in gdf.columns if not c == "geometry"):
            if not pd.api.types.is_numeric_dtype(gdf[col]):
                gdf[col] = gdf[col].fillna("").astype(str)
        return gdf

    def _save_graph_shapefile_directional(self, G, filepath, encoding="utf-8"):
        # if save folder does not already exist, create it (shapefiles
        # get saved as set of files)
        if not filepath == "" and not os.path.exists(filepath):
            os.makedirs(filepath)
        filepath_nodes = os.path.join(filepath, "nodes.shp")
        filepath_edges = os.path.join(filepath, "edges.shp")

        # convert undirected graph to gdfs and stringify non-numeric columns
        gdf_nodes, gdf_edges = ox.utils_graph.graph_to_gdfs(G)
        gdf_nodes = self._stringify_nonnumeric_cols(gdf_nodes)

        # We need a unique ID for each edge
        # gdf_edges['fid'] = gdf_edges.index.to_flat_index()  # this didn't work right, so we use a numeric id instead
        gdf_edges['fid'] = np.arange(0, gdf_edges.shape[0])
        gdf_edges = self._stringify_nonnumeric_cols(gdf_edges)

        # save the nodes and edges as separate ESRI shapefiles
        gdf_nodes.to_file(filepath_nodes, encoding=encoding)
        gdf_edges.to_file(filepath_edges, encoding=encoding)

    def _save_speeds(self, G) -> None:
        G_speeds = ox.add_edge_speeds(G)
        edge_list = nx.to_pandas_edgelist(G_speeds)

        only_speeds = edge_list[['source', 'target', 'speed_kph']]
        only_speeds = only_speeds.drop_duplicates()
        only_speeds.to_csv(self._speed_limits_path, index=False)

        # plot speed limits
        # ec = ox.plot.get_edge_colors_by_attr(G_speeds, 'speed_kph', cmap='plasma')
        # fig, ax = ox.plot_graph(G_speeds, node_alpha=0.1, edge_color=ec)

    def do_algorithm(self) -> None:

        ox.utils.config(cache_folder=self._cache_path)

        # Download by place name
        print("Downloading map: ", self._place)
        # which result selects the polygon of the result set. I can apparently be different.
        # It can be checked by using the search bar of osm.org.
        # It is best to choose a search term that gives the preferred region as first result.
        # 'None'/Default should select the first valid one.
        # G = ox.graph_from_place(self._place, network_type='drive', which_result=2)
        G = ox.graph_from_place(self._place, network_type='drive')

        print("Saving shapefile")
        self._save_graph_shapefile_directional(G, filepath=self._path)

        print("Saving speed limits")
        self._save_speeds(G)

        print("Saving Graph as graphml")
        G = ox.add_edge_speeds(G)
        G = ox.add_edge_travel_times(G)
        ox.save_graphml(G, self._graphml_file_path)
