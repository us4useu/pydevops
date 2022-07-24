from pydevops.base import Step, StepContext


class Configure(Step):

    def __init__(self):


    def execute(self, ctx: StepContext):
        ctx.sh("cmake")
        # TODO dorzuc do


class Build(Step):
    pass


class Install(Step):
    pass


class Test(Step):
    pass

