import getpass
import json
import os
import pathlib
from random import sample
from tarfile import TarFile
from builtins import open as bltn_open


def get_minecraft_name() -> str:
    """
    Creates an pair of adjective and noun from minecraft domain in CamelCase format.
    The nouns and adjectives come from "minecraft_names.json" file.
    Some examples: GlassSunflower, EmptyCube, GoldBluet.
    :return:
    """
    try:
        with open(str(pathlib.Path(__file__).parents[0] / "minecraft_names.json"), "r") as items_file:
            items = json.load(items_file)
    except FileNotFoundError:
        with open("minecraft_names.json", "r") as items_file:
            items = json.load(items_file)

    result = sample(items['adj'], k=1)[0] + sample(items['nn'], k=1)[0]
    return result


def create_name() -> str:
    """
    Creates full name for docker container from existing parts (see parts_of_name).
    Example:
        container_name_config: {"delimiter": '.', "parts": ['user', 'minecraft']}
        return:
    :param container_name_config:
    :return: user.SmoothClay
    """
    result = []
    parts_of_name = {
        'user': lambda: getpass.getuser(),
        'minecraft': lambda: get_minecraft_name(),
    }
    container_name_config = {"delimiter": '.', "parts": ['user', 'minecraft']}
    for part in container_name_config['parts']:
        if part not in parts_of_name:
            names = ", ".join(parts_of_name.keys())
            raise KeyError('"{}" is not a part of name. Existing parts are: {}'.format(part, names))
        else:
            result.append(parts_of_name[part]())
    return container_name_config['delimiter'].join(result)


class PatchedTarfile(TarFile):

    def add(self, name, arcname=None, recursive=True, *, filter=None, ignore=None):
        """Add the file `name' to the archive. `name' may be any type of file
           (directory, fifo, symbolic link, etc.). If given, `arcname'
           specifies an alternative name for the file in the archive.
           Directories are added recursively by default. This can be avoided by
           setting `recursive' to False. `filter' is a function
           that expects a TarInfo object argument and returns the changed
           TarInfo object, if it returns None the TarInfo object will be
           excluded from the archive.
        """
        if ignore and os.path.abspath(name) in map(os.path.join, ignore):
            print('ignoring:', name)
            return

        self._check("awx")

        if arcname is None:
            arcname = name

        # Skip if somebody tries to archive the archive...
        if self.name is not None and os.path.abspath(name) == self.name:
            self._dbg(2, "tarfile: Skipped %r" % name)
            return

        self._dbg(1, name)

        # Create a TarInfo object from the file.
        tarinfo = self.gettarinfo(name, arcname)

        if tarinfo is None:
            self._dbg(1, "tarfile: Unsupported type %r" % name)
            return

        # Change or exclude the TarInfo object.
        if filter is not None:
            tarinfo = filter(tarinfo)
            if tarinfo is None:
                self._dbg(2, "tarfile: Excluded %r" % name)
                return

        # Append the tar header and data to the archive.
        if tarinfo.isreg():
            with bltn_open(name, "rb") as f:
                self.addfile(tarinfo, f)

        elif tarinfo.isdir():
            self.addfile(tarinfo)
            if recursive:
                for f in sorted(os.listdir(name)):
                    self.add(os.path.join(name, f), os.path.join(arcname, f),
                             recursive, filter=filter, ignore=ignore)

        else:
            self.addfile(tarinfo)

def get_size_by_path(path, ignore=None, max_size=None):
    if ignore is None:
        ignore = []
    result = 0
    if os.path.abspath(path) in ignore:
        return 0
    if path.is_file():
        return path.stat().st_size
    for f in path.iterdir():
        result += get_size_by_path(f, ignore, max_size - result if max_size else None)
        if max_size is not None and result > max_size:
            return result
    return result

