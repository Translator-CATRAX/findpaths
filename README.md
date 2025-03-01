# Developed by

This code was developed by Stephen Ramsey at Oregon State University, with
significant technical and algorithm design input from David Koslicki at Penn
State University.

# What does this code do?

The `findpaths.py` module provides functions for finding all paths between two
fixed user-specified nodes in the RTX-KG2c knowledge graph, up to a length limit
(typically four, unless you have a massive amount of RAM on your computer). The
module provides a capability for finding all paths between a single pair of
nodes, as well as a batch capability for finding all paths between source and
target for a user-provided list of (source,target) node pairs.  The module also
provides capabilities (accessed via running the module at the command-line) for
(1) benchmarking the module's performance at batch-mode path-finding (using a
built-in list or a user-supplied list of node pairs); and (2) loading the
RTX-KG2c knowledge graph from the "lite" JSON-lines KG2c distribution files and
converting the graph to a pickled data file format that is more convenient for
efficient loading from storage when the `findpaths.py` program starts up. The
`findpaths.py` module's path-finding code is implemented two ways, in python and
in multi-threaded C++. The C++ path-finding code is implemented in a set of
functions in the C++ module `findpaths-core.cpp`. The user can specify start
and end nodes by CURIE (but see the Caveats and Limitations section below).

# Caveats and limitations

1. Don't set the path length cutoff to a value greater than four.
2. You have to use the KG2c _canonical_ CURIE for each node that you want to
specify as a start or end node for path-finding. The `findpaths.py` module
does not provide the ability to "find" the canonicalized CURIE for a given
non-canonicalized CURIE; that should be done using the ARAX synonymizer, and is
beyond the scope of functionality envisioned for `findpaths.py`.
3. The paths that are returned are integer node _index values_; these index values can be
trivially translated back into CURIEs using the tuple of CURIEs (ordered by node
integer index value) that is in the `ids` variable (i.e., the third tuple entry)
returned from `read_and_unpack_picked_graph` (see the `example_usage.py` script).

# Requirements

This code has been tested on the following specific computer systems:

## macOS/arm64 test system
- macOS Sonoma 14.4.1 operating system
- cpython 3.10.14 interpreter
- Apple M1 Max processor @ 2.06&ndash;3.22&nbsp;GHz (10 cores)
- 64 GiB memory
- At least 10&nbsp;GiB of free space available on the root filesystem
- Homebrew 4.3.19-98-g9978c3d installed

## Ubuntu/x86_64 test system
- Ubuntu 22.04.4 LTS (jammy) operating system
- cpython 3.10.12 interpreter
- AMD EPYC 7R32 processor @ 3.3&nbsp;GHz (with 48 cores available)
- 96 GiB memory
- At least 10&nbsp;GiB of free space available on the root filesystem
- AWS `c5a.12xlarge` instance
- AMI: `ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-20240701`

## Ubuntu/arm64 test system
- Ubuntu 22.04.4 LTS (jammy) operating system
- cpython 3.10.12 interpreter
- Graviton2 processor @ 2.5&nbsp;GHz (with 48 ARM64 Neoverse N1 cores available)
- 96 GiB memory
- At least 10&nbsp;GiB of free space available on the root filesystem
- AWS `c6g.12xlarge` instance
- AMI: `ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-arm64-server-20240701`

This software has only been tested with the cpython interpreter version 3.10.
If you are running on any other operating system release and/or architecture
type than the system profiles indicated above, your mileage may vary. If you are
on x86_64 but some other Linux distro or Ubuntu release, consider using Docker
with an Ubuntu 22.04 image. If you are on Apple Silicon but some other macOS
release, consider using Docker with an Ubuntu 22.04 image.

# MacOS install/build instructions

## Setup the system to prepare for the findpaths C++ library build
From the `findpaths` directory, run:
```
./setup-macos.sh
```
which will, among other things, create a virtualenv in the 
subdirectory `venv` and install the PyPI dependencies into it.
This step may take a while, as it has to download some rather
large data files from a webserver in `us-east-1` and then
pickle the data files.

## Build/rebuild and install/reinstall the findpaths C++ library 
From the `findpaths` directory, run:
```
source venv/bin/activate
./build-cxx-macos.sh
```

# Ubuntu x86_64 install/build instructions

## Setup the system to prepare for the findpaths C++ library build
From the `findpaths` directory, run:
```
./setup-ubuntu-x86_64.sh
```
which will, among other things, create a virtualenv in the 
subdirectory `venv` and install the PyPI dependencies into it.
This step may take a while, as it has to download some rather
large data files from a webserver in `us-east-1` and then
pickle the data files.

## Build/rebuild and install/reinstall the findpaths C++ library 
From the `findpaths` directory, run:
```
source venv/bin/activate
./build-cxx-ubuntu-x86_64.sh
```

# Ubuntu arm64 install/build instructions

