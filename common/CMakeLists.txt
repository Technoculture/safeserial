add_library(common_lib STATIC 
    protocol/crc16.cpp)


target_include_directories(common_lib PUBLIC .)

