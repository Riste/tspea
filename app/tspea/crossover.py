import numpy as np
import itertools
from operator import itemgetter


def _edge_neighbors(ind, neighbour_lists):
    """
    Auxiliary method which computes the list of neighbours of the individual and modifies in place the passed
    neighbour_lists parameter which is assumed to be a numpy array of shape (len(ind) + 1, 4)
    :param ind: Individual
    :param neighbour_lists: List of neighbours, modified inplace
    :return: The list of neighbours
    """
    lind = len(ind)
    for i in range(lind):
        k = 0
        while neighbour_lists[ind[i]][k] != -1:
            k += 1
        if i < lind - 1:
            neighbour_lists[ind[i]][k] = ind[i + 1]
            k += 1
        if i > 0:
            neighbour_lists[ind[i]][k] = ind[i - 1]
    return neighbour_lists


def _choose_set_pos(vec):
    """
    Auxiliary method which accepts a bit-vector and selects one set position randomly.
    :param vec: Bit-vector
    :return: Random set position. None if vector is all zeros.
    """
    lvec = len(vec)
    i = np.random.randint(lvec)
    k = 0
    while -1 < i - k or i + k < lvec:
        sign = np.random.choice([-1, 1])
        if -1 < i + sign * k < lvec and vec[i + sign * k] != 0:
            return i + sign * k
        if -1 < i - sign * k < lvec and vec[i - sign * k] != 0:
            return i - sign * k
        k += 1
    return None


def edge_recombination(ind1, ind2):
    """
    Implements the edge recombination crossover operator as described in
    `Link text <http://www.rubicite.com/Tutorials/GeneticAlgorithms/CrossoverOperators/EdgeRecombinationCrossoverOperator.aspx>`_
    Returns a tuple of identical individuals result of the crossover.
    :param ind1: First individual
    :param ind2: Second individual
    :return: Tuple of two individuals
    """
    ilen = len(ind1)
    # neighbours lists as numpy array of shape (ilen + 1, 4), -1 represents absence of neighbour
    # note that the first row is unused: array indexing starts from 0, cities are enumerated starting from 1
    nlists = np.full((ilen + 1, 4), -1)
    _edge_neighbors(ind1, nlists)
    _edge_neighbors(ind2, nlists)
    i, off = 0, np.empty(ilen, dtype=int)
    x = ind1[0] if np.random.random() < 0.5 else ind2[0]  # randomly choose the first node from the individuals
    remaining = np.ones((ilen,), dtype=int)  # unassigned nodes to the offspring
    while True:
        off[i] = x
        i += 1
        if i >= ilen:
            break
        remaining[x - 1] = 0
        nlists[nlists == x] = -1  # removing x from neighbours lists
        if np.any(nlists[x] != -1):
            # neighbours of x and their neighbours count
            x_neighbours_counts = [(n, len(nlists[n][nlists[n] != -1])) for n in nlists[x][nlists[x] != -1]]
            # neighbours of x with fewest neighbours, there can be more than one
            _, x_neighbours_counts_min_neighbourhood = next(itertools.groupby(sorted(x_neighbours_counts, key=itemgetter(1))))
            # choose a neighbour of x with fewest neighbours randomly
            x = np.random.choice([n[0] for n in x_neighbours_counts_min_neighbourhood])
        else:
            x = _choose_set_pos(remaining) + 1
    assert len(off) == len(set(off))  # sanity check
    for i in range(ilen):
        ind1[i] = off[i]
        ind2[i] = off[i]
    return ind1, ind2
