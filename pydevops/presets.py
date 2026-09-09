import json
import os


CONFIGURE = "configurePresets"
BUILD = "buildPresets"
TEST = "testPresets"


def read_presets(presets_path: str, kind: str = CONFIGURE, visited=None):
    """
    Reads presets of the given kind from the given CMake presets file,
     the "include" entries.

    :param presets_path: path to the presets file to read
    :param kind: presets to read: CONFIGURE, BUILD or TEST
    :param visited: paths already read (guards against include cycles)
    """
    if visited is None:
        visited = set()
    presets_path = os.path.abspath(presets_path)
    if presets_path in visited or not os.path.isfile(presets_path):
        return []
    visited.add(presets_path)
    with open(presets_path) as f:
        data = json.load(f)

    presets = list(data.get(kind) or [])
    for included in (data.get("include") or []):
        if not os.path.isabs(included):
            included = os.path.join(os.path.dirname(presets_path), included)
        presets.extend(read_presets(included, kind, visited))
    return presets


def _read_conan_presets(src_dir: str, build_dir: str, kind: str):
    """
    Reads the conan-generated presets of the given kind.
    """
    presets = read_presets(
        os.path.join(src_dir, "CMakeUserPresets.json"), kind)
    if not presets:
        # conan writes the presets to the output folder.
        presets = read_presets(
            os.path.join(build_dir, "CMakePresets.json"), kind)
    return [p for p in presets if "name" in p and not p.get("hidden")]


def find_conan_preset(src_dir: str, build_dir: str, build_type: str):
    """
    Returns the conan-generated CMake configure preset matching the given
    build type, or None when there is no such preset.
    """
    presets = _read_conan_presets(src_dir, build_dir, CONFIGURE)
    if not presets:
        return None
    matched = [
        p for p in presets
        if (p.get("cacheVariables") or {}).get("CMAKE_BUILD_TYPE", "").lower()
           == build_type.lower()
    ] or presets
    return matched[0]


def find_conan_build_preset(src_dir: str, build_dir: str, build_type: str,
                            kind: str = BUILD):
    """
    Returns the conan-generated build (or test) preset to use with the
    configure preset for the given build type, or None when there is none.

    :param kind: BUILD or TEST
    """
    configure = find_conan_preset(src_dir, build_dir, build_type)
    if configure is None:
        return None
    presets = [p for p in _read_conan_presets(src_dir, build_dir, kind)
               if p.get("configurePreset") == configure["name"]]
    matched = [
        p for p in presets
        if p.get("configuration", "").lower() == build_type.lower()
    ] or presets
    return matched[0] if matched else None


def preset_binary_dir(preset, src_dir: str):
    """
    Returns the directory the given configure preset builds in, or None when
    the preset does not declare one.

    :param preset: configure preset, as returned by find_conan_preset
    :param src_dir: source dir, used to expand the ${sourceDir} macro
    """
    binary_dir = preset.get("binaryDir")
    if not binary_dir:
        return None
    binary_dir = (binary_dir
                  .replace("${sourceDir}", src_dir)
                  .replace("${presetName}", preset.get("name", "")))
    if not os.path.isabs(binary_dir):
        binary_dir = os.path.join(src_dir, binary_dir)
    return binary_dir
