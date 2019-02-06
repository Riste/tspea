import random
import logging
import os
import csv
from deap import tools
from .messaging import ID, FIRST, SECOND, GEN, TYPE, MATE, MUTATE
from collections.abc import Iterable

Log = logging.getLogger(__name__)
_STATS_DELIMITER = ','


def write_stats(header, stats, stats_file):
    out_file_exists = os.path.exists(stats_file)
    with open(stats_file, 'a') as f:
        if not out_file_exists:
            f.write('%s\n' % _STATS_DELIMITER.join(header))
        f.write('%s\n' % _STATS_DELIMITER.join(map(str, stats)))


def load_stats(stats_file):
    if not os.path.exists(stats_file):
        return []
    with open(stats_file, 'r') as f:
        reader = csv.reader(stats_file, delimiter=_STATS_DELIMITER)
        return [row for row in reader]


def _apply_to_population(pop, idxs, inds_vals):
    if isinstance(idxs, Iterable):
        for idx, ind_vals in zip(idxs, inds_vals):
            for i in range(len(pop[idx])):
                pop[idx][i] = ind_vals[i]
    else:
        for i in range(len(pop[idxs])):
            pop[idxs][i] = inds_vals[i]


def _var_and(population, toolbox, cxpb, mutpb, gen):
    offspring = [toolbox.clone(ind) for ind in population]

    # Apply crossover and mutation on the offspring
    mate_tasks = []
    for i in range(1, len(offspring), 2):
        if random.random() < cxpb:
            mate_tasks.append({ID: (i-1, i), TYPE: MATE, GEN: gen,
                               FIRST: list(offspring[i-1]),
                               SECOND: list(offspring[i])})
            del offspring[i - 1].fitness.values, offspring[i].fitness.values
    Log.info('Performing crossover...')
    mate_results = toolbox.publish_tasks(mate_tasks)
    for r in mate_results:
        _apply_to_population(offspring, r[ID], [r[FIRST], r[SECOND]])

    mutate_tasks = []
    for i in range(len(offspring)):
        if random.random() < mutpb:
            mutate_tasks.append({ID: i, TYPE: MUTATE, GEN: gen, FIRST: list(offspring[i])})
            del offspring[i].fitness.values
    Log.info('Performing mutation...')
    mutate_results = toolbox.publish_tasks(mutate_tasks)
    for r in mutate_results:
        _apply_to_population(offspring, r[ID], r[FIRST])

    return offspring


def ea_simple(population, toolbox, cxpb, mutpb, ngen, stats=None, halloffame=None, verbose=__debug__, elitism=True):

    logbook = tools.Logbook()
    logbook.header = ['gen', 'nevals'] + (stats.fields if stats else [])

    # Evaluate the individuals with an invalid fitness
    invalid_ind = [ind for ind in population if not ind.fitness.valid]
    fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
    for ind, fit in zip(invalid_ind, fitnesses):
        ind.fitness.values = fit

    if halloffame is not None:
        halloffame.update(population)

    record = stats.compile(population) if stats else {}
    logbook.record(gen=0, nevals=len(invalid_ind), **record)
    if verbose:
        Log.info(logbook.stream)

    if stats:
        toolbox.write_stats(stats.fields, [record[f] for f in stats.fields])

    current_gen = len(toolbox.load_stats())

    # Begin the generational process
    for gen in range(current_gen, ngen + 1):
        # Select the next generation individuals
        offspring = toolbox.select(population, len(population))

        # Vary the pool of individuals
        offspring = _var_and(offspring, toolbox, cxpb, mutpb, gen)

        # Evaluate the individuals with an invalid fitness
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit

        # Update the hall of fame with the generated individuals
        if halloffame is not None:
            halloffame.update(offspring)

        # Replace the current population by the offspring
        if elitism:
            _, bp = _find_extreme_individual(population, _cmp)
            wo_idx, _ = _find_extreme_individual(offspring, cmp=lambda a, b: -_cmp(a, b))
            population[:] = offspring
            population[wo_idx] = bp  # replace worst offspring with best parent
        else:
            population[:] = offspring

        toolbox.save_population(population)

        # Append the current generation statistics to the logbook
        record = stats.compile(population) if stats else {}
        logbook.record(gen=gen, nevals=len(invalid_ind), **record)
        if verbose:
            print(logbook.stream)
        if stats:
            toolbox.write_stats(stats.fields, [record[f] for f in stats.fields])
        toolbox.save_best_individual(halloffame)
    return population, logbook


def _cmp(a, b):
    return int(a > b) - int(a < b)


def _find_extreme_individual(pop, cmp):
    eidx, eind = 0, pop[0]
    for idx in range(1, len(pop)):
        if cmp(pop[idx].fitness.values, eind.fitness.values) == -1:
            eidx = idx
            eind = pop[idx]
    return eidx, eind

