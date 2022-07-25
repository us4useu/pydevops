import os
import pydevops.cmake as cmake
import pydevops.conan as conan
import pydevops.us4us as us4us


def get_default_generator_for_current_os():
    if os.name == "nt":
        return "Visual Studio 15 2017 Win64"
    else:
        return "Unix Makefiles"


# pydevops version
version = "0.1.0"

stages = {
    "cfg": (
        ("conan", conan.Install),
        ("cmake", cmake.Configure),
    ),
    "build": cmake.Build,
    "test": cmake.Test,
    "install": cmake.Install,
    "publish_docs": us4us.PublishDocs,
    "publish_releases": us4us.PublishReleases
}

init_stages = ["cfg"]
build_stages = ["build", "test", "install"]

aliases = {
    "build_type": (
        "/cfg/conan/build_type",
        "/cfg/cmake/CMAKE_BUILD_TYPE",
        "/build/config",
        "/install/config"
    ),
    "python": (
        "/cfg/cmake/ARRUS_BUILD_PYTHON"
    ),
    "matlab": (
        "/cfg/cmake/ARRUS_BUILD_MATLAB"
    ),
    "docs": (
        "/cfg/cmake/ARRUS_BUILD_DOCS"
    ),
    "tests": (
        "/cfg/cmake/ARRUS_RUN_TESTS"
    ),
}

defaults = {
    "build_type": "Release",
    "/cfg/cmake/generator": get_default_generator_for_current_os()
}
