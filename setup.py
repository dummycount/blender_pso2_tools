from setuptools import Extension, setup
import sys


_PYTHON_INCLUDE_PATH = "src/Python/Include"
_PYTHON_LIB_PATH = "src/Python/libs"

_LIB_DIRECTXTEX_PATH = "DirectXTex/DirectXTex"

_LIB_DIRECTXTEX_SOURCE = [
    "BC.cpp",
    "BC4BC5.cpp",
    "BC6HBC7.cpp",
    "DirectXTexCompress.cpp",
    "DirectXTexConvert.cpp",
    "DirectXTexDDS.cpp",
    "DirectXTexHDR.cpp",
    "DirectXTexImage.cpp",
    "DirectXTexMipmaps.cpp",
    "DirectXTexMisc.cpp",
    "DirectXTexNormalMaps.cpp",
    "DirectXTexPMAlpha.cpp",
    "DirectXTexResize.cpp",
    "DirectXTexTGA.cpp",
    "DirectXTexUtil.cpp",
    "DirectXTexFlipRotate.cpp",
    "DirectXTexWIC.cpp",
]


directxtex_sources = [
    f"{_LIB_DIRECTXTEX_PATH}/{file}" for file in _LIB_DIRECTXTEX_SOURCE
]

_SOURCE = [
    "dds.cpp",
    "import_dds.cpp",
]

extension_sources = [f"src/{file}" for file in _SOURCE]

setup(
    ext_modules=[
        Extension(
            name="pso2_tools.import_dds",
            sources=[*extension_sources, *directxtex_sources],
            libraries=["d3d11", "ole32"],
            include_dirs=[_LIB_DIRECTXTEX_PATH, _PYTHON_INCLUDE_PATH],
            library_dirs=[_PYTHON_LIB_PATH],
            extra_compile_args=[
                "/std:c++20",
                "/O2",
                "/GR-",
                "/fp:fast",
            ],
        ),
    ]
)
