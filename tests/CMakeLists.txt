enable_testing()

find_package(GTest REQUIRED)

add_executable(test_crc16
    test_crc16.cpp
    ../src/protocol/crc16.cpp
)

target_include_directories(test_crc16 PRIVATE ../src)

target_link_libraries(test_crc16
    GTest::GTest
    GTest::Main
)

add_test(NAME CRC16Tests COMMAND test_crc16)

