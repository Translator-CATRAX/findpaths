#!venv/bin/python3.10
#
# findpaths.py
#
# Stephen Ramsey
# Oregon State University

from collections.abc import Iterator
from collections import deque, defaultdict
import timeit
import pytest
import pickle
import argparse
from toolz import pipe
import toolz.curried as tc
import toolz.sandbox.core as tsc
import gzip
import jsonlines
import os
import sys
import multiprocess
import numpy as np
import pandas as pd
import itertools as it
import typing
import types
from typing import Iterable

# Optional imports used during debugging:
# import pprint   # uncomment this for pprint debugging
# import profile  # uncomment this if you want to do profiling


# This needs to be consistent with m_initializer in
# findpaths-core.cpp, and also not overlap any integer
# node identifier, so don't change it unless you
# know what you are doing:
g_np_graph_initializer = -1

g_default_start_node = None
g_default_end_node = None
g_default_cutoff = 3
g_default_multi_node_file_name = None
g_language = None
g_module = sys.modules[__name__]
g_g = None
g_g_inv = None
g_min_nodes_for_multiproc = 1000


def set_language(lang: str) -> types.ModuleType:
    if lang == 'cxx':
        pass
    elif lang == 'python':
        pass
    else:
        assert False, f"invalid language specified: {lang}"
    global g_module
    if lang == 'cxx':
        import findpaths_core as fpc
        g_module = fpc
    elif lang == 'python':
        pass
    assert g_module is not None
    return g_module


def _stream_gz_jsonl(gz_jl_file_name: str) -> Iterator[dict]:
    with gzip.open(gz_jl_file_name) as input_file:
        reader = jsonlines.Reader(input_file)
        for obj in reader:
            yield obj


def _curie_to_parts(curie: str) -> tuple:
    return tuple(curie.split(':', maxsplit=1))


def _clean_up_node(n: dict) -> dict:
    return dict(n, **{'category':
                      _curie_to_parts(n['category'])[1]})


def _load_graph(gz_jl_base_file_name: str) -> tuple[tuple, tuple]:

    node_ids, nodes = \
        pipe(gz_jl_base_file_name +
             "-nodes.jsonl.gz",
             _stream_gz_jsonl,
             tc.map(lambda n: (n['id'],
                               _clean_up_node(n))),
             tsc.unzip,  # toolz.sandbox.core.unzip returns a tuple of maps
             tc.map(tuple),
             tuple)

    edges = \
        pipe(gz_jl_base_file_name +
             "-edges.jsonl.gz",
             _stream_gz_jsonl,
             tuple)

    return (nodes, edges)


def _make_curie_to_index_map(nodes: tuple[dict, ...]) -> dict[str, int]:
    return {nodes[i]['id']: i for i in range(len(nodes))}


def _make_graph_edgelist(nodes: tuple[dict, ...],
                         edges: tuple[dict, ...]) -> dict:
    g_dict = dict()
    g_dict['ids'] = tuple(node['id'] for node in nodes)
    curie_to_index_map = dict()
    N = len(nodes)
    curie_to_index_map = _make_curie_to_index_map(nodes)
    g: tuple[set[int], ...] = tuple(set() for _ in range(N))
    g_inv: tuple[set[int], ...] = tuple(set() for _ in range(N))
    for e in edges:
        s = curie_to_index_map[e['subject']]
        t = curie_to_index_map[e['object']]
        g[s].add(t)
        g_inv[t].add(s)
    g_dict['g'] = g
    g_dict['g_inv'] = g_inv
    return g_dict


