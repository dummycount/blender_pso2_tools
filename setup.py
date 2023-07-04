from setuptools import Extension, setup
import os
import shlex

PYTHON_INCLUDE_PATH = "src/Python/Include"
PYTHON_LIB_PATH = "src/Python/libs"

LIB_DIRECTXTEX_PATH = "DirectXTex/DirectXTex"

LIB_DIRECTXTEX_SOURCE = [
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


directxtex_sources = [f"{LIB_DIRECTXTEX_PATH}/{file}" for file in LIB_DIRECTXTEX_SOURCE]

SOURCE = [
    "dds.cpp",
    "import_dds.cpp",
]

extension_sources = [f"src/{file}" for file in SOURCE]

# CFLAGS/LDFLAGS are ignored when building extensions, so add those manually.
cflags = shlex.split(os.getenv("CFLAGS", ""))
ldflags = shlex.split(os.getenv("LDFLAGS", ""))

setup(
    ext_modules=[
        Extension(
            name="pso2_tools.import_dds",
            sources=[*extension_sources, *directxtex_sources],
            libraries=["d3d11", "ole32"],
            include_dirs=[LIB_DIRECTXTEX_PATH],
            extra_compile_args=[
                "/std:c++20",
                "/O2",
                "/GR-",
                "/fp:fast",
                *cflags,
            ],
            extra_link_args=ldflags,
        ),
    ]
)
