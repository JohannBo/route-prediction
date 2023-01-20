# History Oblivious Route Recovery on Road Networks

This is the source code for the paper "History Oblivious Route Recovery on Road Networks".
DOI: https://doi.org/10.1145/3557915.3560979


# Preparation of environment

## install fmm
https://fmm-wiki.github.io/docs/installation/

## prepare python

`pip install osmnx scikit-learn jupyter geopandas fiona shapely networkx`



# Preparing dataset

Test with small included test dataset first:
parameter: "-ds porto_small"

For other datasets, the train file must be in the corresponding directory.
See conf.ini file for paths.

We used:
https://www.kaggle.com/datasets/crailtap/taxi-trajectory

## Download Map

`python Main.py -ds porto_small -osm`

## Mapmatching of training data

`python Main.py -ds porto_small -fmm`



# Running strategies

List all strategies with `python Main.py --help`.


## Example: Single via Paths

`python Main.py -ds porto_small -vp`

Some strategies need the results from others. E.g., "-svp-lopt" needs "-vp".

**Note: the code for k-shortest paths is not included because we calculated the results with an external library. Therefore, all "-kspd" strategies will not work unless you import results manually.**

Multiple strategies can also be run in a single command:

`python Main.py -ds porto_small -vp -svp-lopt`

# Evaluation

charts are generated in a jupyter notebook: "charts.ipynb"