def _get_args() -> argparse.Namespace:
    arg_parser = argparse.ArgumentParser(description="findpaths.py: "
                                         "find paths between genes "
                                         "and symptoms in a large "
                                         "biomedical knowledge graph")
    arg_parser.add_argument('filebase',
                            help="base filename, to which "
                            "\'-nodes.jsonl.gz\' or "
                            "\'-edges.jsonl.gz\' will"
                            "get added; for example, "
                            "\'kg2c-2.8.4\' would get "
                            "expanded to "
                            "kg2c-2.8.4-nodes.json.gz "
                            "and "
                            "kg2c-2.8.4-edges.json.gz")
    arg_parser.add_argument('--undirected',
                            default=False,
                            action='store_true',
                            dest='undirected',
                            help="treat the graph as undirected "
                            "(default is directed)")
    arg_parser.add_argument('--writePickle',
                            default=None,
                            dest='write_pickle',
                            action='store_true',
                            help="write the graph to a pickle file")
    arg_parser.add_argument('--outputbase',
                            default=None,
                            help='optional base filename for the output '
                            'file(s)')
    arg_parser.add_argument('--readPickle',
                            default=False,
                            dest='read_pickle',
                            action='store_true',
                            help="read the graph from a pickle file")
    arg_parser.add_argument('--cutoff',
                            dest='cutoff',
                            type=int,
                            help='maximum path length, in edge hops')
    arg_parser.add_argument('--debug',
                            default=False,
                            action='store_true',
                            dest='debug')
    arg_parser.add_argument('--startnode',
                            type=str,
                            help='the CURIE of the starting node for path '
                            'finding',
                            default=g_default_start_node)
    arg_parser.add_argument('--endnode',
                            type=str,
                            help='the CURIE of the ending node for path '
                            'finding',
                            default=g_default_end_node)
    arg_parser.add_argument('--multiNodeFileName',
                            type=str,
                            help='name of a tab-delimited text file' +
                            ' containing two columns of CURIES',
                            default=g_default_multi_node_file_name)
    arg_parser.add_argument('--lang',
                            default='python',
                            dest='lang',
                            help='if you'
                            ' pass this option as \"cxx\",'
                            ' the C++ implementation will be'
                            ' used; otherwise the python implementation will'
                            ' be used')
    arg_parser.add_argument('--mult',
                            default=None,
                            type=int,
                            dest='mult',
                            help='repeat the path-finding work N times')
    return arg_parser.parse_args()


def _invert_graph(g: tuple[set[int], ...]) -> tuple[set[int], ...]:
    N = len(g)
    g_inv: tuple[set[int], ...] = tuple(set() for _ in range(N))
    for s in range(0, N):
        for t in g[s]:
            g_inv[t].add(s)
    return g_inv


def _update_backpaths(backpaths: defaultdict[int, set[tuple[int, ...]]],
                      g_inv: tuple[set[int], ...],
                      nodes: set[int],
                      reverse: bool,
                      cutoff: int,
                      v: int) -> set[tuple[int, ...]]:
    res_set = set()
    for nv in g_inv[v]:
        if nv in nodes:
            if not reverse:
                for p in backpaths[nv]:
                    if len(p) < cutoff + 1:
                        res_set.add(p + (v,))
            else:
                for p in backpaths[nv]:
                    if len(p) < cutoff + 1:
                        res_set.add((v,) + p)
    return backpaths[v] | res_set


def _bfs_limited_paths(g: tuple[set[int], ...],
                       g_inv: tuple[set[int], ...],
                       v_start: int,
                       cutoff: int,
                       reverse: bool) -> dict[int, set[tuple[int]]]:
    if cutoff < 0:
        raise ValueError(f"invalid distance cutoff: {cutoff}")
    if cutoff == 0:
        return dict()
    queue = deque([v_start])
    distances = defaultdict(lambda: -1)
    backpaths: defaultdict[int, set[tuple[int, ...]]] = defaultdict(set)
    distances[v_start] = 0
    backpaths[v_start].add((v_start,))
    g_use = g_inv if reverse else g
    while queue:
        v = queue.popleft()
        v_dist = distances[v]  # get the shortest-path distance to vertex v
        if v_dist > cutoff:
            break
        elif v_dist == cutoff:
            # no point in looking at neighbors for v; they
            # are too far away
            continue
        for v_neighb in g_use[v]:
            if distances[v_neighb] == -1:
                # We have not reached v_neighb before.
                # By definition, the distance to v_neighb
                # must be the distance to v, plus one:
                distances[v_neighb] = v_dist + 1
                # We need to explore v_neighb; add to queue:
                queue.append(v_neighb)
            # Record a path back from v_neighb to v:
            assert v in backpaths, f"could not find node {v_neighb} " + \
                f"in backpaths, when node v is: {v}"
            if not reverse:
                for p in backpaths[v]:
                    if len(p) < cutoff + 1:
                        backpaths[v_neighb].add(p + (v_neighb,))
            else:
                for p in backpaths[v]:
                    if len(p) < cutoff + 1:
                        backpaths[v_neighb].add((v_neighb,) + p)

    return dict(typing.cast(dict[int, set[tuple[int]]],
                            backpaths))


