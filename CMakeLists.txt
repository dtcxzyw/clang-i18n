cmake_minimum_required(VERSION 3.12)

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

include_directories(${LLVM_INCLUDE_DIRS})
include_directories(${CLANG_INCLUDE_DIRS})

add_library(clang-i18n MODULE clang-i18n.cpp)
target_link_libraries(clang-i18n PRIVATE dl)
if (${LLVM_LINK_LLVM_DYLIB})
  if(NOT DEFINED LLVM_SHLIB_SYMBOL_VERSION)
    # "Symbol version prefix for libLLVM.so and libclang-cpp.so"
    set(LLVM_SHLIB_SYMBOL_VERSION "LLVM_${LLVM_VERSION_MAJOR}.${LLVM_VERSION_MINOR}")
  endif()
  message(STATUS "LLVM_SHLIB_SYMBOL_VERSION: ${LLVM_SHLIB_SYMBOL_VERSION}")
  configure_file(simple_version_script.map.in simple_version_script.map)
  target_link_libraries(clang-i18n PRIVATE clang-cpp LLVM)
  target_link_options(clang-i18n PRIVATE -Wl,--version-script,${CMAKE_CURRENT_BINARY_DIR}/simple_version_script.map)
else()
  target_link_libraries(clang-i18n PRIVATE clangBasic LLVMSupport LLVMOption)
endif()