## Setup the system to prepare for the findpaths C++ library build
From the `findpaths` directory, run:
```
./setup-ubuntu-arm64.sh
```
which will, among other things, create a virtualenv in the 
subdirectory `venv` and install the PyPI dependencies into it.
This step may take a while, as it has to download some rather
large data files from a webserver in `us-east-1` and then
pickle the data files.

## Build/rebuild and install/reinstall the findpaths C++ library 
From the `findpaths` directory, run:
```
source venv/bin/activate
./build-cxx-ubuntu-arm64.sh
```

# Troubleshooting the build

When you run the build `build-cxx-*.sh` script, if
you get an error from CMake about not being able to find
the `pybind11Config.cmake` file, like this,
```
CMake Error at CMakeLists.txt:6 (find_package):
  By not providing "Findpybind11.cmake" in CMAKE_MODULE_PATH this project has
  asked CMake to find a package configuration file provided by "pybind11",
  but CMake did not find one.

  Could not find a package configuration file provided by "pybind11" with any
  of the following names:

    pybind11Config.cmake
    pybind11-config.cmake

  Add the installation prefix of "pybind11" to CMAKE_PREFIX_PATH or set
  "pybind11_DIR" to a directory containing one of the above files.  If
  "pybind11" provides a separate development package or SDK, be sure it has
  been installed.
```
you probably forgot to run the `source venv/bin/activate` step.

# Manually run the type checking on the python modules

Note, this step is already done when you run the `setup-macos.sh` script
or the `setup-ubuntu-x86_64.sh` script. But to do a standalone run
of `mypy` to carry out static analysis of all of the python
modules in the `findpaths` directory, run the following:
```
venv/bin/mypy --ignore-missing-imports findpaths.py
venv/bin/mypy --ignore-missing-imports example_usage.py
venv/bin/mypy --ignore-missing-imports example_usage_batch.py
```
Or you can just run:
```
./run-mypy-checks.sh
```

# Run the pytest suite, for the python-only version of findpaths:
From the `findpaths` directory, run
```
venv/bin/pytest
```
or if you want to be explicit about it
```
venv/bin/pytest --lang python
```

# Run the pytest suite, for the C++-enabled version of findpaths:
From the `findpaths` directory, run
```
venv/bin/pytest --lang cxx
```

# [OPTIONAL] Read RTX-KG2c graph as json-lines files and save as a pickle file 
Normally, the knowledge graph file is pickled by the `setup-common.sh` script
which is run by your OS-specific setup script, but if you need to generate the
pickled knowledge graph file manually for some reason, here is the command
(note, you need to have previously run the setup script for your particular
OS). From the `findpaths` directory, run:
```
venv/bin/python findpaths.py --writePickle kg2c-2.8.4
```
This should save the file as `kg2c-2.8.4.pkl`. At that point, you are
ready to run the script in benchmarking mode (see below).

# Benchmark the performance of `findpaths.py`, for the python only implementation:
Before you can do this step, you will need to have previously built the
RTX-KG2c pickle file (see the section "Read RTX-KG2c graph as json-lines files
and save as a pickle file). From the `findpaths` directory, run:
```
./run-benchmark.sh
```
or if you want to be explicit about it
```
./run-benchmark.sh python
```
It should print the number of paths generated per second, when the script completes.

# Benchmark the performance of `findpaths.py`, for the C++-enabled version:
From the `findpaths` directory, run:
```
./run-benchmark.sh cxx
```
It should print the number of paths generated per second, when the script completes, 
like this:
```
./run-benchmark.sh cxx
Elapsed time: 180.40 sec
Num paths: 336004760
Paths per second: 1862573
```

