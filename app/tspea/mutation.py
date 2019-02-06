import numpy as np


def _index_neighbourhood(p, k, individual):
    r = k // 2
    return [i for i in range(max(0, p - r), min(len(individual), p + r)) if i != p]


def _urand_neighbourhood(p, k, individual):
    return [i for i in np.random.choice(range(1, len(individual)), k, replace=False) if i != p]


class TwoOptMutate(object):
    def __init__(self, dist, eval_tsp, eval_tsp_fragment):
        self.dist = dist
        self.eval_tsp = eval_tsp
        self.eval_tsp_fragment = eval_tsp_fragment

    def __euclid_dist_rand_neighbourhood(self, p, k, individual):
        euclid_dists_to_p = np.array([self.dist(individual[p], individual[i]) for i in range(len(individual))])
        p_dist = 1. / (euclid_dists_to_p + 1.)
        p_dist[p] = 0.
        p_dist = p_dist / p_dist.sum()
        return np.random.choice(range(len(individual)), k, replace=False, p=p_dist)

    def __call__(self, individual, k, rmp=0.5):
        total_gain = 0.0
        p = np.random.randint(len(individual))
        neighbourhood_func = self.__euclid_dist_rand_neighbourhood if np.random.rand() < rmp else _index_neighbourhood
        for n in neighbourhood_func(p, k, individual):
            p1, p2 = min(p, n), max(p, n)
            fragment = list(individual[p1:p2+1])
            frag_len = self.eval_tsp_fragment(individual, fragment, p1)
            min_len, min_frag = frag_len, None
            nfragment = [individual[p2]] + list(individual[p1 + 1: p2]) + [individual[p1]]
            nfrag_len = self.eval_tsp_fragment(individual, nfragment, p1)
            if nfrag_len < min_len:
                min_len = nfrag_len
                min_frag = nfragment
            nfragment = [individual[p2]] + list(individual[p2-1: p1:-1]) + [individual[p1]]
            nfrag_len = self.eval_tsp_fragment(individual, nfragment, p1)
            if nfrag_len < min_len:
                min_frag = nfragment
            if min_frag:
                start_ind_len, = self.eval_tsp(individual)
                for j in range(len(min_frag)):
                    individual[p1 + j] = min_frag[j]
                assert len(individual) == len(set(individual))
                end_ind_len, = self.eval_tsp(individual)
                gain = start_ind_len - end_ind_len
                total_gain += gain
        print(' [...] Achieved gain :%f' % total_gain)
        return individual,

