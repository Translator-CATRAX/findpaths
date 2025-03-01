#!venv/bin/python3.10
import findpaths as fp
fp.set_language('cxx')
g, g_inv, ids = fp.read_and_unpack_pickled_graph('kg2c-2.8.4', debug=False)
start_i, end_i = fp.node_names_to_ids(ids,
                                      ('NCBIGene:1277', 'HP:0001001'))
fp.set_graph(g, g_inv)
paths = fp.get_all_paths(start_i,
                         end_i,
                         n=3,
                         debug=False)
print(f"Number of paths returned: {paths.shape[0]}")
