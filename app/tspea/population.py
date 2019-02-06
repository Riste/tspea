import array
import numpy as np
import os
import shutil
import logging
from deap import base, creator
from collections import Iterable


Log = logging.getLogger(__name__)

POP_DIR_NAME = 'population'
NEW_POP_DIR_NAME = 'new_population'
BEST_INDIVIDUAL_FNAME = 'best_individual.csv'


creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
creator.create("Individual", array.array, typecode='i', fitness=creator.FitnessMin)


def generate_population(num_cities, pop_size):
    cities = [i for i in range(1, num_cities)]
    return [creator.Individual(np.random.choice(cities, num_cities - 1, replace=False)) for i in range(pop_size)]


def individual_from(source):
    if isinstance(source, str):
        with open(source) as f:
            ls = [l.strip() for l in f.readlines()]
            indexes = [int(l) for l in ls if l]
            return creator.Individual(indexes)
    elif isinstance(source, Iterable):
        return creator.Individual(source)
    else:
        raise Exception('Invalid individual creation method!')


def init_population(num_cities, in_dir, pop_size=None):
    assert in_dir is not None
    Log.info('Initializing population...')
    pop_dir = os.path.join(in_dir, POP_DIR_NAME)
    if not os.path.exists(in_dir) or not os.path.exists(pop_dir):
        Log.info('Generating individuals randomly...')
        return generate_population(num_cities, pop_size)
    inds_fnames = os.listdir(pop_dir)
    if len(inds_fnames):
        Log.info('Loading population from disk...')
        return [individual_from(os.path.join(pop_dir, fname)) for fname in inds_fnames]
    else:
        Log.info('Generating individuals randomly...')
        return generate_population(num_cities, pop_size)


def _create_dirs(out_dir):
    assert out_dir is not None
    if not os.path.exists(out_dir):
        os.makedirs(os.path.join(out_dir, POP_DIR_NAME))
        return
    pop_dir = os.path.join(out_dir, POP_DIR_NAME)
    if not os.path.exists(pop_dir):
        os.makedirs(pop_dir)


def save_individual(individual, out):
    with open(out, 'w') as f:
        for i in individual:
            f.write('%d\n' % i)


def save_best_individual(halloffame, out_dir):
    if len(halloffame):
        Log.info('Saving best individual. Achieved fitness: %f' % halloffame[0].fitness.values[0])
        save_individual(halloffame[0], os.path.join(out_dir, BEST_INDIVIDUAL_FNAME))


def save_population(population, out_dir):
    assert out_dir is not None
    Log.info('Saving population...')
    Log.info('Checking directory structure...')
    _create_dirs(out_dir)
    Log.info('Creating new population directory...')
    new_pop_dir = os.path.join(out_dir, NEW_POP_DIR_NAME)
    if os.path.exists(new_pop_dir):
        shutil.rmtree(new_pop_dir)
    os.mkdir(new_pop_dir)
    Log.info('Saving individuals...')
    for i, ind in enumerate(population):
        out = os.path.join(new_pop_dir, '%d.csv' % i)
        save_individual(ind, out)
    Log.info('Deleting previous population directory...')
    shutil.rmtree(os.path.join(out_dir, POP_DIR_NAME))
    Log.info('Renaming population folder...')
    shutil.move(new_pop_dir, os.path.join(out_dir, POP_DIR_NAME))




