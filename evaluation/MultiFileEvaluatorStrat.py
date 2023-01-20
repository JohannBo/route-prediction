import configparser
import os

import osmnx as ox
from Strategy import Strategy

from evaluation import EvalUtil


class MultiFileEvaluatorStrat(Strategy):

    def __init__(self, config: configparser.ConfigParser, input_method: str) -> None:
        eval_method = 'eval-' + input_method
        train_file_name = config['DEFAULT']['train_file_name']
        fmm_output_path = config['fmm']['output_path']
        input_method_output_path = config[input_method]['output_path']

        self._output_path = config[eval_method]['output_path']
        self._input_method_output_file_path = os.path.join(input_method_output_path, train_file_name)
        self._train_file_path = os.path.join(fmm_output_path, train_file_name)
        self._output_file_path = os.path.join(self._output_path, train_file_name)
        self._graphml_file_path = config['osm']['graphml_file_path']

    def do_algorithm(self) -> None:
        G = ox.load_graphml(self._graphml_file_path)
        G = ox.get_digraph(G, weight='length')

        precisions, recalls = EvalUtil.get_stats_single_file(G, self._train_file_path,
                                                             self._input_method_output_file_path)

        if not os.path.exists(self._output_file_path):
            os.makedirs(self._output_file_path)

        precision_file_path = os.path.join(self._output_file_path, 'precision.csv')
        EvalUtil.save_stat_file(precision_file_path, precisions)

        recall_file_name = os.path.join(self._output_file_path, 'recall.csv')
        EvalUtil.save_stat_file(recall_file_name, recalls)
