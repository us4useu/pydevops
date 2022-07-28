# PyDevOps

## Introduction

Application build tools used in us4us projects.

## Usage

### Configuring project pipeline

Project configuration file `pydevops.py` should be stored in the project's 
root directory. The configuration file should have the following properties:

- `stages`: a dictionary (mapping) from stage `name: str` to the `list` of 
   steps that should be run in the stage. The list of steps can be specified
   in one of the following ways:
  - list of pairs `(name: str, Step)` where `name` is the name of the step, 
    `Step` is a class that implements `pydevops.base.Step` interface,
  - list of `Step` classes, `step_name` will be set to the fully qualified name 
     of the class),
  - a single pair of values `(name: str, Step)`,
  - a single value `Step`.
- `init_stages`: a list of stages (names) that should be run during pipeline initialization,
- `build_stages`: a list of stages that should be run during pipeline build,
- _(optional)_`aliases`: option aliases, it can be set to a `dict` that maps
  alias `name: str` to list of the target option names, 
- _(optional)_`defaults`: parameter defaults,
- _(optional)_`build_directory`: default build directory.


### Running project pipeline

To run project pipeline, run `pydevops` program:

```
pydevops \
 --src_dir=/path/to/src/dir \
 --build_dir=/path/to/build/dir \
 --stage=stage_name \
 --options NAME1=VALUE1 NAME2=VALUE2
```

Project pipeline is executed in the following steps:

1. Initialize the pipeline on the target host, if not already initialized.
    - Pipeline is initialized if the `{build_dir}/pydevops_ctx.yml` exists.
    - During initialization, the stages from the `init_stages` list are executed, in order according to the list.
2. Run the list stages indicated by the `--stage` parameter.
    - The `--stage` parameter is optional, by default the `build_stages` are executed.

#### Local host

By default, the parameter `host` is set to `localhost` and this means that 
all the stages will be executed on the host, on which pydevops was called. 

#### Remote host via SSH

It is also possible to redirect pipeline execution to remote host. 

Requirements:
- SSH protocol server should be installed and running on the remote host,
- Python interpreter and `virtualenv` package should be installed on the 
  remote machine.

To run the pipeline on the remote host, the following parameters needs to be
passed to `pydevops`:
- `host`: it should be set to the address of the target host. Some SSH server 
    should be running on the target host. It is possible to specify target port, 
    by using the following address format: `user@ip_address:port_number`.
- `local_dir`: a path to the source directory on the  **local host**. That 
   local source directory will be copied to the remote host during 
   initialization to the path specified by the `src_dir` directory.
- `src_dir`: a path to the source directory on the **remote host**. This is the 
   source code that will be used by remote `pydevops` to run 
- `build_dir`:

During initialization:
1. local `pydevops` copies `local_dir` to the address `user@ip_address:port_number/src_dir`,
2. local `pydevops` puts in the `pydevops_ctx.yml` file information, that 
   all the following commands should be executed on the remote host,
3. local `pydevops` creates a new virtual environment in the folder `{src_dir}/.venv/pydevops`,
   and then installs the `pydevops` package in it with the same version as the local host version,
4. remote `pydevops` initializes its copy of the pipeline.

Any subsequent calls (that do not require pipeline initialization) will be redirected 
to the remote pydevops via the SSH calls.

#### Docker

It is also possible to redirect pipeline execution to some external docker 
container.

All the rules described in the "Remote host via SSH" section also apply to
building a pipeline in the docker container, with the following exceptions:
- use parameter `docker` to specify what container/image/docker file should
  be used to execute the pipeline,
- during initialization:
  - if the target docker container is not running, start it,
  - if the docker image is used instead, pydevops start new docker container and
    remembers its id in the local host `pydevops_ctx.yml`,
  - if the docker file is used instead, build the docker image, start the container
    and remember their ids in the local host `pydevops_ctx.yml`.

### Options

The individual steps of the pipeline can be addressed using the following syntax:

```
/stage/step
```

To address a certain option `abc` of the step `/stage/step`, just append 
the parameter to the above path, i.e.:

```
/stage/step/abc
```

Note: there are a couple of exception to the above rule:
- it is also possible to address a step from a single-step stage using the following shortcut: `/stage/abc`
  That is, you can skip the step name.
- if you are running only a single stage (i.e. `--stage` contains description) it is sufficient to use 
  `step/abc`; in addition, if that stage consists of a single step, you can skip step name, i.e. `abc`.

On the other side, The step implementation will be able to access the parameter
`abc` simply by using e.g. `ctx.get_parameter("abc")`.

You can pass options to pipeline by the `pydevops` `--options` parameter, e.g.
```
--options /stage/step/abc=Release
```

#### Aliases

Sometimes it is necessary to pass the same parameter value to many
different stages of the building pipeline. For example to build libraries
in the `Debug` mode, probably you would also like to configure conan to download 
dependencies in with the debug symbols, set the `CMAKE_BUILD_TYPE=Debug` 
on initialization, and at the final stage specify `--config Debug` in 
the `cmake install`.

The option aliases can be specified in the project pipeline configuration file (parameter `aliases`)
and allows you to specify a single option name for multiple different option paths.
See examples for more details.

#### Default parameters

It is possible to specify default option values to be used when no value 
is specified by the user. See examples for more details.

### Steps

#### Available steps

Currently `pydevops` provides the implementation of the following steps:

##### CMake

###### Configure

- `pydevops.cmake.Configure`,
- options:
  - asdsadaas

###### Build

###### Test

###### Install


## License

MIT License