def _drop_first(i: tuple[int]) -> tuple[int, ...]:
    rest: list[int]
    _, *rest = i
    return tuple(rest)


def _get_all_paths_ret_set(g: tuple[set[int], ...],
                           g_inv: tuple[set[int], ...],
                           s: int,
                           t: int,
                           n: int,
                           debug: bool = False) -> set[tuple[int, ...]]:
    if n <= 0:
        raise ValueError(f"invalid value for n: {n}")
    n1, n2 = (n + 1) // 2, n // 2
    if n2 < n1:
        k_s = len(g[s])
        k_t = len(g_inv[t])
        if debug:
            print(f"k_s: {k_s}  k_t: {k_t}")
        if k_s > k_t:
            return set(
                map(tuple,
                    map(reversed,
                        _get_all_paths_ret_set(g_inv, g, t, s, n, debug))))
    N = len(g)
    if s > N - 1 or s < 0:
        raise ValueError(f"source vertex is invalid: {s}")
    if t > N - 1 or t < 0:
        raise ValueError(f"target vertex is invalid: {t}")
    if s == t:
        raise ValueError("this function won't find a path between a node and "
                         f"itself; value: {s}")
    if debug:
        print(f"running bfs on node s with cutoff {n1}")
    s_paths: dict[int, set[tuple[int]]] = _bfs_limited_paths(g, g_inv, s,
                                                             cutoff=n1,
                                                             reverse=False)
    s_nodes = set(s_paths.keys())
    if debug:
        print(f"number of nodes found in paths of length {n1} "
              f"from starting vertex: {len(s_nodes)}")
    if debug:
        print(f"running bfs on node t with cutoff {n2}")
    t_paths: dict[int, set[tuple[int]]] = _bfs_limited_paths(g, g_inv, t,
                                                             cutoff=n2,
                                                             reverse=True)
    t_nodes = set(t_paths.keys())
    if debug:
        print(f"number of nodes found in paths of length {n2} "
              f"from ending vertex: {len(t_nodes)}")
    border_nodes = s_nodes & t_nodes
    res_set: set[tuple[int, ...]] = set()

    if t in s_nodes:
        res_set |= s_paths[t]
        border_nodes = border_nodes - {t}

    if debug:
        print(f"number of border nodes: {len(border_nodes)}")

    for b in border_nodes:
        res_set |= set(map(tuple,
                           map(it.chain.from_iterable,
                               it.product(*(s_paths[b],
                                            map(_drop_first, t_paths[b]))))))

    # At cutoff=4, a small proportion of paths will be non-simple; filter them
    # out (this line of code is kind of slow (maybe 5% of total running time):
    return set(filter(lambda path: len(set(path)) == len(path), res_set))


def _set_graph(g: tuple[set[int], ...],
               g_inv: tuple[set[int], ...]):
    global g_g
    global g_g_inv
    g_g = g
    g_g_inv = g_inv


def set_graph(g: tuple[set[int], ...],
              g_inv: tuple[set[int], ...]):
    g_module._set_graph(g, g_inv)


def _get_all_paths_np(g: tuple[set[int], ...],
                      g_inv: tuple[set[int], ...],
                      s: int,
                      t: int,
                      n: int,
                      debug: bool = False) -> np.ndarray:
    paths = _get_all_paths_ret_set(g, g_inv, s, t, n, debug)
    return _convert_paths_from_ragged_list_to_np(paths, n)


def _get_all_paths_np_cached_graph(s: int,
                                   t: int,
                                   n: int,
                                   debug: bool = False) -> np.ndarray:
    if g_g is None or g_g_inv is None:
        raise ValueError("cannot call _get_all_paths_np_cached_graph "
                         "unless set_graph has previously been caled")
    paths = _get_all_paths_ret_set(g_g, g_g_inv, s, t, n, debug)
    return _convert_paths_from_ragged_list_to_np(paths, n)


