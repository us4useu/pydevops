from pydevops.base import StepInstance
from pydevops.cmake import (
    Configure, Build, Test, Install
)

steps = {
    "cfg": StepInstance(
        cls=Configure,
        defaults={
            "BUILD_TYPE": "Release",
            ""
        }
    )
    "build": Build,
    "test": Test,
    "install": Install
}

init_steps = ["cfg"]
build_steps = ["build", "install"]