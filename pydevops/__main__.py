import argparse
import importlib
import sys
import os.path
from collections import defaultdict
from pydevops.process import Process


def load_cfg(path):
    module_name = "pydevops_cfg"
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def parse_options(options_str):
    """
    A list of key=value pairs.
    e.g.
    Values with whitespaces should be in quotation marks.
    """
    result = defaultdict(list)
    for option in options_str:
        key, value = option.split("=")
        key = key.strip()
        value = value.strip()
        result[key].append(value)
    return result


# Jezeli jest ustawiony ssh/docker
# Zweryfikuj, czy na zdalnym komputerze jest pydevops w tej samej wersji
# co ten pydevops, jezeli nie -> rzuc wyjatek
# wykonaj obecna komende dokladnie z tymi samymi parametrami, tylko
# przekaz host=localhost

# jenkins projects:
# project, platform (platforma musi byc jakims parametrem, ktory mozna odczytac w Jenkinsfile)
# dzieki temu mamy mozliwosc uruchomienia builda dla wielu platform jednoczesnie)
# Typ builda (Debug, Release, RelWithInfo): parametr w Jenkinsfile, ktory nastepnie jest przekazany do
# Jenkins?
# Git pull podane repozytorium (na hoscie) -- utrzymaj hosta
# wykonaj sekwencje operacji:
# init:
# Init jest taki sam
# linux amd64: (host okreslany na podstawie parametru w jenkinsfile)
# pydevops --step=init --host=localhost --docker=file:sciezka do DockerFile (np. .docker/Dockerfile)
# Uruchom kontener docker (wykonaj build, etc.), o tagu
# Skopiuj dane do docelowego folderu: okreslony w ~/.pydevops/cfg.yml
# folder zostanie skopiowany do {build_dir}/{project_name}/git hash, jezeli folder istnieje: usun stary, zapisz nowy
# Linux arm64:
#       pydevops --step=init --host=148.81.52.232:8222 --docker=file:sciezka do dockerFile (np.docker/Dockerfile)
# skopiuj dociagniete zrodla na docelowy komputer (do jakiego folderu?) uzywajac scp
# upewnij sie, ze zdalny komputer ma zainstalowany pydevops w takiej samej wersji, co host (byc moze uruchom virtualenv -> pip install?)
# wykonaj na zdalnym polecenie pydevops (z host=localhost)
# Reszta leci po staremu
# Windows
# pydevops --step=init --host=148.81.52.232:4222
# upewnij sie, ze zdalny komputer ma zainstalowany pydevops o takiej samej wersji
# wykonaj na zdalnym polecenie pydevops (z host=localhost)
# pydevops --step=cfg
# ssh: wykonaj na zdalnym polecenie
# docker: wystartuj kontener dla obrazu o tagu taki, jak hash (byc moze lepiej wziac tag)
# ...
# pydevops --step=install
# ssh: sciezka docelowa na tym, na ktorym jest to wykonywane (uwaga: trzeba sprawdzic, czy jest Windows, czy Linux)
# docker: zainstaluj w folderze hosta (docker powinien zostac uruchomiony z zamontowanym folderem docelowym)

# ------ Plik konfiguracyjny
# steps = {

# }
# Okresla zbior steps, ktore moga byc wykonane (cmake_cfg, build, etc.) -> dla kazdego step przypisuje odpowiednia operacje
# Dla kazdej z operacji okreslone beda domyslne parametry (jezeli jakis bedzie brakowalo, uzytkownik bedzie musial wskazac)
# Okresla domyslny proces, ktory bedzie wykonany w momencie zrobienia pydevops . np. sekwencje operacji cfg, build, install
# Pydevops umozliwia wykonanie pojedynczych krokow, ale rowniez szeregu krokow (jak przekazywac parametry? id_operacji:nazwa_parametru, jest też możliwosc wskazania )
# plik konfiguracyjny
# init steps: [cfg]
# build steps: [build, install]
# wykonanie pydevops, w sytuacji gdy nie isntieje folder .pydevops, skutkuje wykonaniem init steps, nastepnie build steps
#


def main():
    parser = argparse.ArgumentParser(description="DevOps tools")
    parser.add_argument("--step", dest="step",
                        help="Step to execute, when not provided, "
                             "the sequence of steps will be executed",
                        type=str, required=False, default=None)
    parser.add_argument("--host", dest="host",
                        help="Host on which the command should be executed."
                             " The default `localhost` means that "
                             "the process will be executed on the local "
                             "computer. Otherwise, all communication with "
                             "the remote host will be done via ssh.",
                        type=str, required=False, default="localhost")
    parser.add_argument("--docker", dest="docker",
                        help="Docker image tag (img::image_tag), "
                             "container name/id "
                             "(container::container_name/id) "
                             "or the path to the Dockerfile (file::path). "
                             "By default (None) docker will be not used to "
                             "execute the process.",
                        type=str, required=False, default=None)
    parser.add_argument("--src_dir", dest="src_dir",
                        help="Path to the source directory.",
                        type=str, required=False, default=".")
    parser.add_argument("--build_dir", dest="build_dir",
                        help="Path to the build directory.",
                        type=str, required=False, default="./build")
    parser.add_argument("--options", dest="options",
                        help="A list of options that should be passed "
                             "to the process steps.",
                        type=str, required=False, default=[],
                        nargs="*")
    args = parser.parse_args()
    step = args.step
    host = args.host
    docker = args.docker
    src_dir = args.src_dir
    build_dir = args.build_dir
    options = parse_options(args.options)
    options["src_dir"] = src_dir
    options["build_dir"] = build_dir
    options["docker"] = docker
    options["host"] = host
    options["step"] = step
    # Remote and/or docker
    if host != "localhost" or docker is not None:
        # TODO reconstruct cmd
        # note: --host should be replaced to localhost
        # note: --docker should be removed
        # create appropriate environment
        # if the directory in the remote
        # 1. start remote process (needed for docker) if necessary
        # 2. checkout
        # 2.

        # specjalne kroki
        # --step=clean jezeli jest ssh process: usun zdalnie zrodla, jezeli jest docker process: usun kontener, w przeciwnym przypadku usun build
        # --step=init: jezeli jest docker: wystartuj kontener dockerowy, w przeciwnym razie nop
        # --step=checkout: jezeli jest remote/docker: zrob git checkout, w przeciwnym przypadku NOP
        # To wszystko powyzsze mogloby byc czescia jednej komendy init?
        # dalej kroki takie jak w przekazanym pliku konfiguracyjnym, tylko wolac zdalnie
        pass
    # Localhost and not Docker
    else:
        cfg = load_cfg(os.path.join(build_dir, "devops.py"))
        steps = cfg.steps
        process = Process(steps, options)
        return process.do()


if __name__ == "__main__":
    sys.exit(main())
