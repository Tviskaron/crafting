import getpass
import json
import pathlib
from random import sample


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


def create_name(container_name_config: dict) -> str:
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
    for part in container_name_config['parts']:
        if part not in parts_of_name:
            names = ", ".join(parts_of_name.keys())
            raise KeyError('"{}" is not a part of name. Existing parts are: {}'.format(part, names))
        else:
            result.append(parts_of_name[part]())
    return container_name_config['delimiter'].join(result)