def get_all_paths(s: int,
                  t: int,
                  n: int,
                  debug: bool = False) -> np.ndarray:
    return g_module._get_all_paths_np_cached_graph(s, t, n, debug)


def _get_all_paths_lazy(g: tuple[set[int], ...],
                        s: int,
                        t: int,
                        n: int,
                        debug: bool = False) -> set[tuple[int]]:
    g_inv = _invert_graph(g)
    paths_np = g_module._get_all_paths_np(g, g_inv, s, t, n, debug)
    return _convert_paths_from_np_to_ragged_list(paths_np)


test_graphs_edgelist = {
    'g1': ((0, 1),
           (1, 2),
           (2, 3),
           (0, 4),
           (4, 2)),  # this graph is a simple DAG
    'g2': ((0, 1),
           (1, 2),
           (1, 3),
           (2, 4),
           (3, 4),
           (4, 9),
           (0, 5),
           (5, 6),
           (5, 7),
           (6, 8),
           (7, 8),
           (8, 9),
           (9, 0)),  # this graph has a cycle
    'g3': ((0, 1),
           (0, 2),
           (1, 3),
           (2, 3)),
    'g4': ((0, 1),   # this graph is v1 with a shortcut
           (1, 2),
           (2, 3),
           (0, 4),
           (4, 2),
           (0, 2)),
    'g5': ((0, 1),
           (1, 2),
           (2, 1),
           (1, 3))   # this graph has a cycle
}


def _make_test_graph_from_edgelist(el: tuple[tuple[int, int],
                                             ...]) -> tuple[set[int], ...]:
    N = max(max(s, t) for s, t in el) + 1
    g: tuple[set[int], ...] = tuple(set() for _ in range(N))
    for s, t in el:
        g[s].add(t)
    return g


def _make_test_graphs(el_dict: dict[str,
                                    tuple[tuple[int, int],
                                          ...]]) \
                                          -> dict[str, tuple[set[int], ...]]:
    return {k: _make_test_graph_from_edgelist(v)
            for k, v in el_dict.items()}


test_graphs = _make_test_graphs(test_graphs_edgelist)


def _results_are_all_ints(r: set[tuple[int]]) -> bool:
    return all(isinstance(v, int) for p in r for v in p)


def test_g3_two_paths_length_two(lang):
    r = _get_all_paths_lazy(test_graphs['g3'], 0, 3, 2)
    assert len(r) == 2


def test_g1_no_path_insufficient_length():
    r = _get_all_paths_lazy(test_graphs['g1'], 0, 2, 1)
    assert not r


def test_g1_no_path_against_edge_direction():
    r = _get_all_paths_lazy(test_graphs['g1'], 3, 0, 3)
    assert not r


def test_g1_length_longer_than_needed():
    r = _get_all_paths_lazy(test_graphs['g1'], 0, 3, 4)
    assert r == {(0, 1, 2, 3),
                 (0, 4, 2, 3)}


def test_g1_length_exact_length():
    r = _get_all_paths_lazy(test_graphs['g1'], 0, 3, 3)
    assert r == {(0, 1, 2, 3),
                 (0, 4, 2, 3)}


def test_g1_one_hop():
    r = _get_all_paths_lazy(test_graphs['g1'], 0, 4, 1)
    assert len(r) == 1
    assert _results_are_all_ints(r)
    assert r == {(0, 4)}


def test_g1_zero_length():
    with pytest.raises(ValueError):
        _get_all_paths_lazy(test_graphs['g1'], 0, 4, 0)


def test_g1_self_edge():
    with pytest.raises(ValueError):
        _get_all_paths_lazy(test_graphs['g1'], 0, 0, 1)


def test_g1_non_existing_vertex():
    with pytest.raises(ValueError):
        _get_all_paths_lazy(test_graphs['g1'], 0, 6, 2)


def test_g1_length_2_single_path():
    r = _get_all_paths_lazy(test_graphs['g1'], 4, 3, 2)
    assert r == {(4, 2, 3)}


