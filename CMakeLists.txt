cmake_minimum_required(VERSION 3.8)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

set(CMAKE_FIND_PACKAGE_SORT_ORDER NATURAL)
set(CMAKE_FIND_PACKAGE_SORT_DIRECTION DEC)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

project(clang-i18n)

find_package(LLVM REQUIRED CONFIG)
find_package(Clang REQUIRED CONFIG)
message(STATUS "Found LLVM ${LLVM_PACKAGE_VERSION}")
message(STATUS "Using LLVMConfig.cmake in: ${LLVM_DIR}")
include(AddLLVM)

if (NOT ${HAVE_CLANG_PLUGIN_SUPPORT})
  message(FATAL_ERROR "This project requires Clang plugin support.")
endif()

include_directories(${LLVM_INCLUDE_DIRS})
include_directories(${CLANG_INCLUDE_DIRS})
set(LLVM_LINK_COMPONENTS clangFrontend)

add_library(clang-i18n MODULE clang-i18n.cpp)
target_link_libraries(clang-i18n PRIVATE dl)
target_link_libraries(clang-i18n PRIVATE clangBasic LLVMSupport)
# target_link_libraries(clang-i18n PRIVATE clang-cpp LLVM)
