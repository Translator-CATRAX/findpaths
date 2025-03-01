#include <dpl/algorithm>
#include <dpl/execution>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/stl_bind.h>
#include <pybind11/numpy.h>
#include <iostream>
#include <unordered_map>
#include <vector>
#include <set>
#include <queue>
#include <stdexcept>
#include <map>
#include <tuple>
#include <iterator>
#include <functional>
#include <sstream>
#include <utility>

namespace py = pybind11;

using Graph = std::vector<std::set<int>>;
using Path = std::vector<int>;
using NodeSet = std::set<int>;
using PathSet = std::set<Path>;
using PathVec = std::vector<Path>;
using NodeToPathVec = std::unordered_map<int, PathVec>;

// maybe this could be used if we wanted to make PathSet a std::unordered_set
struct VectorHash {
    size_t operator()(const Path& v) const {
        std::hash<int> hasher;
        size_t seed = 0;
        for (int i : v) {
            seed ^= hasher(i) + 0x9e3779b9 + (seed << 6) + (seed >> 2);
        }
        return seed;
    }
};


std::pair<NodeToPathVec, NodeSet> bfs_limited_paths_internal(
    const Graph& g,
    const Graph& g_inv,
    int v_start,
    int cutoff,
    bool reverse) {
    
    if (cutoff < 0) {
        throw std::invalid_argument("invalid distance cutoff: " + std::to_string(cutoff));
    }
    if (cutoff == 0) {
        return {};
    }
    const Graph& g_use = (reverse ? g_inv : g);

    std::queue<int> queue;
    std::unordered_map<int, int> distances;
    NodeToPathVec backpaths;

    queue.push(v_start);
    distances[v_start] = 0;
    backpaths[v_start].push_back({v_start});

    while (!queue.empty()) {
        int v = queue.front();
        queue.pop();
        int v_dist = distances[v];
        if (v_dist > cutoff) {
            break;
        }
        for (int v_neighb : g_use[v]) {
            if (distances.find(v_neighb) == distances.end()) {
                distances[v_neighb] = v_dist + 1;
                queue.push(v_neighb);
            }
            for (const auto& p : backpaths[v]) {
                if (p.size() < cutoff + 1) {
                    Path new_path(p);
                    new_path.push_back(v_neighb);
                    backpaths[v_neighb].push_back(new_path);
                }
            }
        }
    }
    if ( reverse ) {
      for (auto& pair : backpaths) {
        for (auto& path : pair.second) {
          std::reverse(path.begin(), path.end());
        }
      }
    }

    NodeSet nodes;
    for (const auto& pair: backpaths) {
      nodes.insert(pair.first);
    }
    return std::pair<NodeToPathVec, NodeSet>(backpaths, nodes);
}

PathSet combine_paths(const PathVec& s_paths,
                      const PathVec& t_paths) {
    PathSet result;
    for (const auto& sp : s_paths) {
        for (const auto& tp : t_paths) {
            Path combined;
            combined.reserve(sp.size() + tp.size());  // Reserve space upfront
            combined.insert(combined.end(), sp.begin(), sp.end());
            combined.insert(combined.end(), tp.begin(), tp.end());
            result.emplace(std::move(combined));  // Use emplace with move semantics
        }
    }
    return result;
}

Graph m_initializer = *(new std::vector<std::set<int>> {{-1}});
Graph m_g = m_initializer;
Graph m_g_inv = m_initializer;

void set_graph(const Graph& g,
               const Graph& g_inv) {
  m_g = g;
  m_g_inv = g_inv;
}