def test_g2_length_4():
    r = _get_all_paths_lazy(test_graphs['g2'], 0, 9, 4)
    assert r == {(0, 1, 2, 4, 9),
                 (0, 1, 3, 4, 9),
                 (0, 5, 6, 8, 9),
                 (0, 5, 7, 8, 9)}


def test_g4_one_hop():
    r = _get_all_paths_lazy(test_graphs['g4'], 0, 2, 1)
    assert r == {(0, 2)}


def test_g4_three_hop():
    r = _get_all_paths_lazy(test_graphs['g4'], 0, 3, 3)
    assert r == {(0, 2, 3),
                 (0, 1, 2, 3),
                 (0, 4, 2, 3)}


def test_g4_three_hop_inv():
    r = _get_all_paths_lazy(_invert_graph(test_graphs['g4']), 3, 0, 3)
    assert r == {(3, 2, 0),
                 (3, 2, 1, 0),
                 (3, 2, 4, 0)}


def test_bfs_g1_one_hop():
    g = test_graphs['g1']
    g_inv = _invert_graph(g)
    r = g_module._bfs_limited_paths(g, g_inv, 0, 1, reverse=False)
    assert r == {0: {(0,)}, 1: {(0, 1)}, 4: {(0, 4)}}


def test_bfs_g1_one_hop_rev_drop_first():
    g = test_graphs['g1']
    g_inv = _invert_graph(g)
    r = g_module._bfs_limited_paths(g_inv, g, 0, 1, reverse=True)
    assert r == {0: {(0,)}, 1: {(1, 0)}, 4: {(4, 0)}}


def test_g5_non_simple_path():
    r = _get_all_paths_lazy(test_graphs['g5'], 0, 3, 4)
    assert r == {(0, 1, 3)}


def _convert_paths_from_ragged_list_to_np(paths: set[tuple[int, ...]],
                                          cutoff: int) -> np.ndarray:
    num_paths = len(paths)
    paths_np = np.full(shape=[num_paths, cutoff + 1], dtype=int,
                       fill_value=g_np_graph_initializer)
    for i, path in enumerate(paths):
        plen = len(path)
        paths_np[i, 0:plen] = path
    return paths_np


def _convert_paths_from_np_to_ragged_list(paths_np: np.ndarray) -> \
        set[tuple[int]]:
    paths_list = paths_np.tolist()
    paths_list_ragged = set(map(lambda p: tuple(filter(lambda i: i >= 0, p)),
                                paths_list))
    return paths_list_ragged


def _return_paths_are_valid(g: tuple[set, ...],
                            s: int,
                            t: int,
                            cutoff: int,
                            path_list: list[list[int]]) -> bool:
    return all(map(lambda path: len(path) <= cutoff + 1 and
                   path[0] == s and
                   path[-1] == t and
                   len(set(path)) == len(path) and
                   all([path[i+1] in g[path[i]]
                        for i in range(0, len(path) - 1)]),
                   path_list))


def get_all_paths_batch(job_data: tuple[tuple[int, int, int], ...],
                        debug: bool) -> list[np.ndarray]:
    def _get_all_paths_internal(s: int,
                                t: int,
                                n: int) -> np.ndarray:
        return g_module._get_all_paths_np_cached_graph(s, t, n, debug)
    with multiprocess.Pool() as mp_pool:
        res = mp_pool.starmap(_get_all_paths_internal,
                              job_data)
    return res


def node_name_to_id(ids: tuple[str, ...],
                    name: str) -> int:
    try:
        id = ids.index(name)
    except ValueError:
        raise ValueError(f"unable to get integer node ID for CURIE {name}")
    return id


def node_names_to_ids(ids: tuple[str, ...],
                      names: tuple[str, str]) -> tuple[int, int]:
    return (node_name_to_id(ids, names[0]),
            node_name_to_id(ids, names[1]))


