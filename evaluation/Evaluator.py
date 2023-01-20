import matplotlib.pyplot as plt
import csv
import ast
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, precision_recall_fscore_support
import os
from util import Util
from util import HighwayExtractor
import configparser
import datetime
import numpy as np
import networkx as nx
import osmnx as ox

if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.sections()
    config.read('conf.ini')

    dataset = 'porto'
    train_file_name = 'trajectories_2013-07-01.csv'
    config['DEFAULT']['dataset'] = dataset
    config[dataset]['train_file_name'] = train_file_name

    config['DEFAULT']['base_path'] = config[dataset]['base_path']
    config['osm']['place'] = config[dataset]['place']
    config['fmm']['trajectory_interval'] = config[dataset]['trajectory_interval']
    config['DEFAULT']['train_file_name'] = config[dataset]['train_file_name']

    graphml_file_path = config['osm']['graphml_file_path']

    G = ox.load_graphml(graphml_file_path)
    G = ox.get_digraph(G)

    print('G nodes', len(G.nodes()))
    print('G edges', len(G.edges()))
    G_nodes = list(G.nodes)
