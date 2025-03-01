#!/usr/bin/env python3

import pickle

with open("kg2.8.4c-tupleset.pkl", "rb") as fi:
    g_dict = pickle.load(fi)
    g = tuple(tuple(s) for s in g_dict['g'])
    with open("kg2.8.4c-tupleset.clj", "w") as fo:
        print("[", file=fo)
        for s in g_dict['g']:
            print(f"    #{{{' '.join([str(i) for i in s])}}}", file=fo)
        print("]", file=fo)