// what if this function just returned a PathVec ?
PathSet get_all_paths_internal(
    const Graph& g,
    const Graph& g_inv,
    int s,
    int t,
    int n,
    bool debug) {
  if (n <= 0) {
    throw std::invalid_argument("invalid value for n: " + std::to_string(n));
  }
  int n1 = (n + 1) / 2;
  int n2 = n / 2;
  if (n2 < n1) {
    int k_s = g[s].size();
    int k_t = g_inv[t].size();
    if (debug) {
      std::cout << "k_s: " + std::to_string(k_s) + " k_t: " + std::to_string(k_t) << std::endl;
    }
    if (k_s > k_t) {
      PathSet paths = get_all_paths_internal(g_inv, g, t, s, n, debug);
      PathSet paths_rev;
      for (auto i: paths) {
        std::reverse(i.begin(), i.end());
        paths_rev.insert(i);
      }
      return paths_rev;
    }
  }
  std::size_t N = g.size();
  if (s > N - 1 || s < 0) {
    throw std::invalid_argument("source vertex is invalid: " + std::to_string(s));
  }
  if (t > N - 1 || t < 0) {
    throw std::invalid_argument("target vertex is invalid: " + std::to_string(t));
  }
  if (s == t) {
    throw std::invalid_argument("this function won\'t find a path between a node and itself; value: " + \
                                std::to_string(s));
  }
  if (debug) {
    std::cout << "running bfs on node s with cutoff " + std::to_string(n1) << std::endl;
  }

  std::vector<std::pair<NodeToPathVec, NodeSet>> results(2);

  std::vector<std::function<void()>> tasks = {
    [&results, &g, &g_inv, &s, &n1]() {
      results[0] = bfs_limited_paths_internal(g, g_inv, s, n1, false);
    },
    [&results, &g, &g_inv, &t, &n2]() {
      results[1] = bfs_limited_paths_internal(g, g_inv, t, n2, true);
    }
  };

  NodeToPathVec s_paths, t_paths;
  NodeSet s_nodes, t_nodes;

  // This is the old sequential code (for some reason, std::execution::seq does not work):
  // std::tie(s_paths, s_nodes) = bfs_limited_paths_internal(g, g_inv, s, n1, false);
  // std::tie(t_paths, t_nodes) = bfs_limited_paths_internal(g, g_inv, t, n1, true);
  
  // Execute the tasks in parallel using std::for_each with std::execution::par
  std::for_each(std::execution::par, tasks.begin(), tasks.end(), [](auto& task) {
    task();
  });

  std::tie(s_paths, s_nodes) = results[0];

  if (debug) {
    std::cout << "number of nodes found in paths of length " + std::to_string(n1) + \
      " from starting vertex: " + std::to_string(s_nodes.size()) << std::endl;
    std::cout << "running bfs on node t with cutoff " + std::to_string(n2) << std::endl;
  }
  
  std::tie(t_paths, t_nodes) = results[1];

  if (debug) {
    std::cout << "number of nodes found in paths of length " + std::to_string(n2) + \
      " from ending vertex: " + std::to_string(t_nodes.size()) << std::endl;
  }

  NodeSet border_nodes;
  std::set_intersection(s_nodes.begin(), s_nodes.end(),
                        t_nodes.begin(), t_nodes.end(),
                        std::inserter(border_nodes, border_nodes.begin()));

  PathSet res_set; // assume initialized to empty
  if (s_nodes.find(t) != s_nodes.end()) {
    PathVec paths_to_add = s_paths[t];
    res_set.insert(paths_to_add.begin(), paths_to_add.end());
    border_nodes.erase(t);
  }

  if (debug) {
    std::cout << "number of border nodes: " + std::to_string(border_nodes.size()) << std::endl;
  }

  for (int b : border_nodes) {
    for (auto& path: s_paths[b]) {
      if (! path.empty()) {
        path.pop_back();
      }
    }
    PathSet new_paths = combine_paths(s_paths[b], t_paths[b]);
    res_set.insert(new_paths.begin(), new_paths.end());
  }

  if (debug) {
    std::cout << "filtering paths for appropriate length" << std::endl;
  }

  for (auto it = res_set.begin(); it != res_set.end(); /* no increment here */) {
    if ( std::unordered_set<int>((*it).begin(), (*it).end()).size() != (*it).size() ) {
      it = res_set.erase(it);
    } else {
      ++it;
    }
  }
  if (debug) {
    std::cout << "filtering complete; returning paths" << std::endl;
  }
  
  return res_set;
}

PathVec get_all_paths(
    const Graph& g,
    const Graph& g_inv,
    int s,
    int t,
    int n,
    bool debug) {

  if (debug) {
    std::cout << "running get_all_paths with cutoff: " << \
      std::to_string(n) << std::endl;
  }
  
  PathSet res_set_filtered = get_all_paths_internal(g, g_inv, s, t, n, debug);

  if (debug) {
    std::cout << "converting " << std::to_string(res_set_filtered.size()) << \
      " paths to PathVec format" << std::endl;
  }
 
  PathVec res_vec(res_set_filtered.begin(),
                  res_set_filtered.end());

  if (debug) {
    std::cout << "returning PathVec paths" << std::endl;
  }
   
  return res_vec;
}

py::array_t<int> convert_paths_from_pathvec_to_np(const PathVec &paths,
                                                  int n) {
  size_t paths_size = paths.size();
  auto shape = std::vector<size_t>({paths_size, static_cast<size_t>(n + 1)});
  auto res_paths = py::array_t<int>(shape);
  auto res_paths_view = res_paths.mutable_unchecked<2>();

  size_t psize;
  int np1 = n + 1;
  int pctr = 0;
  
  if (paths_size > 0) {
    // Parallel processing setup
    for (size_t i = 0; i < paths_size; ++i) {
      const auto& path = paths[i];
      psize = path.size();
      if (psize > np1) {
          std::stringstream ss;
          ss << "Path length exceeds cutoff; n: " << n + 1 << "; path: ";
          std::copy(path.begin(), path.end(), std::ostream_iterator<int>(ss, " "));
          throw std::runtime_error(ss.str());
      }
      for (size_t j = 0; j < psize; ++j) {
        res_paths_view(i, j) = path[j];
        //        ptr[pctr + j] = path[j];
      }
      for (size_t j = psize; j < np1; ++j) {
        res_paths_view(i, j) = -1;
      }
      pctr += np1;
    }
  }

  return res_paths;
}

