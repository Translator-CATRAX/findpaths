#!venv/bin/python3.10
import findpaths as fp
fp.set_language('cxx')
g, g_inv, ids = fp.read_and_unpack_pickled_graph('kg2c-2.8.4', debug=False)
fp.set_graph(g, g_inv)
job_data = tuple(fp.node_names_to_ids(ids, (start_curie, end_curie)) + (3,)
                 for start_curie, end_curie in (('NCBIGene:1277',
                                                 'HP:0001001'),
                                                ('NCBIGene:9927',
                                                 'HP:0003474')))
all_paths = fp.get_all_paths_batch(job_data,
                                   debug=False)
print(f"Num. paths returned: {sum(paths.shape[0] for paths in all_paths)}")
