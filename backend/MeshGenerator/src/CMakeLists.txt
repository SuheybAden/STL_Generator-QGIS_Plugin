cmake_minimum_required(VERSION 3.14)

project(MeshGenerator LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_library(MeshGenerator SHARED
  MeshGenerator_global.h
  meshgenerator.cpp
  meshgenerator.h
)

set_target_properties(MeshGenerator
  PROPERTIES
  C_VISIBILITY_PRESET hidden
  CXX_VISIBILITY_PRESET hidden
)

target_compile_definitions(MeshGenerator PRIVATE MESHGENERATOR_LIBRARY)

install(TARGETS MeshGenerator
  LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
)