py::array_t<int> get_all_paths_np(
    const Graph& g,
    const Graph& g_inv,
    int s,
    int t,
    int n,
    bool debug) {

  if (debug) {
    std::cout << "running get_all_paths with cutoff: " << n << std::endl;
  }

  PathSet res_set_filtered = get_all_paths_internal(g, g_inv, s, t, n, debug);

  if (debug) {
    std::cout << "converting " << res_set_filtered.size() << " paths to PathVec format" << std::endl;
  }

  size_t rsf_size = res_set_filtered.size();
  std::vector<std::vector<int>> res_vec_filtered(res_set_filtered.begin(), res_set_filtered.end());

  return convert_paths_from_pathvec_to_np(res_vec_filtered, n);
}

py::array_t<int> get_all_paths_np_cached_graph(int s,
                                               int t,
                                               int n,
                                               bool debug) {
  if (m_g == m_initializer &&
      m_g_inv == m_initializer) {
    throw std::domain_error("Must first call set_graph to store the graph, before you can call get_all_paths_np_cached_graph");
  }
  
  return get_all_paths_np(m_g, m_g_inv, s, t, n, debug);
}


PathVec get_all_paths_cached_graph(int s,
                                   int t,
                                   int n,
                                   bool debug) {
  if (m_g == m_initializer &&
      m_g_inv == m_initializer) {
    throw std::domain_error("Must first call set_graph to store the graph, before you can call get_all_paths_np_cached_graph");
  }

  return get_all_paths(m_g, m_g_inv, s, t, n, debug);
}


std::vector<py::array_t<int>> get_all_paths_batch(const std::vector<std::vector<int>> & node_list,
                                                  int n,
                                                  bool debug) {
  auto get_paths_one_pair_lambda = [n, debug](std::vector<int> node_pair) -> PathVec {
    return get_all_paths_cached_graph(node_pair[0], node_pair[1], n, debug);
  };
                               
  std::vector<PathVec> paths_all_nodes(node_list.size());
  std::transform(std::execution::par,
                 node_list.begin(),
                 node_list.end(),
                 paths_all_nodes.begin(),
                 get_paths_one_pair_lambda);


  auto convert_paths_given_n = [n](const PathVec &paths) -> py::array_t<int> {
    return convert_paths_from_pathvec_to_np(paths, n);
  };
  
  std::vector<py::array_t<int>> paths_np_all_nodes(node_list.size());
  std::transform(std::execution::seq,
                 paths_all_nodes.begin(),
                 paths_all_nodes.end(),
                 paths_np_all_nodes.begin(),
                 convert_paths_given_n);
  
  return paths_np_all_nodes;
}

std::unordered_map<int, std::set<py::tuple>> bfs_limited_paths(
    const Graph& g,
    const Graph& g_inv,
    int v_start,
    int cutoff,
    bool reverse) {

    NodeToPathVec backpaths;

    backpaths = bfs_limited_paths_internal(g, g_inv, v_start, cutoff, reverse).first;
    
    std::unordered_map<int, std::set<py::tuple>> python_result;
    for (const auto& pair : backpaths) {
        std::set<py::tuple> tuple_set;
        for (const auto& vec : pair.second) {
            tuple_set.insert(py::cast(vec)); // Convert vector to tuple
        }
        python_result[pair.first] = std::move(tuple_set);
    }    
    return python_result;
}

PYBIND11_MODULE(findpaths_core, m) {
    m.doc() = "Pybind11 example plugin"; // optional module docstring
    
    m.def("_set_graph",
          &set_graph,
          "Store the graph (and the inverse graph) so it can be accessed efficiently",
          py::arg("g"), py::arg("g_inv"));
    
    m.def("_bfs_limited_paths",
          &bfs_limited_paths,
          "A function which calculates BFS paths with limited length",
          py::arg("g"), py::arg("g_inv"), py::arg("v_start"), py::arg("cutoff"), py::arg("reverse"));

    m.def("get_all_paths",
          &get_all_paths,
          "A function which obtains all paths between two given nodes",
          py::arg("g"), py::arg("g_inv"), py::arg("s"), py::arg("t"), py::arg("n"), py::arg("debug"));

    m.def("_get_all_paths_np",
          &get_all_paths_np,
          "A function which obtains all paths between two given nodes",
          py::arg("g"), py::arg("g_inv"), py::arg("s"), py::arg("t"), py::arg("n"), py::arg("debug"),
          py::return_value_policy::take_ownership);

    m.def("_get_all_paths_np_cached_graph",
          &get_all_paths_np_cached_graph,
          "A function which obtains all paths between two given nodes",
          py::arg("s"), py::arg("t"), py::arg("n"), py::arg("debug"),
          py::return_value_policy::take_ownership);

    m.def("_get_all_paths_batch",
          &get_all_paths_batch,
          "A function which obtains all paths between source and target nodes from a list of pairs of nodes",
          py::arg("node_list"), py::arg("n"), py::arg("debug"),
          py::return_value_policy::take_ownership);      
}


