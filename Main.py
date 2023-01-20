import argparse
import configparser
import os

import evaluation.MultiFileEvaluatorStrat as mfes
import evaluation.SinglePathEvaluatorStrat as esp
import fastmapmatching.MapMatcher as mm
import fastmapmatching.UbodtGenerator as ug
import osm.OsmDownloader as osm
import prediction.BatchStrategy as bs
import prediction.Penalty as pen
import prediction.ResourceConstrained as rc
import prediction.ShortestPath as sp
import prediction.ViaPaths as vp
import selection.LocalOptimality as lopt
import selection.MinPeaks as minp
import selection.Skyline as skyline
import selection.DiversityStrat as diversity
import selection.SelectAllStrat as all
from Context import Context

"""
Concrete Strategies implement the algorithm while following the base Strategy
interface. The interface makes them interchangeable in the Context.
"""


def dir_path(string):
    if os.path.isdir(string):
        return string
    else:
        raise NotADirectoryError(string)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-ds", "--dataset", help="work directory.", default='porto_small')
    parser.add_argument("-d", "--directory", help="work directory.", type=dir_path, default=None)
    parser.add_argument("-tf", "--train-file", help="train file.", default=None)
    parser.add_argument("-osm", "--openstreetmaps", help="download and prepare openstreetmaps data",
                        action="store_true")
    parser.add_argument("-fmm", "--fastmapmatching", help="run fastmapmatching", action="store_true")
    parser.add_argument("-gh", "--graphhopper", help="run mapmatching using graphhopper", action="store_true")
    parser.add_argument("-sp", "--shortestpath", help="run shortest path", action="store_true")
    parser.add_argument("-fp", "--fastestpath", help="run fastest path", action="store_true")
    parser.add_argument("-rc", "--resource-constrained", help="run resource constrained", action="store_true")
    parser.add_argument("-vp", "--via-paths", help="run via paths", action="store_true")
    parser.add_argument("-pen", "--penalty", help="run penalty strategy", action="store_true")

    parser.add_argument("-bs-15", "--batch-15", help="run batch strategy with batch size 15 min", action="store_true")
    parser.add_argument("-bs-30", "--batch-30", help="run batch strategy with batch size 30 min", action="store_true")
    parser.add_argument("-bs-60", "--batch-60", help="run batch strategy with batch size 60 min", action="store_true")

    parser.add_argument("-svp-all", "--svp-all", help="run min select all strategy on svp results.", action="store_true")
    parser.add_argument("-pen-all", "--pen-all", help="run min select all strategy on penalty results.", action="store_true")
    parser.add_argument("-kspd-all", "--kspd-all", help="run min select all strategy on kspd results.", action="store_true")
    parser.add_argument("-batch-15-all", "--batch-15-all", help="run min select all strategy on batch-15 results.", action="store_true")
    parser.add_argument("-batch-30-all", "--batch-30-all", help="run min select all strategy on batch-30 results.", action="store_true")
    parser.add_argument("-batch-60-all", "--batch-60-all", help="run min select all strategy on batch-60 results.", action="store_true")

    parser.add_argument("-svp-minp", "--svp-min-peaks", help="run min highway peaks strategy on svp results.", action="store_true")
    parser.add_argument("-pen-minp", "--pen-min-peaks", help="run min highway peaks strategy on penalty results.", action="store_true")
    parser.add_argument("-kspd-minp", "--kspd-min-peaks", help="run min highway peaks strategy on kspd results.", action="store_true")
    parser.add_argument("-batch-15-minp", "--batch-15-min-peaks", help="run min highway peaks strategy on batch-15 results.", action="store_true")
    parser.add_argument("-batch-30-minp", "--batch-30-min-peaks", help="run min highway peaks strategy on batch-30 results.", action="store_true")
    parser.add_argument("-batch-60-minp", "--batch-60-min-peaks", help="run min highway peaks strategy on batch-60 results.", action="store_true")

    parser.add_argument("-svp-sky", "--svp-skyline", help="run skyline strategy on svp results.", action="store_true")
    parser.add_argument("-pen-sky", "--pen-skyline", help="run skyline strategy on pen results.", action="store_true")
    parser.add_argument("-kspd-sky", "--kspd-skyline", help="run skyline strategy on kspd results.", action="store_true")
    parser.add_argument("-batch-15-sky", "--batch-15-skyline", help="run skyline strategy on batch-15 results.", action="store_true")
    parser.add_argument("-batch-30-sky", "--batch-30-skyline", help="run skyline strategy on batch-30 results.", action="store_true")
    parser.add_argument("-batch-60-sky", "--batch-60-skyline", help="run skyline strategy on batch-60 results.", action="store_true")

    parser.add_argument("-svp-lopt", "--svp-local-optimality", help="run local optimality strategy on svp results.", action="store_true")
    parser.add_argument("-pen-lopt", "--pen-local-optimality", help="run local optimality strategy on pen results.", action="store_true")
    parser.add_argument("-kspd-lopt", "--kspd-local-optimality", help="run local optimality strategy on kspd results.", action="store_true")
    parser.add_argument("-batch-15-lopt", "--batch-15-local-optimality", help="run local optimality strategy on batch-15 results.", action="store_true")
    parser.add_argument("-batch-30-lopt", "--batch-30-local-optimality", help="run local optimality strategy on batch-30 results.", action="store_true")
    parser.add_argument("-batch-60-lopt", "--batch-60-local-optimality", help="run local optimality strategy on batch-60 results.", action="store_true")

    parser.add_argument("-svp-div-10", "--svp-diversity-10", help="run diversity strategy with 10 percent threshold on svp results.", action="store_true")
    parser.add_argument("-pen-div-10", "--pen-diversity-10", help="run diversity strategy with 10 percent threshold on pen results.", action="store_true")
    parser.add_argument("-kspd-div-10", "--kspd-diversity-10", help="run diversity strategy with 10 percent threshold on kspd results.", action="store_true")
    parser.add_argument("-batch-15-div-10", "--batch-15-diversity-10", help="run diversity strategy with 10 percent threshold on batch-15 results.", action="store_true")
    parser.add_argument("-batch-30-div-10", "--batch-30-diversity-10", help="run diversity strategy with 10 percent threshold on batch-30 results.", action="store_true")
    parser.add_argument("-batch-60-div-10", "--batch-60-diversity-10", help="run diversity strategy with 10 percent threshold on batch-60 results.", action="store_true")

    parser.add_argument("-svp-div-30", "--svp-diversity-30", help="run diversity strategy with 30 percent threshold on svp results.", action="store_true")
    parser.add_argument("-pen-div-30", "--pen-diversity-30", help="run diversity strategy with 30 percent threshold on pen results.", action="store_true")
    parser.add_argument("-kspd-div-30", "--kspd-diversity-30", help="run diversity strategy with 30 percent threshold on kspd results.", action="store_true")
    parser.add_argument("-batch-15-div-30", "--batch-15-diversity-30", help="run diversity strategy with 30 percent threshold on batch-15 results.", action="store_true")
    parser.add_argument("-batch-30-div-30", "--batch-30-diversity-30", help="run diversity strategy with 30 percent threshold on batch-30 results.", action="store_true")
    parser.add_argument("-batch-60-div-30", "--batch-60-diversity-30", help="run diversity strategy with 30 percent threshold on batch-60 results.", action="store_true")

    parser.add_argument("-svp-div-70", "--svp-diversity-70", help="run diversity strategy with 70 percent threshold on svp results.", action="store_true")
    parser.add_argument("-pen-div-70", "--pen-diversity-70", help="run diversity strategy with 70 percent threshold on pen results.", action="store_true")
    parser.add_argument("-kspd-div-70", "--kspd-diversity-70", help="run diversity strategy with 70 percent threshold on kspd results.", action="store_true")
    parser.add_argument("-batch-15-div-70", "--batch-15-diversity-70", help="run diversity strategy with 70 percent threshold on batch-15 results.", action="store_true")
    parser.add_argument("-batch-30-div-70", "--batch-30-diversity-70", help="run diversity strategy with 70 percent threshold on batch-30 results.", action="store_true")
    parser.add_argument("-batch-60-div-70", "--batch-60-diversity-70", help="run diversity strategy with 70 percent threshold on batch-60 results.", action="store_true")

    parser.add_argument("-esp", "--evaluate-shortest-path", help="evaluate shortest path", action="store_true")
    parser.add_argument("-efp", "--evaluate-fastest-path", help="evaluate fastest path", action="store_true")


    args = parser.parse_args()

    config = configparser.ConfigParser()
    config.sections()
    config.read('conf.ini')

    # check which dataset to use, then set dataset dependent config params
    if args.dataset is not None:
        config['DEFAULT']['dataset'] = args.dataset
    dataset = config['DEFAULT']['dataset']
    config['DEFAULT']['base_path'] = config[dataset]['base_path']
    config['osm']['place'] = config[dataset]['place']
    config['fmm']['trajectory_interval'] = config[dataset]['trajectory_interval']
    config['DEFAULT']['train_file_name'] = config[dataset]['train_file_name']

    if args.directory is not None:
        config['DEFAULT']['base_path'] = args.directory
    if args.train_file is not None:
        config['DEFAULT']['train_file_name'] = args.train_file

    print('dataset:', config['DEFAULT']['dataset'])
    print('base path:', config['DEFAULT']['base_path'])

    context = Context()

    if args.openstreetmaps:
        context.append_strategy(osm.OsmDownloaderStrat(config))
    if args.fastmapmatching:
        context.append_strategy(ug.UbodtGeneratorStrat(config))
        context.append_strategy(mm.MapMatchingStrat(config))
    if args.shortestpath:
        context.append_strategy(sp.ShortestPathStrat(config, fastest=False))
    if args.fastestpath:
        context.append_strategy(sp.ShortestPathStrat(config, fastest=True))
    if args.resource_constrained:
        context.append_strategy(rc.ResourceConstrainedStrat(config))
    if args.via_paths:
        context.append_strategy(vp.ViaPathsStrat(config))
    if args.penalty:
        context.append_strategy(pen.PenaltyStrat(config))
    if args.batch_15:
        context.append_strategy(bs.BatchStrat(config, '15'))
    if args.batch_30:
        context.append_strategy(bs.BatchStrat(config, '30'))
    if args.batch_60:
        context.append_strategy(bs.BatchStrat(config, '60'))

    if args.svp_all:
        context.append_strategy(all.SelectAllStrat(config, 'vp'))
    if args.pen_all:
        context.append_strategy(all.SelectAllStrat(config, 'pen'))
    if args.kspd_all:
        context.append_strategy(all.SelectAllStrat(config, 'kspd'))
    if args.batch_15_all:
        context.append_strategy(all.SelectAllStrat(config, 'batch-15'))
    if args.batch_30_all:
        context.append_strategy(all.SelectAllStrat(config, 'batch-30'))
    if args.batch_60_all:
        context.append_strategy(all.SelectAllStrat(config, 'batch-60'))

    if args.svp_min_peaks:
        context.append_strategy(minp.MinPeaksStrat(config, 'vp'))
    if args.pen_min_peaks:
        context.append_strategy(minp.MinPeaksStrat(config, 'pen'))
    if args.kspd_min_peaks:
        context.append_strategy(minp.MinPeaksStrat(config, 'kspd'))
    if args.batch_15_min_peaks:
        context.append_strategy(minp.MinPeaksStrat(config, 'batch-15'))
    if args.batch_30_min_peaks:
        context.append_strategy(minp.MinPeaksStrat(config, 'batch-30'))
    if args.batch_30_min_peaks:
        context.append_strategy(minp.MinPeaksStrat(config, 'batch-60'))

    if args.svp_skyline:
        context.append_strategy(skyline.SkylineStrat(config, 'vp'))
    if args.pen_skyline:
        context.append_strategy(skyline.SkylineStrat(config, 'pen'))
    if args.kspd_skyline:
        context.append_strategy(skyline.SkylineStrat(config, 'kspd'))
    if args.batch_15_skyline:
        context.append_strategy(skyline.SkylineStrat(config, 'batch-15'))
    if args.batch_30_skyline:
        context.append_strategy(skyline.SkylineStrat(config, 'batch-30'))
    if args.batch_60_skyline:
        context.append_strategy(skyline.SkylineStrat(config, 'batch-60'))

    if args.svp_local_optimality:
        context.append_strategy(lopt.LocalOptimalityStrat(config, 'vp'))
    if args.pen_local_optimality:
        context.append_strategy(lopt.LocalOptimalityStrat(config, 'pen'))
    if args.kspd_local_optimality:
        context.append_strategy(lopt.LocalOptimalityStrat(config, 'kspd'))
    if args.batch_15_local_optimality:
        context.append_strategy(lopt.LocalOptimalityStrat(config, 'batch-15'))
    if args.batch_30_local_optimality:
        context.append_strategy(lopt.LocalOptimalityStrat(config, 'batch-30'))
    if args.batch_60_local_optimality:
        context.append_strategy(lopt.LocalOptimalityStrat(config, 'batch-60'))

    if args.svp_diversity_10:
        context.append_strategy(diversity.DiversityStrat(config, 'vp', .1))
    if args.pen_diversity_10:
        context.append_strategy(diversity.DiversityStrat(config, 'pen', .1))
    if args.kspd_diversity_10:
        context.append_strategy(diversity.DiversityStrat(config, 'kspd', .1))
    if args.batch_15_diversity_10:
        context.append_strategy(diversity.DiversityStrat(config, 'batch-15', .1))
    if args.batch_30_diversity_10:
        context.append_strategy(diversity.DiversityStrat(config, 'batch-30', .1))
    if args.batch_60_diversity_10:
        context.append_strategy(diversity.DiversityStrat(config, 'batch-60', .1))

    if args.svp_diversity_30:
        context.append_strategy(diversity.DiversityStrat(config, 'vp', .3))
    if args.pen_diversity_30:
        context.append_strategy(diversity.DiversityStrat(config, 'pen', .3))
    if args.kspd_diversity_30:
        context.append_strategy(diversity.DiversityStrat(config, 'kspd', .3))
    if args.batch_15_diversity_30:
        context.append_strategy(diversity.DiversityStrat(config, 'batch-15', .3))
    if args.batch_30_diversity_30:
        context.append_strategy(diversity.DiversityStrat(config, 'batch-30', .3))
    if args.batch_60_diversity_30:
        context.append_strategy(diversity.DiversityStrat(config, 'batch-60', .3))

    if args.svp_diversity_70:
        context.append_strategy(diversity.DiversityStrat(config, 'vp', .7))
    if args.pen_diversity_70:
        context.append_strategy(diversity.DiversityStrat(config, 'pen', .7))
    if args.kspd_diversity_70:
        context.append_strategy(diversity.DiversityStrat(config, 'kspd', .7))
    if args.batch_15_diversity_70:
        context.append_strategy(diversity.DiversityStrat(config, 'batch-15', .7))
    if args.batch_30_diversity_70:
        context.append_strategy(diversity.DiversityStrat(config, 'batch-30', .7))
    if args.batch_60_diversity_70:
        context.append_strategy(diversity.DiversityStrat(config, 'batch-60', .7))

    if args.evaluate_shortest_path:
        context.append_strategy(esp.SinglePathEvaluatorStrat(config, 'eval-sp'))
    if args.evaluate_fastest_path:
        context.append_strategy(esp.SinglePathEvaluatorStrat(config, 'eval-fp'))

    context.run_strategies()
