cmake_minimum_required(VERSION 3.24)
project(rotator_firmware LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_library(rotator_core
  src/sensor/cde_dual_end_pot.cpp
  src/drive/triac_ac_relay_brake.cpp
  src/motion/motion_controller.cpp
  src/protocol/gs232.cpp
  src/settings/settings.cpp
)
target_include_directories(rotator_core PUBLIC include)
target_compile_options(rotator_core PRIVATE -Wall -Wextra -Wpedantic -Werror)

include(CTest)
if(BUILD_TESTING)
  include(FetchContent)
  FetchContent_Declare(
    googletest
    URL https://github.com/google/googletest/archive/refs/tags/v1.15.2.zip
  )
  set(INSTALL_GTEST OFF CACHE BOOL "" FORCE)
  set(BUILD_GMOCK OFF CACHE BOOL "" FORCE)
  FetchContent_MakeAvailable(googletest)

  add_executable(rotator_tests
    tests/cde_dual_end_pot_test.cpp
    tests/triac_drive_test.cpp
    tests/motion_controller_test.cpp
    tests/gs232_test.cpp
    tests/settings_test.cpp
  )
  target_include_directories(rotator_tests PRIVATE tests)
  target_link_libraries(rotator_tests PRIVATE rotator_core GTest::gtest_main)
  target_compile_options(rotator_tests PRIVATE -Wall -Wextra -Wpedantic -Werror)

  add_test(NAME rotator_host_tests COMMAND rotator_tests)
endif()
