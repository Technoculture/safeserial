cmake_minimum_required(VERSION 3.10)
project(crc_serial_proto LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_subdirectory(common)
add_subdirectory(app)
add_subdirectory(transport)
add_subdirectory(tests)


