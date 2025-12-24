add_executable(serial_app main.cpp)
target_link_libraries(serial_app PRIVATE transport_lib common_lib)
