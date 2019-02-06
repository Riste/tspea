import numpy as np
import pandas as pd


class TSPInstance(object):
    def __init__(self, cities_file):
        with open(cities_file) as f:
            cities_df = pd.read_csv(f, sep=',', index_col=0)
            self.num_cities = len(cities_df)
            self.cities = np.empty((self.num_cities, 2), dtype=np.float64)
            for i in cities_df.index.values:
                self.cities[i, 0] = cities_df.loc[i, 'X']
                self.cities[i, 1] = cities_df.loc[i, 'Y']
            self.primes = set([p for p in self.__primes_sieve(self.num_cities)])

    @staticmethod
    def __primes_sieve(limit):
        a = [True] * limit  # Initialize the primality list
        a[0] = a[1] = False
        for (i, is_prime) in enumerate(a):
            if is_prime:
                yield i
                for n in range(i * i, limit, i):  # Mark factors non-prime
                    a[n] = False

    def distance(self, start, end):
        return np.sqrt(np.sum(np.square(self.cities[end] - self.cities[start])))

    def step_distance(self, start, end, step_number):
        d = self.distance(start, end)
        if step_number % 10 == 0 and start not in self.primes:
            d += 0.1 * d
        return d

    def size(self):
        return self.num_cities


class EvalTSPSolution(object):
    def __init__(self, tsp_instance):
        self.tsp_instance = tsp_instance

    def __call__(self, individual):
        distance, prev, step_num = 0., 0, 1
        for i in individual:
            distance += self.tsp_instance.step_distance(prev, i, step_num)
            prev = i
            step_num += 1
        distance += self.tsp_instance.step_distance(prev, 0, step_num)
        return distance,


class EvalTSPSolutionFragment(object):
    def __init__(self, tsp_instance):
        self.tsp_instance = tsp_instance

    def __call__(self, individual, fragment, start):
        assert start > -1
        assert start + len(fragment) <= len(individual)
        distance, step_num = 0., start + 1
        prev = 0 if start == 0 else individual[start - 1]
        for i in fragment:
            distance += self.tsp_instance.step_distance(prev, i, step_num)
            prev = i
            step_num += 1
        next_ind = start + len(fragment)
        distance += self.tsp_instance.step_distance(fragment[-1],
                                                    0 if next_ind == len(individual) else individual[next_ind],
                                                    step_num + 1)
        return distance