# Benchmark the performance of `findpaths.py` for a custom list of pairs of start/end nodes
If you wish to benchmark the performance of findpaths.py for a custom list of
pairs of start node CURIE and end node CURIE (in a two-column tab-separated character
file `test-data-file.txt`, run the following command from within the `findpaths` directory:
```
venv/bin/python findpaths.py --readPickle \
         --cutoff 3 4 \
         --multiNodeFileName test-data-file.txt \
         kg2c-2.8.4
```
It should print the number of paths generated per second, when the script completes.

Here is an example `test-data-file.txt`:
```
cat test-data-file.txt
start	end
MONDO:0007522	HP:0001001
NCBIGene:1277	HP:0001001
MONDO:0013635	HP:0002814
NCBIGene:57572	HP:0002814
NCBIGene:9927	HP:0003474
MONDO:0012727	HP:0001945
MONDO:0012276	HP:0002197
NCBIGene:3778	HP:0002197
MONDO:0007191	HP:0003326
NCBIGene:3586	HP:0003326
MONDO:0018866	HP:0001276
NCBIGene:103	HP:0001276
```

# Example usage: finding all paths between two fixed nodes using the C++-enabled version
This code is also available in the script `example_usage.py`:
```
#!venv/bin/python3.10
import findpaths as fp
fp.set_language('cxx')
g, g_inv, ids = fp.read_and_unpack_pickled_graph('kg2c-2.8.4', debug=False)
fp.set_graph(g, g_inv)
start_i, end_i = fp.node_names_to_ids(ids,
                                      ('NCBIGene:1277', 'HP:0001001'))
paths = fp.get_all_paths(start_i,
                         end_i,
                         n=3,
                         debug=False)
print(f"Number of paths returned: {paths.shape[0]}")
```
The code should produce this output:
```
Number of paths returned: 97
```

# Example usage: finding all paths between two fixed nodes using the python-enabled version

```
#!venv/bin/python3.10
import findpaths as fp
g, g_inv, ids = fp.read_and_unpack_pickled_graph('kg2c-2.8.4', debug=False)
fp.set_graph(g, g_inv)
start_i, end_i = fp.node_names_to_ids(ids,
                                      ('NCBIGene:1277', 'HP:0001001'))
paths = fp.get_all_paths(start_i,
                         end_i,
                         n=3,
                         debug=False)
print(f"Number of paths returned: {paths.shape[0]}")
```
The code should produce this output:
```
Number of paths returned: 97
```

# Example usage: finding all paths between two fixed nodes using the C++-enabled version, for a user-specified list of pairs of nodes ("batch" mode)
This code is also available in the script `example_usage_batch.py`:
```
#!venv/bin/python3.10
import findpaths as fp
fp.set_language('cxx')
g, g_inv, ids = fp.read_and_unpack_pickled_graph('kg2c-2.8.4', debug=False)
fp.set_graph(g, g_inv)
nodes_list = [fp.node_names_to_ids(ids, (start_curie, end_curie))
              for start_curie, end_curie in (('NCBIGene:1277', 'HP:0001001'),
                                             ('NCBIGene:9927', 'HP:0003474'))]
all_paths = fp.get_all_paths_batch(nodes_list,
                                   n=3,
                                   debug=False)
print(f"Num. paths returned: {sum(paths.shape[0] for paths in all_paths)}")
```
The code should produce this output:
```
Num. paths returned: 27826
```

# Some useful start and end nodes
[See also the nodes in the file `test-data-file.txt`]
- `MONDO:0015564`: Castleman's Disease
- `HP:0002027`: abdominal pain

# The `findpaths.py` CLI help (reprinted here for convenience)

```
./findpaths.py --help
usage: findpaths.py [-h] [--undirected] [--writePickle]
                    [--outputbase OUTPUTBASE] [--readPickle]
                    [--cutoff CUTOFF] [--debug]
                    [--startnode STARTNODE] [--endnode ENDNODE]
                    [--multiNodeFileName MULTINODEFILENAME] [--lang LANG]
                    filebase

findpaths.py: find paths between genes and symptoms in a large biomedical
knowledge graph

positional arguments:
  filebase              base filename, to which '-nodes.jsonl.gz' or
                        '-edges.jsonl.gz' willget added; for example,
                        'kg2c-2.8.4' would get expanded to
                        kg2c-2.8.4-nodes.json.gz and kg2c-2.8.4-edges.json.gz

options:
  -h, --help            show this help message and exit
  --undirected          treat the graph as undirected (default is directed)
  --writePickle         write the graph to a pickle file
  --outputbase OUTPUTBASE
                        optional base filename for the output file(s)
  --readPickle          read the graph from a pickle file
  --cutoff CUTOFF       maximum path length, in edge hops
  --debug
  --startnode STARTNODE
                        the CURIE of the starting node for path finding
  --endnode ENDNODE     the CURIE of the ending node for path finding
  --multiNodeFileName MULTINODEFILENAME
                        name of a tab-delimited text file containing two
                        columns of CURIES
  --lang LANG           if you pass this option as "cxx", the C++
                        implementation will be used; otherwise the python
                        implementation will be used
```

# TODO

1. Make `--undirected` the default option (suggested by David Koslicki).
2. Make the number of cores for the C++ parallelism configurable through CLI.
3. Consider adding a third column to `test-data-file.txt` containing the
   "cutoff" value; that might be cleaner than passing a list of cutoff values
   that are applied to all node pairs in the node pair list (a user might want
   to search with one cutoff for one node pair, and a different cutoff for
   another, in principle). Not sure how important this is, however.
4. Need to run the code through the C++ profiler (e.g., Intel VTune).
5. Need to add the ability to filter paths by a set of allowed intermediate node
   categories.
6. Investigate if it is possible to parallelize `bfs_limited_paths_internal`
   in `findpaths-core.cpp`, along the lines of Mohsen's PathFinder code.
7. Investigate if it is possible to parallelize the two calls to
   `bfs_limited_paths_internal` in the function `get_all_paths_internal`.

