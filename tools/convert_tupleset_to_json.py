#!/usr/bin/env python3

import json
import pickle

with open("kg2.8.4c-tupleset.pkl", "rb") as fi:
    g_dict = pickle.load(fi)
    g = tuple(tuple(s) for s in g_dict['g'])
    with open("kg2.8.4c-tupleset.json", "w") as fo:
        json.dump(g, fo, indent=4)

