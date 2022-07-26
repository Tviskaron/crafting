from pydantic import BaseModel, Field, Extra
from typing import List

from .utils import create_name


class Container(BaseModel, extra=Extra.allow):
    image: str = "python:slim"
    command: str = '''python3 -c "print('Hello world, we are crafting here!')" '''
    tty: bool = True
    name: str = Field(default_factory=create_name)
    working_dir: str = None
    detach: bool = None
    stdin_open: bool = None


class HostConfig(BaseModel, extra=Extra.allow):
    network_mode: str = 'host'
    mounts: list = []


class Code(BaseModel, extra=Extra.forbid):
    folder: str = None
    volume_attach: List[str] = []
    ignore: List[str] = []


class Cfg(BaseModel, extra=Extra.ignore):
    container: Container = Container()
    host_config: HostConfig = HostConfig()
    code: Code = Code()


class MountVolume(BaseModel, extra=Extra.allow):
    target: str = None
    source: str = None
    read_only: bool = None
    type: str = 'volume'
