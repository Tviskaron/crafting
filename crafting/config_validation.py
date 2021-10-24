from pydantic import BaseModel, Field
from typing import List

from utils import create_name


class Container(BaseModel):
    image: str = "python:slim"
    command: str = '''python3 -c "print('Hello world, crafting here!')" '''
    tty: bool = True
    name: str = Field(default_factory=create_name)
    working_dir: str = None
    detach: bool = None
    stdin_open: bool = None


class HostConfig(BaseModel):
    network_mode: str = 'host'
    runtime: str = None
    mounts: list = []


class Code(BaseModel):
    folder: str = None
    volume_attach: List[str] = []


class Cfg(BaseModel):
    container: Container = Container()
    host_config: HostConfig = HostConfig()
    code: Code = Code()


class MountVolume(BaseModel):
    target: str = None
    source: str = None
    read_only: bool = None
    type: str = 'volume'
