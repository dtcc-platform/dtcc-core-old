cmake_minimum_required(VERSION 3.12...3.18)
project(generate_protobuf LANGUAGES CXX)

set(CMAKE_CXX_FLAGS "-Wall -Werror -fPIC")


find_package(pybind11 REQUIRED)
find_package(Protobuf REQUIRED)

set(THREADS_PREFER_PTHREAD_FLAG ON)
find_package(Threads REQUIRED)

# build protobuf
add_subdirectory(dtcc-model/protobuf)
include_directories(${PROTOBUF_INCLUDE_DIRS}) 
include_directories(${CMAKE_CURRENT_BINARY_DIR}/dtcc-model)
include_directories(${CMAKE_SOURCE_DIR}/dtcc-model)

link_directories(/usr/local/lib)

add_subdirectory(src/dtcc)




