cmake_minimum_required(VERSION 3.10)
project(data_bridge_sdk LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Library is in src/
add_subdirectory(src)

# Example App
add_subdirectory(examples)

# Test Suite
add_subdirectory(tests)
