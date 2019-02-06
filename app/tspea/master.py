import os
import logging
import numpy as np
from deap import base, tools
from .fitness import TSPInstance, EvalTSPSolution, EvalTSPSolutionFragment
from .population import init_population, save_population, save_best_individual
from .messaging import publish_tasks, send_term_signals
from .algorighms import ea_simple, write_stats, load_stats

Log = logging.getLogger(__name__)

POP_SIZE = int(os.getenv('POP_SIZE', 2))
NUM_GENS = int(os.getenv('NUM_GENS', 2))
CROSSOVER_PROB = float(os.getenv('CROSSOVER_PROB', .7))
MUTATION_PROB = float(os.getenv('MUTATION_PROB', 1.0))


def run(cities_file, broker_url, out_dir):
    Log.info('Starting master...')
    toolbox = base.Toolbox()
    tsp_instance = TSPInstance(cities_file)
    toolbox.register('evaluate', EvalTSPSolution(tsp_instance))
    toolbox.register('evaluate_fragment', EvalTSPSolutionFragment(tsp_instance))
    toolbox.register('select', tools.selTournament, tournsize=3)
    toolbox.register('population', init_population, num_cities=tsp_instance.size(), in_dir=out_dir)
    toolbox.register('publish_tasks', publish_tasks, broker_url=broker_url)
    toolbox.register('save_population', save_population, out_dir=out_dir)
    toolbox.register('save_best_individual', save_best_individual, out_dir=out_dir)
    toolbox.register('write_stats', write_stats, stats_file=os.path.join(out_dir, 'stats.csv'))
    toolbox.register('load_stats', load_stats, stats_file=os.path.join(out_dir, 'stats.csv'))

    hof = tools.HallOfFame(1)
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", np.mean)
    stats.register("std", np.std)
    stats.register("min", np.min)
    stats.register("max", np.max)

    pop = toolbox.population(pop_size=POP_SIZE)
    try:
        ea_simple(pop, toolbox, CROSSOVER_PROB, MUTATION_PROB, NUM_GENS, stats=stats, halloffame=hof)
        send_term_signals(broker_url, retries=2)
    finally:
        toolbox.save_best_individual(hof)

