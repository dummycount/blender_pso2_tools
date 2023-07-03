cmake_minimum_required(VERSION 3.26.0)
project(pso2_tools)

set(CMAKE_CXX_STANDARD 20)

set(BUILD_TOOLS OFF)
set(BUILD_SAMPLE OFF)
set(BUILD_DX11 OFF)
set(BUILD_DX12 OFF)

add_subdirectory(DirectXTex)
add_subdirectory(src)