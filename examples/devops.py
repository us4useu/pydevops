import pydevops.cmake as cmake
import pydevops.conan as conan
import pydevops.us4us as us4us

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

aliases = {
    "build_type": (
        "cfg/conan/build_type",
        "cfg/cmake/CMAKE_BUILD_TYPE",
        "build/config",
        "install/config"
    )
}

defaults = {
    "build_type": "Release",
}

build_directory = "build"

# W kontekście zapisane zostaną ostatnio użyte parametry
# TODO lista parametrow powinna zostac zapisana w build_directory?
# Bedzie to lista parametrow, ktore zostana uzyte w sytuacji, gdy inne nie zostaly przekazane
# Mapa parametrow - precedencja:
# parametry przekazane w linii komend
# parametry zapisane w kontekscie
# parametry domyslne
# W ramach kazdego, precedencja namespace:
# parametry lokalne w step
# parametry lokalne w stage
# parametry globalne

init_stages = ["cfg"]
build_stages = ["build", "test", "install"]
