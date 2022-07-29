from pydevops.sh import Shell


class DockerClient:
    """
    Accepts the following options:

    This is a context manager; entering this context:
    - docker container will be built if
    build -> image id
    create -> container id
    start -> container id
    trzeba w kontekście zapisać informacje, co jest dostepne
    np. 'name:: nazwa obrazu; build:: -f .docker/build/Dockerfile;run:: -v asada:/asdadsa asdadada/asdadas' -> to zbuduje nowy obraz,
    -> w wyniku tego dostaniemy image id
    -- > w wyniku tego w env powinien pojawic sie zapis:
    'run::image_id -v asdsada/adsadsada asasdsasadadsa'
    Nastepnie ten container id powinien byc uzywany do wszystkich polecen
    Wszystkie polecenia powinny byc wykonywane w odpowiednim
    Teraz:
    - jezeli uzytkownik ponownie w docker wskaze build:: -> konieczne jest przebudowanie kontenera (bo np. chce swiezego builda)
    - jezeli image_id nie istnieje, konieczne jest ponowne wykonanie build: moze wystarczy na razie zrobic to z clean?
    """

    def __init__(self, parameters: str):
        self.parameters = self._index_parameters(parameters)
        self.image_id = None
        self.cmd_exec = Shell()
        build_params = self.parameters.get("build", None)
        name = self.parameters["name"]
        if build_params is not None:
            self.cmd_exec.run(f"docker build . {build_params} -t {name}")
            # Do not build the image on the next run.
            self.parameters.pop("build")
        # Use the latest image with a given name
        self.image_id = self.cmd_exec.run(f"docker images -q {name}",
                                          capture_stdout=True).stdout

    def sh(self, cmd: str):
        if self.image_id is None:
            raise ValueError("Build docker image first.")
        run_params = self.parameters.get("run", "")
        self.cmd_exec.run(f"docker run --rm {run_params} {self.image_id} -l -c \"{cmd}\"")

    @property
    def params(self):
        result = []
        for k, v in self.parameters.items():
            result.append(f"{k}::{v}")
        return ";".join(result)

    def _index_parameters(self, params: str) -> dict:
        params = params.strip().strip(";")
        params = params.split(";")
        result = {}
        for p in params:
            p = p.strip().strip("::")
            p = p.split("::")
            if len(p) != 2:
                raise ValueError("Syntax error in docker options; each options"
                                 "should have a format name::params")
            key, values = p
            result[key] = values
        return result
