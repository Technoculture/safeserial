add_library(transport_lib STATIC) 

if(WIN32)
    target_sources(transport_lib PRIVATE ../platform/windows/windows_serial.cpp)
else()
    target_sources(transport_lib PRIVATE ../platform/linux/linux_serial.cpp)
endif()

target_include_directories(transport_lib PUBLIC include)
