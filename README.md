# PyDevOps

## Introduction

Application build tools used in us4us projects.

## Usage

### Configuring project pipeline

Project configuration file `devops.py` should be stored in the project's 
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

######  Configure

Runs CMake's configure step.

- options:
  - `src_dir`: path to the source directory
  - `build_dir`: path to the build directory
  - `generator`: cmake project generator name (cmake option -G) (e.g. "Unix Makefiles")
  - `*`: all the other options will be passed to the `cmake` as `-{parameter}=value`


###### Build

Runs CMake's build step.

- options:
    - `src_dir`: path to the source directory
    - `build_dir`: path to the build directory
    - `config`: build type to apply on the build step (Debug or Release), on Windows, on other platforms use configure option `DCMAKE_BUILD_TYPE`
    - `j`: number of parallel jobs to run
    - `verbose`: turn on verbose output


###### Test

Runs CTest in the given build directory.

- options:
    - `src_dir`: path to the source directory
    - `build_dir`: path to the build directory
    - `C`: build type to apply (e.g. Debug or Release)
    - `j`: number of parallel jobs to run
    - `verbose`: turn on verbose output

###### Install

- options:
    - `build_dir`: path to the build directory
    - `config`: build type to use (e.g. Debug or Release)
    - `prefix`: path to the output directory

##### Conan

###### Install

Runs `conan install` step (installs all the dependencies required by the project).

- options:
    - `src_dir`: path to the source directory
    - `build_dir`: path to the build directory
    - `build_type`: build type to use (e.g. Debug or Release)
    - `build` (optional, default: None): what build strategy to use (e.g. build=missing will build only the missing packages)
    - `profile` (optional, default: None): path to the conan profile to use
    - `conan_home` (optional, default: None): path to the directory, where conan home should be located

##### us4us



###### Package

Publish documentation according to policy used by us4us.

- options:
    - `src_artifact`: list of paths (glob) to the input artifacts, paths should be separated by semicolons
    - `dst_dir`: path where the package should be located
    - `dst_artifact` (optional, default `__same__`) the name of the output artifact
    - `release_name`: version of the release (will be used as a name of the docs folder)

###### PublishDocs

Publish documentation according to policy used by us4us.

- options:
    - `install_dir`: path to the directory, where build and installed package is located
    - `repository`: full url to the repository, where documentation should be located
    - `commit_msg`: commit message to use,
    - `version`: version of the release (will be used as a name of the docs folder)


###### PublishReleases

Publishes given artifacts located on the current host in the given
repository as a given dst_artifact.

If the src artifact is a regular file, it will be renamed to the
given dst_artifact (if provided).

If there is no release with the given release_name, it will be created.
Release name with pattern different than `^v[0-9]+\.[0-9]+\.[0-9]+$`
will be marked as pre-release.  If the release is pre-release, a new tag with the same name as branch
will be created.

Note: if there are multiple artifacts pointed by src_artifact, and all
of them are regular files, the name of the artifacts will not be changed
to the dst_artifact. If there are multiple files and some of them are
directories, all the files will be zipped to a single dst_artifact.zip file.

- options:
    - `release_name`: target release name
    - `src_artifact`: source artifact name (glob),
    - `dst_artifact` (optional, if not provided, the src_artifact name will be used): the name of the artifact (asset) to create
    - `description` (optional, default: empty string): text that should be appended to the release description,
    - `token`: Github Personal Access Token (PAT)
    - `repository_name`: Github user_name/repository_name

## License

MIT License
