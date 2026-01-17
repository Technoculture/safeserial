cmake_minimum_required(VERSION 3.10)
project(safeserial_sdk LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

enable_testing()

# Sanitizer configuration (Clang/GCC only)
list(APPEND CMAKE_MODULE_PATH "${CMAKE_SOURCE_DIR}/cmake")
set(SAFESERIAL_SANITIZERS "" CACHE STRING "Semicolon or comma-separated sanitizers (address,undefined,thread,leak)")
include(Sanitizers)

option(SAFESERIAL_COVERAGE "Enable coverage reporting" OFF)
option(SAFESERIAL_ENABLE_FUZZING "Enable fuzzing targets (Clang only)" OFF)

if(SAFESERIAL_COVERAGE)
    if(MSVC)
        message(FATAL_ERROR "Coverage is not supported with MSVC")
    endif()
    add_compile_options(--coverage -O0 -g)
    add_link_options(--coverage)
endif()

# Library is in src/
add_subdirectory(src)

# Example App
add_subdirectory(examples)

# Test Suite
add_subdirectory(tests)
