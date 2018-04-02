from __future__ import print_function

import os
import sys
import logging
import argparse
try:
    import configparser
except ImportError:
    import ConfigParser as configparser

import pandas as pd
import numpy as np

file_path = os.path.dirname(os.path.realpath(__file__))
lib_path = os.path.abspath(os.path.join(file_path, '..', 'common'))
sys.path.append(lib_path)
# lib_path2 = os.path.abspath(os.path.join(file_path, '..', '..', 'common'))
# sys.path.append(lib_path2)

import p1_common

logger = logging.getLogger(__name__)


def common_parser(parser):
    parser.add_argument("--config-file", dest='config_file', type=str,
                        default=os.path.join(file_path, 'uno_default_model.txt'),
                        help="specify model configuration file")

    # Parse has been split between arguments that are common with the default neon parser
    # and all the other options
    parser = p1_common.get_default_neon_parse(parser)
    parser = p1_common.get_p1_common_parser(parser)

    # Arguments that are applicable just to uno
    parser = uno_parser(parser)

    return parser


def uno_parser(parser):
    parser.add_argument('--by_cell',
                        default=None,
                        help='sample ID for building a by-cell model')
    parser.add_argument('--by_drug',
                        default=None,
                        help='drug ID or name for building a by-drug model')
    parser.add_argument("--train_sources", nargs='+',
                        default=argparse.SUPPRESS,
                        choices=['all', 'CCLE', 'CTRP', 'gCSI', 'GDSC', 'NCI60', 'SCL', 'SCLC', 'ALMANAC'],
                        help="use one or more sources of drug response data for training")
    parser.add_argument("--test_sources", nargs='+',
                        default=argparse.SUPPRESS,
                        choices=['train', 'all', 'CCLE', 'CTRP', 'gCSI', 'GDSC', 'NCI60', 'SCL', 'SCLC', 'ALMANAC'],
                        help="use one or more sources of drug response data for testing")
    parser.add_argument("--cell_features", nargs='+',
                        default=argparse.SUPPRESS,
                        choices=['expression', 'mirna', 'proteome', 'all', 'expression_5platform', 'expression_u133p2', 'rnaseq', 'categorical'],
                        help="use one or more cell line feature sets: 'expression', 'mirna', 'proteome', 'all'; use all for ['expression', 'mirna', 'proteome']; use 'categorical' for one-hot encoded cell lines")
    parser.add_argument("--drug_features", nargs='+',
                        default=argparse.SUPPRESS,
                        choices=['descriptors', 'latent', 'all', 'categorical', 'noise'],
                        help="use dragon7 descriptors, latent representations from Aspuru-Guzik's SMILES autoencoder, or both, or one-hot encoded drugs, or random features; 'descriptors','latent', 'all', 'categorical', 'noise'")
    parser.add_argument('--dense_feature_layers', nargs='+', type=int,
                        default=argparse.SUPPRESS,
                        help='number of neurons in intermediate dense layers in the feature encoding submodels')
    parser.add_argument("--use_landmark_genes", action="store_true",
                        help="use the 978 landmark genes from LINCS (L1000) as expression features")
    parser.add_argument("--residual", action="store_true",
                        help="add skip connections to the layers")
    parser.add_argument('--reduce_lr', action='store_true',
                        help='reduce learning rate on plateau')
    parser.add_argument('--warmup_lr', action='store_true',
                        help='gradually increase learning rate on start')
    parser.add_argument('--base_lr', type=float,
                        default=None,
                        help='base learning rate')
    parser.add_argument('--cp', action='store_true',
                        help='checkpoint models with best val_loss')
    parser.add_argument('--tb', action='store_true',
                        help='use tensorboard')
    parser.add_argument('--max_val_loss', type=float,
                        default=argparse.SUPPRESS,
                        help='retrain if val_loss is greater than the threshold')
    parser.add_argument("--partition_by",
                        choices=['index', 'drug_pair', 'cell'],
                        default=None,
                        help="cross validation paritioning scheme")
    parser.add_argument("--cv", type=int,
                        default=argparse.SUPPRESS,
                        help="cross validation folds")
    parser.add_argument("--gen", action="store_true",
                        help="use generator for training and validation data")
    parser.add_argument("--cache",
                        default=None,
                        help="prefix of data cache files to use")
    return parser


def read_config_file(file):
    config = configparser.ConfigParser()
    config.read(file)
    section = config.sections()

    args = [['activation', 'batch_size', 'dense', 'dense_feature_layers', 'drop',
             'epochs', 'learning_rate', 'loss', 'optimizer', 'residual', 'rng_seed',
             'save', 'scaling', 'feature_subsample', 'validation_split'],
            ['solr_root', 'timeout']]

    file_params = {}
    for i, sec_args in enumerate(args):
        for arg in sec_args:
            file_params[arg] = eval(config.get(section[i], arg))

    # parse the remaining values
    for k, v in config.items(section[0]):
        if not k in file_params:
            file_params[k] = eval(v)

    return file_params