cmake_minimum_required(VERSION 3.4)
project(findpaths_core LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
find_package(oneDPL REQUIRED)
find_package(TBB REQUIRED)
find_package(pybind11 REQUIRED)
pybind11_add_module(findpaths_core findpaths-core.cpp)
target_link_libraries(findpaths_core PRIVATE TBB::tbb)
add_compile_options(-fexperimental-library)