def _run_benchmark(g_dict: dict,
                   job_data: Iterable[tuple[str, str, int]],
                   undirected: bool,
                   debug: bool,
                   multiprocess: bool,
                   chunksize: int,
                   mult: int):

    g = g_dict['g']
    g_inv = g_dict['g_inv']
    if undirected:
        g = tuple(g[n] | g_inv[n] for n in range(len(g)))
        g_inv = g

    g_module._set_graph(g, g_inv)

    ids = g_dict['ids']

    start = timeit.default_timer()

    job_data_processed = tuple(node_names_to_ids(ids, (s, t)) + (chunksize,)
                               for s, t, chunksize in job_data)

    if mult is not None:
        job_data_processed = job_data_processed * mult

    paths_all = get_all_paths_batch(job_data_processed, debug)
    paths_ctr = sum([pl.shape[0] for pl in paths_all])

    end = timeit.default_timer()
    elapsed_time = end - start
    print(f"Elapsed time: {elapsed_time:0.2f} sec")
    print(f"Num paths: {paths_ctr}")
    print(f"Paths per second: {paths_ctr/elapsed_time:0.0f}")


def _namespace_to_dict(namespace):
    return {
        k: _namespace_to_dict(v) if isinstance(v, argparse.Namespace) else v
        for k, v in vars(namespace).items()
    }


def _write_pickled_graph(g: tuple[tuple, tuple],
                         output_file_base: str,
                         debug=False):
    output_pickle_file_name = output_file_base + ".pkl"
    if debug:
        print("Writing graph to pickle file: "
              f"{output_pickle_file_name}")
    with open(output_pickle_file_name, 'wb') as output_file:
        pickle.dump(g, output_file)


def _read_pickled_graph(filebase: str, debug=False) -> dict[str, tuple]:
    input_pickle_file_name = filebase + ".pkl"
    if os.path.exists(input_pickle_file_name):
        if debug:
            print("Loading graph from pickle file: "
                  f"{input_pickle_file_name}")
        with open(input_pickle_file_name, 'rb') as input_file:
            g_dict = pickle.load(input_file)
    else:
        sys.exit(f"unable to open pickle file {input_pickle_file_name}")
    return g_dict


def read_and_unpack_pickled_graph(filebase: str,
                                  debug=False) -> tuple[tuple, tuple, tuple]:
    g_dict = _read_pickled_graph(filebase, debug)
    return (g_dict['g'],
            g_dict['g_inv'],
            g_dict['ids'])


def _read_file_describing_batch_job(filename: str) -> \
        tuple[tuple[str, str, int], ...]:
    batch_job_df = pd.read_csv(filename, sep="\t")
    return tuple(tuple(sub) for sub in batch_job_df.values.tolist())


# See the comment above the line `if __name__ == "__main__"`
# for an explanation of why the `main` function has arguments.
def _main(filebase=None,
          outputbase=None,
          read_pickle=False,
          write_pickle=False,
          debug=False,
          multiprocess=False,
          undirected=False,
          startnode=g_default_start_node,
          endnode=g_default_end_node,
          cutoff=None,
          multiNodeFileName=None,
          lang=None,
          chunksize=None,
          mult=None):

    set_language(lang)

    if mult is not None:
        if mult < 1:
            raise ValueError(f"invalid value for CLI option \'mult\': {mult}")
    if read_pickle:
        g_dict = _read_pickled_graph(filebase, debug)
    else:
        g_dict = _make_graph_edgelist(*_load_graph(filebase))
        if write_pickle:
            output_file_base = (filebase if outputbase is None else
                                outputbase)
            _write_pickled_graph(g_dict, output_file_base, debug)
    if multiNodeFileName is None:
        if cutoff is None:
            cutoff = g_default_cutoff
        if (startnode is not None and endnode is None) or \
           (startnode is None and endnode is not None):
            sys.exit("both `startnode` and `endnode` must be specified, or "
                     "neither of them")
        if startnode is not None:
            job_data = [[startnode, endnode, cutoff]]
        else:
            job_data = None
    else:
        if cutoff is not None:
            raise ValueError("cannot specify cutoff on CLI if using "
                             "multiNodeFileName")
        job_data = _read_file_describing_batch_job(multiNodeFileName)

    if job_data is not None:
        _run_benchmark(g_dict,
                       job_data,
                       undirected=undirected,
                       debug=debug,
                       multiprocess=multiprocess,
                       chunksize=chunksize,
                       mult=mult)


if __name__ == "__main__":
    # Enable calling `main` (with arguments) from another python function, for
    # module testing.
    _main(**_namespace_to_dict(_get_args()))
